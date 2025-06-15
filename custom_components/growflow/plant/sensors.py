"""Sensor entities for Plant using history-based calculations."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..const import (
    DOMAIN,
    MANUFACTURER,
    UNIT_DAYS,
    UNIT_ML,
    GROWTH_STAGES,
    GROWTH_STAGE_LABELS,
)
from .coordinator import PlantCoordinator

_LOGGER = logging.getLogger(__name__)


class PlantSensorBase(CoordinatorEntity, SensorEntity):
    """Base class for Plant sensors."""

    def __init__(self, coordinator: PlantCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"plant_{coordinator.plant_id}")},
            "name": f"{coordinator.plant_name} ({coordinator.plant_strain})",
            "manufacturer": MANUFACTURER,
            "model": "Plant",
            "via_device": (DOMAIN, coordinator.growbox_name),
        }


class PlantHistoryDebugSensor(PlantSensorBase):
    """Debug sensor showing state history array."""

    def __init__(self, coordinator: PlantCoordinator) -> None:
        """Initialize state history debug sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"plant_{coordinator.plant_id}_state_history_debug"
        self._attr_name = f"{coordinator.plant_name} State History Debug"
        self._attr_icon = "mdi:format-list-bulleted"
        self._attr_entity_registry_enabled_default = False  # Disabled by default

    @property
    def native_value(self) -> str:
        """Return number of state history entries."""
        history = self.coordinator.get_state_history()
        return f"{len(history)} entries"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return state history and debug info."""
        history = self.coordinator.get_state_history()
        
        return {
            "plant_id": self.coordinator.plant_id,
            "current_stage": self.coordinator.growth_stage,
            "planted_date": str(self.coordinator.planted_date),
            "state_history": history,
            "total_entries": len(history),
            "tracking_method": "state_history_array",
            "storage_location": "config_entry_options",
            "first_entry": history[0] if history else None,
            "last_entry": history[-1] if history else None,
        }


class PlantDaysInCurrentPhaseSensor(PlantSensorBase):
    """Days in current phase sensor (calculated from history)."""

    def __init__(self, coordinator: PlantCoordinator) -> None:
        """Initialize days in current phase sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"plant_{coordinator.plant_id}_days_in_current_phase"
        self._attr_name = f"{coordinator.plant_name} Tage in aktueller Phase"
        self._attr_native_unit_of_measurement = UNIT_DAYS
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:calendar-clock"

    @property
    def native_value(self) -> int | None:
        """Return days in current phase from history calculations."""
        return self.coordinator.data.get("days_in_current_phase")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        current_stage = self.coordinator.growth_stage
        return {
            "current_phase": GROWTH_STAGE_LABELS.get(current_stage, current_stage),
            "current_phase_key": current_stage,
            "strain": self.coordinator.plant_strain,
            "calculation_method": "state_history_array",
            "select_entity": self.coordinator.select_entity_id,
        }


class PlantDaysSincePlantedSensor(PlantSensorBase):
    """Days since planted sensor."""

    def __init__(self, coordinator: PlantCoordinator) -> None:
        """Initialize days since planted sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"plant_{coordinator.plant_id}_days_since_planted"
        self._attr_name = f"{coordinator.plant_name} Gesamte Tage"
        self._attr_native_unit_of_measurement = UNIT_DAYS
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_icon = "mdi:calendar-range"

    @property
    def native_value(self) -> int | None:
        """Return days since planted."""
        return self.coordinator.data.get("days_since_planted")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        return {
            "planted_date": str(self.coordinator.planted_date),
            "growth_stage": self.coordinator.growth_stage,
            "strain": self.coordinator.plant_strain,
            "total_veg_days": self.coordinator.data.get("total_veg_days"),
            "total_flower_days": self.coordinator.data.get("total_flower_days"),
        }


# Individual Phase Sensors (History-based)
class PlantPhaseBaseSensor(PlantSensorBase):
    """Base class for individual phase sensors using history."""

    def __init__(self, coordinator: PlantCoordinator, phase: str) -> None:
        """Initialize phase sensor."""
        super().__init__(coordinator)
        self.phase = phase
        self.phase_label = GROWTH_STAGE_LABELS.get(phase, phase)
        self._attr_unique_id = f"plant_{coordinator.plant_id}_days_in_{phase}"
        self._attr_name = f"{coordinator.plant_name} Tage in {self.phase_label}"
        self._attr_native_unit_of_measurement = UNIT_DAYS
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_icon = self._get_phase_icon(phase)

    def _get_phase_icon(self, phase: str) -> str:
        """Get icon for phase."""
        icons = {
            "early_veg": "mdi:sprout",
            "mid_late_veg": "mdi:leaf-circle",  # ✅ New combined icon
            "early_flower": "mdi:flower",
            "mid_late_flower": "mdi:flower-tulip-outline",  # ✅ New combined icon
            "flushing": "mdi:water-sync",
            "done": "mdi:check-circle",
        }
        return icons.get(phase, "mdi:calendar")

    @property
    def native_value(self) -> int | None:
        """Return days in this phase from history calculations."""
        return self.coordinator.data.get(f"days_in_{self.phase}", 0)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        is_current = self.coordinator.growth_stage == self.phase
        return {
            "phase": self.phase_label,
            "phase_key": self.phase,
            "is_current_phase": is_current,
            "strain": self.coordinator.plant_strain,
            "calculation_method": "state_history_array",
        }


# ✅ NEW: Watering Sensors
class PlantLastWateringSensor(PlantSensorBase):
    """Last watering timestamp sensor."""

    def __init__(self, coordinator: PlantCoordinator) -> None:
        """Initialize last watering sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"plant_{coordinator.plant_id}_last_watering"
        self._attr_name = f"{coordinator.plant_name} Letztes Gießen"
        self._attr_icon = "mdi:water-clock"
        self._attr_device_class = "timestamp"

    @property
    def native_value(self) -> datetime | None:
        """Return last watering timestamp as datetime object."""
        last_watering = self.coordinator.data.get("last_watering")
        return last_watering  # ✅ Return datetime object directly, not ISO string

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        return {
            "total_sessions": self.coordinator.data.get("total_watering_sessions", 0),
            "strain": self.coordinator.plant_strain,
        }


