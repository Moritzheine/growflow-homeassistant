"""Data coordinator for Plant."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, date
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
    GROWTH_STAGE_EARLY_VEG,
    GROWTH_STAGES,
    VEG_PHASES,
    FLOWER_PHASES,
)

_LOGGER = logging.getLogger(__name__)


class PlantCoordinator(DataUpdateCoordinator):
    """Coordinator to manage Plant data using simple state history array."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.hass = hass
        self.entry = entry
        self.plant_name = entry.data[CONF_PLANT_NAME]
        self.plant_strain = entry.data.get(CONF_PLANT_STRAIN, "Unknown")
        self.growbox_name = entry.data[CONF_PLANT_GROWBOX]
        
        # Parse planted date properly
        planted_date_str = entry.data[CONF_PLANTED_DATE]
        if isinstance(planted_date_str, str):
            self.planted_date = dt_util.parse_date(planted_date_str)
        elif isinstance(planted_date_str, date):
            self.planted_date = planted_date_str
        else:
            self.planted_date = dt_util.now().date()
        
        self.growth_stage = entry.options.get(
            CONF_GROWTH_STAGE, 
            entry.data.get(CONF_GROWTH_STAGE, GROWTH_STAGE_EARLY_VEG)
        )
        
        # State history as simple array in config entry options
        self.state_history = entry.options.get("state_history", [])
        
        # Initialize if empty
        if not self.state_history:
            self.state_history = [{
                "date": self.planted_date.isoformat(),
                "stage": self.growth_stage
            }]
            self._save_state_history()
        
        # Generate consistent entity IDs
        self.plant_id = self.plant_name.lower().replace(" ", "_")
        self.select_entity_id = f"select.{self.plant_id}_growth_phase"
        
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_plant_{self.plant_id}",
            update_interval=timedelta(seconds=SCAN_INTERVAL),
        )

    def _save_state_history(self) -> None:
        """Save state history to config entry options."""
        new_options = dict(self.entry.options)
        new_options["state_history"] = self.state_history
        new_options[CONF_GROWTH_STAGE] = self.growth_stage
        self.hass.config_entries.async_update_entry(self.entry, options=new_options)

    def _calculate_days_in_phase(self, target_phase: str) -> int:
        """Calculate days in a specific phase from state history array."""
        total_days = 0
        current_phase_start = None
        
        for entry in self.state_history:
            entry_date = dt_util.parse_date(entry["date"])
            entry_stage = entry["stage"]
            
            if entry_stage == target_phase:
                # Phase starts
                if current_phase_start is None:
                    current_phase_start = entry_date
            else:
                # Phase ends
                if current_phase_start is not None:
                    total_days += (entry_date - current_phase_start).days
                    current_phase_start = None
        
        # If still in this phase, calculate until today
        if current_phase_start is not None:
            total_days += (dt_util.now().date() - current_phase_start).days
        
        return total_days

    def _calculate_days_in_current_phase(self) -> int:
        """Calculate days in current phase."""
        # Find the last entry with current stage
        for entry in reversed(self.state_history):
            if entry["stage"] == self.growth_stage:
                start_date = dt_util.parse_date(entry["date"])
                return (dt_util.now().date() - start_date).days
        
        # Fallback
        return 0

    def _calculate_total_veg_days(self) -> int:
        """Calculate total days in vegetative phases."""
        total = 0
        for phase in VEG_PHASES:
            total += self._calculate_days_in_phase(phase)
        return total

    def _calculate_total_flower_days(self) -> int:
        """Calculate total days in flowering phases."""
        total = 0
        for phase in FLOWER_PHASES:
            total += self._calculate_days_in_phase(phase)
        return total

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data using simple state history."""
        try:
            # Calculate days since planted
            today = dt_util.now().date()
            days_since_planted = (today - self.planted_date).days
            
            # Phase calculations from state history
            days_in_current_phase = self._calculate_days_in_current_phase()
            
            # Calculate days for each phase from state history
            phase_days = {}
            for phase in GROWTH_STAGES:
                phase_days[f"days_in_{phase}"] = self._calculate_days_in_phase(phase)
            
            # Calculate totals
            total_veg_days = self._calculate_total_veg_days()
            total_flower_days = self._calculate_total_flower_days()
            
            data = {
                "plant_name": self.plant_name,
                "plant_strain": self.plant_strain,
                "growbox_name": self.growbox_name,
                "planted_date": self.planted_date,
                "growth_stage": self.growth_stage,
                "days_since_planted": days_since_planted,
                "days_in_current_phase": days_in_current_phase,
                "total_veg_days": total_veg_days,
                "total_flower_days": total_flower_days,
                **phase_days,
            }
            
            _LOGGER.debug("Updated plant data using state history: %s", self.plant_name)
            return data
            
        except Exception as err:
            raise UpdateFailed(f"Error updating plant data: {err}") from err

    async def async_change_growth_stage(self, new_stage: str, notes: str | None = None) -> None:
        """Change growth stage and update state history."""
        if new_stage not in GROWTH_STAGES:
            _LOGGER.error("Invalid growth stage: %s", new_stage)
            return
        
        old_stage = self.growth_stage
        if old_stage == new_stage:
            return
        
        self.growth_stage = new_stage
        
        # Add to state history array
        self.state_history.append({
            "date": dt_util.now().date().isoformat(),
            "stage": new_stage
        })
        
        # Save to config entry
        self._save_state_history()
        
        await self.async_request_refresh()
        _LOGGER.info("Changed growth stage for %s: %s -> %s", self.plant_name, old_stage, new_stage)

    async def async_update_planted_date(self, new_date: date) -> None:
        """Update planted date and adjust state history."""
        old_date = self.planted_date
        self.planted_date = new_date
        
        # Update first entry in state history
        if self.state_history:
            self.state_history[0]["date"] = new_date.isoformat()
        
        # Update config entry
        new_data = dict(self.entry.data)
        new_data[CONF_PLANTED_DATE] = new_date.isoformat()
        self.hass.config_entries.async_update_entry(self.entry, data=new_data)
        
        # Save state history
        self._save_state_history()
        
        await self.async_request_refresh()
        _LOGGER.info("Updated planted date for %s: %s -> %s", self.plant_name, old_date, new_date)

    async def async_update_strain(self, new_strain: str) -> None:
        """Update plant strain."""
        old_strain = self.plant_strain
        self.plant_strain = new_strain
        
        # Update config entry
        new_data = dict(self.entry.data)
        new_data[CONF_PLANT_STRAIN] = new_strain
        self.hass.config_entries.async_update_entry(self.entry, data=new_data)
        
        await self.async_request_refresh()
        _LOGGER.info("Updated strain for %s: %s -> %s", self.plant_name, old_strain, new_strain)

    def get_state_history(self) -> list[dict]:
        """Get the complete state history."""
        return self.state_history.copy()

    def update_config(self, config_data: dict[str, Any]) -> None:
        """Update configuration from options flow."""
        if CONF_GROWTH_STAGE in config_data:
            self.growth_stage = config_data[CONF_GROWTH_STAGE]