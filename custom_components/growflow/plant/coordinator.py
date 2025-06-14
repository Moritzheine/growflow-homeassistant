"""Data coordinator for Plant."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from ..const import (
    DOMAIN,
    SCAN_INTERVAL,
    CONF_PLANT_NAME,
    CONF_PLANT_STRAIN,
    CONF_PLANT_GROWBOX,
    CONF_PLANTED_DATE,
    CONF_GROWTH_STAGE,
    CONF_SOIL_MOISTURE_ENTITY,
    CONF_EC_ENTITY,
    CONF_PH_ENTITY,
    GROWTH_STAGE_SEEDLING,
)

_LOGGER = logging.getLogger(__name__)


class PlantCoordinator(DataUpdateCoordinator):
    """Coordinator to manage Plant data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.hass = hass
        self.entry = entry
        self.plant_name = entry.data[CONF_PLANT_NAME]
        self.plant_strain = entry.data.get(CONF_PLANT_STRAIN, "Unknown")
        self.growbox_name = entry.data[CONF_PLANT_GROWBOX]
        self.planted_date = dt_util.parse_date(entry.data[CONF_PLANTED_DATE])
        self.growth_stage = entry.options.get(
            CONF_GROWTH_STAGE, 
            entry.data.get(CONF_GROWTH_STAGE, GROWTH_STAGE_SEEDLING)
        )
        self.soil_moisture_entity = entry.data.get(CONF_SOIL_MOISTURE_ENTITY)
        self.ec_entity = entry.data.get(CONF_EC_ENTITY)
        self.ph_entity = entry.data.get(CONF_PH_ENTITY)
        
        # Plant history (in memory for now)
        self.plant_history: list[dict] = []
        
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_plant_{self.plant_name}",
            update_interval=timedelta(seconds=SCAN_INTERVAL),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data from sensors."""
        try:
            # Soil moisture from sensor or mock
            if self.soil_moisture_entity:
                moisture_state = self.hass.states.get(self.soil_moisture_entity)
                soil_moisture = float(moisture_state.state) if moisture_state and moisture_state.state != "unavailable" else 45.0
            else:
                soil_moisture = 45.0  # Mock value
            
            # EC value from sensor or mock
            if self.ec_entity:
                ec_state = self.hass.states.get(self.ec_entity)
                ec_value = float(ec_state.state) if ec_state and ec_state.state != "unavailable" else 1.8
            else:
                ec_value = 1.8  # Mock value
            
            # pH value from sensor or mock
            if self.ph_entity:
                ph_state = self.hass.states.get(self.ph_entity)
                ph_value = float(ph_state.state) if ph_state and ph_state.state != "unavailable" else 6.2
            else:
                ph_value = 6.2  # Mock value
            
            # Calculate days since planted
            today = dt_util.now().date()
            days_since_planted = (today - self.planted_date).days
            
            # Last watering (from history)
            last_watering = self._get_last_activity("water")
            days_since_watering = (today - last_watering.date()).days if last_watering else None
            
            data = {
                "plant_name": self.plant_name,
                "plant_strain": self.plant_strain,
                "growbox_name": self.growbox_name,
                "planted_date": self.planted_date,
                "growth_stage": self.growth_stage,
                "days_since_planted": days_since_planted,
                "days_since_watering": days_since_watering,
                "soil_moisture": soil_moisture,
                "ec_value": ec_value,
                "ph_value": ph_value,
            }
            
            _LOGGER.debug("Updated plant data for %s: %s", self.plant_name, data)
            return data
            
        except Exception as err:
            raise UpdateFailed(f"Error updating plant data: {err}") from err

    def _get_last_activity(self, activity_type: str) -> datetime | None:
        """Get last activity of specific type from history."""
        for entry in reversed(self.plant_history):
            if entry.get("type") == activity_type:
                return entry.get("timestamp")
        return None

    async def async_add_water_entry(self, volume: float, ec: float | None = None, ph: float | None = None, notes: str | None = None) -> None:
        """Add watering entry to plant history."""
        entry = {
            "type": "water",
            "timestamp": dt_util.now(),
            "volume_ml": volume,
            "ec": ec,
            "ph": ph,
            "notes": notes,
        }
        self.plant_history.append(entry)
        await self.async_request_refresh()
        _LOGGER.info("Added watering entry for %s: %s ml", self.plant_name, volume)

    async def async_add_fertilizer_entry(self, fertilizer: str, ec: float | None = None, ph: float | None = None, notes: str | None = None) -> None:
        """Add fertilizer entry to plant history."""
        entry = {
            "type": "fertilizer",
            "timestamp": dt_util.now(),
            "fertilizer": fertilizer,
            "ec": ec,
            "ph": ph,
            "notes": notes,
        }
        self.plant_history.append(entry)
        await self.async_request_refresh()
        _LOGGER.info("Added fertilizer entry for %s: %s", self.plant_name, fertilizer)

    async def async_change_growth_stage(self, new_stage: str, notes: str | None = None) -> None:
        """Change growth stage."""
        old_stage = self.growth_stage
        self.growth_stage = new_stage
        
        # Save to options
        new_options = dict(self.entry.options)
        new_options[CONF_GROWTH_STAGE] = new_stage
        self.hass.config_entries.async_update_entry(self.entry, options=new_options)
        
        # Add to history
        entry = {
            "type": "phase_change",
            "timestamp": dt_util.now(),
            "old_stage": old_stage,
            "new_stage": new_stage,
            "notes": notes,
        }
        self.plant_history.append(entry)
        await self.async_request_refresh()
        _LOGGER.info("Changed growth stage for %s: %s -> %s", self.plant_name, old_stage, new_stage)

    def update_config(self, config_data: dict[str, Any]) -> None:
        """Update configuration from options flow."""
        self.soil_moisture_entity = config_data.get(CONF_SOIL_MOISTURE_ENTITY)
        self.ec_entity = config_data.get(CONF_EC_ENTITY)
        self.ph_entity = config_data.get(CONF_PH_ENTITY)
        self.growth_stage = config_data.get(CONF_GROWTH_STAGE, self.growth_stage)