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
    """Coordinator to manage Plant data."""

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
        
        # Plant history (in memory for now)
        self.plant_history: list[dict] = []
        
        # Phase tracking - initialize if not exists
        self.phase_history: dict[str, dict] = entry.options.get("phase_history", {})
        self._current_phase_start: date | None = None
        
        if not self.phase_history:
            # Initialize with current phase starting from planted date
            self._initialize_phase_tracking()
        else:
            # Load current phase start date
            current_phase_data = self.phase_history.get(self.growth_stage, {})
            if current_phase_data.get("start_date"):
                self._current_phase_start = dt_util.parse_date(current_phase_data["start_date"])
        
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_plant_{self.plant_name.replace(' ', '_')}",
            update_interval=timedelta(seconds=SCAN_INTERVAL),
        )

    def _initialize_phase_tracking(self) -> None:
        """Initialize phase tracking with current phase."""
        self.phase_history = {}
        
        # Start current phase from planted date
        self._current_phase_start = self.planted_date
        self.phase_history[self.growth_stage] = {
            "start_date": self.planted_date.isoformat(),
            "end_date": None,
            "total_days": 0
        }
        
        # Initialize all other phases as not started
        for phase in GROWTH_STAGES:
            if phase != self.growth_stage:
                self.phase_history[phase] = {
                    "start_date": None,
                    "end_date": None,
                    "total_days": 0
                }
        
        self._save_phase_history()

    def _save_phase_history(self) -> None:
        """Save phase history to config entry options."""
        new_options = dict(self.entry.options)
        new_options["phase_history"] = self.phase_history
        new_options[CONF_GROWTH_STAGE] = self.growth_stage
        self.hass.config_entries.async_update_entry(self.entry, options=new_options)

    def _calculate_days_in_phase(self, phase: str) -> int:
        """Calculate total days spent in a specific phase."""
        if phase not in self.phase_history:
            return 0
        
        phase_data = self.phase_history[phase]
        
        # If phase never started
        if not phase_data.get("start_date"):
            return 0
        
        start_date = dt_util.parse_date(phase_data["start_date"])
        
        # If phase is finished, return stored total
        if phase_data.get("end_date"):
            return phase_data.get("total_days", 0)
        
        # If this is the current phase, calculate from start to now
        if phase == self.growth_stage:
            return (dt_util.now().date() - start_date).days
        
        # Phase was started but not current and not finished - shouldn't happen
        return phase_data.get("total_days", 0)

    def _calculate_days_in_current_phase(self) -> int:
        """Calculate days in current phase."""
        if not self._current_phase_start:
            return 0
        return (dt_util.now().date() - self._current_phase_start).days

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
        """Update data from sensors."""
        try:
            # Calculate days since planted
            today = dt_util.now().date()
            days_since_planted = (today - self.planted_date).days
            
            # Phase calculations
            days_in_current_phase = self._calculate_days_in_current_phase()
            
            # Calculate days for each phase
            phase_days = {}
            for phase in GROWTH_STAGES:
                phase_days[f"days_in_{phase}"] = self._calculate_days_in_phase(phase)
            
            data = {
                "plant_name": self.plant_name,
                "plant_strain": self.plant_strain,
                "growbox_name": self.growbox_name,
                "planted_date": self.planted_date,
                "growth_stage": self.growth_stage,
                "days_since_planted": days_since_planted,
                "days_in_current_phase": days_in_current_phase,
                "total_veg_days": self._calculate_total_veg_days(),
                "total_flower_days": self._calculate_total_flower_days(),
                **phase_days,  # Add individual phase days
            }
            
            _LOGGER.debug("Updated plant data for %s: %s", self.plant_name, data)
            return data
            
        except Exception as err:
            raise UpdateFailed(f"Error updating plant data: {err}") from err

    async def async_change_growth_stage(self, new_stage: str, notes: str | None = None) -> None:
        """Change growth stage."""
        if new_stage not in GROWTH_STAGES:
            _LOGGER.error("Invalid growth stage: %s", new_stage)
            return
        
        old_stage = self.growth_stage
        if old_stage == new_stage:
            return
        
        today = dt_util.now().date()
        
        # End current phase
        if old_stage in self.phase_history and self._current_phase_start:
            total_days = (today - self._current_phase_start).days
            self.phase_history[old_stage].update({
                "end_date": today.isoformat(),
                "total_days": total_days
            })
        
        # Start new phase
        self.phase_history[new_stage] = {
            "start_date": today.isoformat(),
            "end_date": None,
            "total_days": 0
        }
        
        self.growth_stage = new_stage
        self._current_phase_start = today
        
        # Save to options
        self._save_phase_history()
        
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

    async def async_update_planted_date(self, new_date: date) -> None:
        """Update planted date."""
        old_date = self.planted_date
        self.planted_date = new_date
        
        # Recalculate phase history if planted date changes
        # This is complex - for now, just update the config and reset phase tracking
        if self.growth_stage in self.phase_history:
            # Update the start of the first phase to the new planted date
            self.phase_history[self.growth_stage]["start_date"] = new_date.isoformat()
            self._current_phase_start = new_date
        
        # Update config entry
        new_data = dict(self.entry.data)
        new_data[CONF_PLANTED_DATE] = new_date.isoformat()
        self.hass.config_entries.async_update_entry(self.entry, data=new_data)
        
        # Save phase history
        self._save_phase_history()
        
        # Add to history
        entry = {
            "type": "planted_date_change",
            "timestamp": dt_util.now(),
            "old_date": old_date,
            "new_date": new_date,
        }
        self.plant_history.append(entry)
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
        
        # Add to history
        entry = {
            "type": "strain_change",
            "timestamp": dt_util.now(),
            "old_strain": old_strain,
            "new_strain": new_strain,
        }
        self.plant_history.append(entry)
        await self.async_request_refresh()
        _LOGGER.info("Updated strain for %s: %s -> %s", self.plant_name, old_strain, new_strain)

    def update_config(self, config_data: dict[str, Any]) -> None:
        """Update configuration from options flow."""
        # No sensors to update anymore - just phase if provided
        if CONF_GROWTH_STAGE in config_data:
            self.growth_stage = config_data[CONF_GROWTH_STAGE]