class PlantDaysSinceWateringSensor(PlantSensorBase):
    """Days since watering sensor."""

    def __init__(self, coordinator: PlantCoordinator) -> None:
        """Initialize days since watering sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"plant_{coordinator.plant_id}_days_since_watering"
        self._attr_name = f"{coordinator.plant_name} Tage seit Gießen"
        self._attr_native_unit_of_measurement = UNIT_DAYS
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:water-alert"

    @property
    def native_value(self) -> int | None:
        """Return days since watering."""
        return self.coordinator.data.get("days_since_watering")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        days = self.coordinator.data.get("days_since_watering")
        if days is None:
            status = "Never watered"
        elif days > 5:
            status = "Overdue"
        elif days > 3:
            status = "Due soon"
        else:
            status = "Good"
            
        return {
            "status": status,
            "last_watering": str(self.coordinator.data.get("last_watering", "Never")),
            "strain": self.coordinator.plant_strain,
        }


class PlantWaterThisWeekSensor(PlantSensorBase):
    """Water volume this week sensor."""

    def __init__(self, coordinator: PlantCoordinator) -> None:
        """Initialize water this week sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"plant_{coordinator.plant_id}_water_this_week"
        self._attr_name = f"{coordinator.plant_name} Wasser diese Woche"
        self._attr_native_unit_of_measurement = UNIT_ML
        self._attr_state_class = SensorStateClass.TOTAL
        self._attr_icon = "mdi:water"

    @property
    def native_value(self) -> int | None:
        """Return water volume this week."""
        return self.coordinator.data.get("water_this_week", 0)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        return {
            "total_sessions": self.coordinator.data.get("total_watering_sessions", 0),
            "avg_per_session": self.coordinator.data.get("avg_water_per_session", 0),
            "strain": self.coordinator.plant_strain,
        }


class PlantAvgWaterPerSessionSensor(PlantSensorBase):
    """Average water per session sensor."""

    def __init__(self, coordinator: PlantCoordinator) -> None:
        """Initialize avg water per session sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"plant_{coordinator.plant_id}_avg_water_per_session"
        self._attr_name = f"{coordinator.plant_name} Ø Wasser pro Gießvorgang"
        self._attr_native_unit_of_measurement = UNIT_ML
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:cup-water"

    @property
    def native_value(self) -> float | None:
        """Return average water per session."""
        return self.coordinator.data.get("avg_water_per_session", 0)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        return {
            "total_sessions": self.coordinator.data.get("total_watering_sessions", 0),
            "calculation_basis": "last_10_sessions",
            "strain": self.coordinator.plant_strain,
        }


class PlantWateringFrequencySensor(PlantSensorBase):
    """Watering frequency sensor."""

    def __init__(self, coordinator: PlantCoordinator) -> None:
        """Initialize watering frequency sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"plant_{coordinator.plant_id}_watering_frequency"
        self._attr_name = f"{coordinator.plant_name} Gießfrequenz"
        self._attr_native_unit_of_measurement = UNIT_DAYS
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:calendar-sync"

    @property
    def native_value(self) -> float | None:
        """Return watering frequency in days."""
        return self.coordinator.data.get("watering_frequency", 0)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        freq = self.coordinator.data.get("watering_frequency", 0)
        if freq == 0:
            pattern = "Not enough data"
        elif freq < 1:
            pattern = "Multiple times daily"
        elif freq <= 2:
            pattern = "Every 1-2 days"
        elif freq <= 4:
            pattern = "Every 3-4 days"
        else:
            pattern = "Weekly or less"
            
        return {
            "pattern": pattern,
            "calculation_basis": "last_5_sessions",
            "strain": self.coordinator.plant_strain,
        }


