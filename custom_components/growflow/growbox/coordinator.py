"""Data coordinator for Growbox."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from ..const import (
    DOMAIN, 
    SCAN_INTERVAL, 
    CONF_GROWBOX_NAME,
    CONF_TEMPERATURE_ENTITY,
    CONF_HUMIDITY_ENTITY,
    CONF_HYGROSTAT_ENTITY,
    CONF_TARGET_VPD,
    DEFAULT_TARGET_VPD,
)
from ..utils import calculate_vpd, calculate_target_humidity

_LOGGER = logging.getLogger(__name__)


class GrowboxCoordinator(DataUpdateCoordinator):
    """Coordinator to manage Growbox data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.hass = hass
        self.entry = entry
        self.growbox_name = entry.data[CONF_GROWBOX_NAME]
        
        # Load entity config with proper priority (options override data)
        def get_entity_config(key):
            if key in entry.options:
                return entry.options[key]  # Could be None if cleared
            return entry.data.get(key)  # Fallback to original data
        
        self.temperature_entity = get_entity_config(CONF_TEMPERATURE_ENTITY)
        self.humidity_entity = get_entity_config(CONF_HUMIDITY_ENTITY)
        self.hygrostat_entity = get_entity_config(CONF_HYGROSTAT_ENTITY)
        self.target_vpd = entry.data.get(CONF_TARGET_VPD, DEFAULT_TARGET_VPD)
        
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{self.growbox_name}",
            update_interval=timedelta(seconds=SCAN_INTERVAL),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data from sensors."""
        try:
            if self.temperature_entity:
                temp_state = self.hass.states.get(self.temperature_entity)
                temperature = float(temp_state.state) if temp_state and temp_state.state != "unavailable" else 24.5
            else:
                temperature = 24.5
            
            if self.humidity_entity:
                humid_state = self.hass.states.get(self.humidity_entity)
                humidity = float(humid_state.state) if humid_state and humid_state.state != "unavailable" else 65.0
            else:
                humidity = 65.0
            
            vpd = calculate_vpd(temperature, humidity)
            target_humidity = calculate_target_humidity(temperature, self.target_vpd)
            
            data = {
                "temperature": temperature,
                "humidity": humidity,
                "vpd": vpd,
                "target_vpd": self.target_vpd,
                "target_humidity": target_humidity,
                "growbox_name": self.growbox_name,
            }
            
            _LOGGER.debug("Updated data for %s: %s", self.growbox_name, data)
            return data
            
        except Exception as err:
            raise UpdateFailed(f"Error updating data: {err}") from err

    async def async_set_target_vpd(self, target_vpd: float) -> None:
        """Set target VPD value."""
        self.target_vpd = target_vpd
        new_options = dict(self.entry.options)
        new_options[CONF_TARGET_VPD] = target_vpd
        self.hass.config_entries.async_update_entry(self.entry, options=new_options)
        await self.async_request_refresh()

    def update_config(self, config_data: dict[str, Any]) -> None:
        """Update configuration from options flow."""
        # Update coordinator attributes with new values (including None for cleared entities)
        if CONF_TEMPERATURE_ENTITY in config_data:
            self.temperature_entity = self._clean_entity_value(config_data[CONF_TEMPERATURE_ENTITY])
        if CONF_HUMIDITY_ENTITY in config_data:
            self.humidity_entity = self._clean_entity_value(config_data[CONF_HUMIDITY_ENTITY])
        if CONF_HYGROSTAT_ENTITY in config_data:
            self.hygrostat_entity = self._clean_entity_value(config_data[CONF_HYGROSTAT_ENTITY])
        
    def _clean_entity_value(self, value: Any) -> str | None:
        """Clean entity value, return None for empty/invalid values."""
        if value is None or value == "" or value == "None":
            return None
        if isinstance(value, str):
            stripped = value.strip()
            if stripped == "" or stripped.lower() == "none":
                return None
            return stripped
        return str(value) if value else None