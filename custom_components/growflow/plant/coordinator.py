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
    CONF_DEFAULT_WATER_VOLUME,
    DEFAULT_WATER_VOLUME,
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
        
        # ✅ NEW: Watering history system
        self.watering_history = entry.options.get("watering_history", [])
        self.default_water_volume = entry.options.get("default_water_volume", DEFAULT_WATER_VOLUME)
        
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
        new_options["watering_history"] = self.watering_history
        new_options["default_water_volume"] = self.default_water_volume
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

    # ✅ NEW: Watering calculation methods
    def _get_last_watering(self) -> datetime | None:
        """Get timestamp of last watering."""
        if not self.watering_history:
            return None
        
        last_entry = self.watering_history[-1]
        timestamp_str = last_entry["timestamp"]
        
        # ✅ Ensure we return a proper datetime object
        try:
            return dt_util.parse_datetime(timestamp_str)
        except (ValueError, TypeError) as e:
            _LOGGER.error("Failed to parse watering timestamp %s: %s", timestamp_str, e)
            return None

    def _calculate_days_since_watering(self) -> int | None:
        """Calculate days since last watering."""
        last_watering = self._get_last_watering()
        if not last_watering:
            return None
        
        # ✅ Ensure we have a proper datetime object
        try:
            return (dt_util.now() - last_watering).days
        except (TypeError, AttributeError) as e:
            _LOGGER.error("Failed to calculate days since watering: %s", e)
            return None

    def _calculate_water_this_week(self) -> int:
        """Calculate total water volume in last 7 days."""
        if not self.watering_history:
            return 0
        
        week_ago = dt_util.now() - timedelta(days=7)
        total = 0
        
        for entry in self.watering_history:
            try:
                entry_time = dt_util.parse_datetime(entry["timestamp"])
                if entry_time and entry_time >= week_ago:
                    total += entry.get("volume_ml", 0)
            except (ValueError, TypeError) as e:
                _LOGGER.debug("Skipping invalid timestamp in watering history: %s", e)
                continue
        
        return total

    def _calculate_avg_water_per_session(self) -> float:
        """Calculate average water volume per session (last 10 sessions)."""
        if not self.watering_history:
            return 0.0
        
        # Take last 10 sessions
        recent_sessions = self.watering_history[-10:]
        if not recent_sessions:
            return 0.0
        
        total_volume = sum(entry.get("volume_ml", 0) for entry in recent_sessions)
        return round(total_volume / len(recent_sessions), 1)

    def _calculate_watering_frequency(self) -> float:
        """Calculate average days between watering sessions."""
        if len(self.watering_history) < 2:
            return 0.0
        
        # Calculate differences between last 5 sessions
        recent_sessions = self.watering_history[-5:]
        if len(recent_sessions) < 2:
            return 0.0
        
        total_days = 0
        count = 0
        
        for i in range(1, len(recent_sessions)):
            try:
                prev_time = dt_util.parse_datetime(recent_sessions[i-1]["timestamp"])
                curr_time = dt_util.parse_datetime(recent_sessions[i]["timestamp"])
                
                if prev_time and curr_time:
                    days_diff = (curr_time - prev_time).days
                    if days_diff > 0:  # Ignore same-day waterings
                        total_days += days_diff
                        count += 1
            except (ValueError, TypeError) as e:
                _LOGGER.debug("Skipping invalid timestamps in frequency calculation: %s", e)
                continue
        
        return round(total_days / count, 1) if count > 0 else 0.0

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
            
            # ✅ NEW: Watering calculations
            last_watering = self._get_last_watering()
            days_since_watering = self._calculate_days_since_watering()
            water_this_week = self._calculate_water_this_week()
            avg_water_per_session = self._calculate_avg_water_per_session()
            watering_frequency = self._calculate_watering_frequency()
            
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
                # ✅ NEW: Watering data
                "default_water_volume": self.default_water_volume,
                "last_watering": last_watering,
                "days_since_watering": days_since_watering,
                "water_this_week": water_this_week,
                "avg_water_per_session": avg_water_per_session,
                "watering_frequency": watering_frequency,
                "total_watering_sessions": len(self.watering_history),
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

    # ✅ NEW: Watering system methods
    async def async_add_watering_entry(self, volume_ml: int, notes: str | None = None) -> None:
        """Add watering entry to history."""
        entry = {
            "timestamp": dt_util.now().isoformat(),
            "volume_ml": volume_ml,
            "growth_stage": self.growth_stage,
            "notes": notes,
        }
        
        self.watering_history.append(entry)
        self._save_state_history()
        
        await self.async_request_refresh()
        _LOGGER.info("Added watering entry for %s: %s ml", self.plant_name, volume_ml)

    async def async_water_plant_quick(self) -> None:
        """Quick water with default volume."""
        await self.async_add_watering_entry(self.default_water_volume, "Quick watering")

    async def async_update_default_water_volume(self, volume_ml: int) -> None:
        """Update default water volume."""
        self.default_water_volume = volume_ml
        self._save_state_history()
        await self.async_request_refresh()
        _LOGGER.info("Updated default water volume for %s: %s ml", self.plant_name, volume_ml)

    def get_watering_history(self) -> list[dict]:
        """Get the complete watering history."""
        return self.watering_history.copy()

    def update_config(self, config_data: dict[str, Any]) -> None:
        """Update configuration from options flow."""
        if CONF_GROWTH_STAGE in config_data:
            self.growth_stage = config_data[CONF_GROWTH_STAGE]
        if CONF_DEFAULT_WATER_VOLUME in config_data:
            self.default_water_volume = config_data[CONF_DEFAULT_WATER_VOLUME]