class PlantWateringDebugSensor(PlantSensorBase):
    """Watering history debug sensor."""

    def __init__(self, coordinator: PlantCoordinator) -> None:
        """Initialize watering debug sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"plant_{coordinator.plant_id}_watering_debug"
        self._attr_name = f"{coordinator.plant_name} Watering Debug"
        self._attr_icon = "mdi:bug-check"
        self._attr_entity_registry_enabled_default = False  # Disabled by default

    @property
    def native_value(self) -> str:
        """Return number of watering entries."""
        history = self.coordinator.get_watering_history()
        return f"{len(history)} sessions"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return watering history and debug info."""
        history = self.coordinator.get_watering_history()
        
        return {
            "plant_id": self.coordinator.plant_id,
            "default_water_volume": self.coordinator.default_water_volume,
            "watering_history": history[-5:] if history else [],  # Last 5 entries
            "total_sessions": len(history),
            "tracking_method": "watering_history_array",
            "storage_location": "config_entry_options",
            "first_watering": history[0] if history else None,
            "last_watering": history[-1] if history else None,
        }


class PlantEarlyVegSensor(PlantPhaseBaseSensor):
    """Early veg days sensor."""
    def __init__(self, coordinator: PlantCoordinator) -> None:
        super().__init__(coordinator, "early_veg")


class PlantMidLateVegSensor(PlantPhaseBaseSensor):
    """Mid Late VEG days sensor (combined)."""
    def __init__(self, coordinator: PlantCoordinator) -> None:
        super().__init__(coordinator, "mid_late_veg")


class PlantEarlyFlowerSensor(PlantPhaseBaseSensor):
    """Early flower days sensor."""
    def __init__(self, coordinator: PlantCoordinator) -> None:
        super().__init__(coordinator, "early_flower")


class PlantMidLateFlowerSensor(PlantPhaseBaseSensor):
    """Mid Late Flower days sensor (combined)."""
    def __init__(self, coordinator: PlantCoordinator) -> None:
        super().__init__(coordinator, "mid_late_flower")


class PlantFlushingSensor(PlantPhaseBaseSensor):
    """Flushing days sensor."""
    def __init__(self, coordinator: PlantCoordinator) -> None:
        super().__init__(coordinator, "flushing")


# Summary Sensors (History-based)
class PlantTotalVegDaysSensor(PlantSensorBase):
    """Total vegetative days sensor from history."""

    def __init__(self, coordinator: PlantCoordinator) -> None:
        """Initialize total veg days sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"plant_{coordinator.plant_id}_total_veg_days"
        self._attr_name = f"{coordinator.plant_name} Vegetative Tage (Gesamt)"
        self._attr_native_unit_of_measurement = UNIT_DAYS
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_icon = "mdi:leaf-circle"

    @property
    def native_value(self) -> int | None:
        """Return total veg days from history calculations."""
        return self.coordinator.data.get("total_veg_days", 0)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        data = self.coordinator.data
        return {
            "early_veg_days": data.get("days_in_early_veg", 0),
            "mid_veg_days": data.get("days_in_mid_veg", 0),
            "late_veg_days": data.get("days_in_late_veg", 0),
            "strain": self.coordinator.plant_strain,
            "calculation_method": "history_based",
        }


class PlantTotalFlowerDaysSensor(PlantSensorBase):
    """Total flowering days sensor from history."""

    def __init__(self, coordinator: PlantCoordinator) -> None:
        """Initialize total flower days sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"plant_{coordinator.plant_id}_total_flower_days"
        self._attr_name = f"{coordinator.plant_name} Blüte Tage (Gesamt)"
        self._attr_native_unit_of_measurement = UNIT_DAYS
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_icon = "mdi:flower-circle"

    @property
    def native_value(self) -> int | None:
        """Return total flower days from history calculations."""
        return self.coordinator.data.get("total_flower_days", 0)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        data = self.coordinator.data
        return {
            "early_flower_days": data.get("days_in_early_flower", 0),
            "mid_flower_days": data.get("days_in_mid_flower", 0),
            "late_flower_days": data.get("days_in_late_flower", 0),
            "flushing_days": data.get("days_in_flushing", 0),
            "strain": self.coordinator.plant_strain,
            "calculation_method": "history_based",
        }