"""Sensor entities for Plant using history-based calculations."""
from __future__ import annotations

import logging
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
            "mid_veg": "mdi:leaf",
            "late_veg": "mdi:tree",
            "early_flower": "mdi:flower",
            "mid_flower": "mdi:flower-outline",
            "late_flower": "mdi:flower-tulip",
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


# Create sensors for each phase
class PlantEarlyVegSensor(PlantPhaseBaseSensor):
    """Early veg days sensor."""
    def __init__(self, coordinator: PlantCoordinator) -> None:
        super().__init__(coordinator, "early_veg")


class PlantMidVegSensor(PlantPhaseBaseSensor):
    """Mid veg days sensor."""
    def __init__(self, coordinator: PlantCoordinator) -> None:
        super().__init__(coordinator, "mid_veg")


class PlantLateVegSensor(PlantPhaseBaseSensor):
    """Late veg days sensor."""
    def __init__(self, coordinator: PlantCoordinator) -> None:
        super().__init__(coordinator, "late_veg")


class PlantEarlyFlowerSensor(PlantPhaseBaseSensor):
    """Early flower days sensor."""
    def __init__(self, coordinator: PlantCoordinator) -> None:
        super().__init__(coordinator, "early_flower")


class PlantMidFlowerSensor(PlantPhaseBaseSensor):
    """Mid flower days sensor."""
    def __init__(self, coordinator: PlantCoordinator) -> None:
        super().__init__(coordinator, "mid_flower")


class PlantLateFlowerSensor(PlantPhaseBaseSensor):
    """Late flower days sensor."""
    def __init__(self, coordinator: PlantCoordinator) -> None:
        super().__init__(coordinator, "late_flower")


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