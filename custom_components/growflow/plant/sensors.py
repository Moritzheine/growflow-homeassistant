"""Sensor entities for Plant."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..const import (
    DOMAIN,
    MANUFACTURER,
    UNIT_DAYS,
    UNIT_EC,
    UNIT_PH,
    PLANT_DEVICE_CLASS_MOISTURE,
)
from .coordinator import PlantCoordinator

_LOGGER = logging.getLogger(__name__)


class PlantSensorBase(CoordinatorEntity, SensorEntity):
    """Base class for Plant sensors."""

    def __init__(self, coordinator: PlantCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"plant_{coordinator.plant_name}")},
            "name": f"{coordinator.plant_name} ({coordinator.plant_strain})",
            "manufacturer": MANUFACTURER,
            "model": "Plant",
            "via_device": (DOMAIN, coordinator.growbox_name),
        }


class PlantSoilMoistureSensor(PlantSensorBase):
    """Soil moisture sensor for plant."""

    def __init__(self, coordinator: PlantCoordinator) -> None:
        """Initialize soil moisture sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"plant_{coordinator.plant_name}_soil_moisture"
        self._attr_name = f"{coordinator.plant_name} Soil Moisture"
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_device_class = SensorDeviceClass.HUMIDITY  # Closest match
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:water-percent"

    @property
    def native_value(self) -> float | None:
        """Return soil moisture value."""
        return self.coordinator.data.get("soil_moisture")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        return {
            "growbox": self.coordinator.data.get("growbox_name"),
            "days_since_watering": self.coordinator.data.get("days_since_watering"),
        }


class PlantECSensor(PlantSensorBase):
    """EC sensor for plant."""

    def __init__(self, coordinator: PlantCoordinator) -> None:
        """Initialize EC sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"plant_{coordinator.plant_name}_ec"
        self._attr_name = f"{coordinator.plant_name} EC"
        self._attr_native_unit_of_measurement = UNIT_EC
        self._attr_device_class = SensorDeviceClass.VOLTAGE  # Closest match
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:lightning-bolt"

    @property
    def native_value(self) -> float | None:
        """Return EC value."""
        return self.coordinator.data.get("ec_value")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        ec = self.coordinator.data.get("ec_value", 0)
        status = "Low" if ec < 1.0 else "High" if ec > 2.5 else "Good"
        return {
            "status": status,
            "growbox": self.coordinator.data.get("growbox_name"),
        }


class PlantPHSensor(PlantSensorBase):
    """pH sensor for plant."""

    def __init__(self, coordinator: PlantCoordinator) -> None:
        """Initialize pH sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"plant_{coordinator.plant_name}_ph"
        self._attr_name = f"{coordinator.plant_name} pH"
        self._attr_native_unit_of_measurement = UNIT_PH
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:ph"

    @property
    def native_value(self) -> float | None:
        """Return pH value."""
        return self.coordinator.data.get("ph_value")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        ph = self.coordinator.data.get("ph_value", 7.0)
        status = "Low" if ph < 5.5 else "High" if ph > 7.0 else "Good"
        return {
            "status": status,
            "growbox": self.coordinator.data.get("growbox_name"),
        }


class PlantDaysSincePlantedSensor(PlantSensorBase):
    """Days since planted sensor for plant."""

    def __init__(self, coordinator: PlantCoordinator) -> None:
        """Initialize days since planted sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"plant_{coordinator.plant_name}_days_since_planted"
        self._attr_name = f"{coordinator.plant_name} Days Since Planted"
        self._attr_native_unit_of_measurement = UNIT_DAYS
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_icon = "mdi:calendar-clock"

    @property
    def native_value(self) -> int | None:
        """Return days since planted."""
        return self.coordinator.data.get("days_since_planted")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        return {
            "planted_date": self.coordinator.data.get("planted_date"),
            "growth_stage": self.coordinator.data.get("growth_stage"),
            "strain": self.coordinator.data.get("plant_strain"),
        }


class PlantDaysSinceWateringSensor(PlantSensorBase):
    """Days since watering sensor for plant."""

    def __init__(self, coordinator: PlantCoordinator) -> None:
        """Initialize days since watering sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"plant_{coordinator.plant_name}_days_since_watering"
        self._attr_name = f"{coordinator.plant_name} Days Since Watering"
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
        status = "Critical" if days and days > 7 else "Warning" if days and days > 4 else "Good"
        return {
            "status": status,
            "soil_moisture": self.coordinator.data.get("soil_moisture"),
        }


class PlantGrowthStageSensor(PlantSensorBase):
    """Growth stage sensor for plant."""

    def __init__(self, coordinator: PlantCoordinator) -> None:
        """Initialize growth stage sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"plant_{coordinator.plant_name}_growth_stage"
        self._attr_name = f"{coordinator.plant_name} Growth Stage"
        self._attr_icon = "mdi:sprout"

    @property
    def native_value(self) -> str | None:
        """Return growth stage."""
        return self.coordinator.data.get("growth_stage")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        return {
            "days_since_planted": self.coordinator.data.get("days_since_planted"),
            "strain": self.coordinator.data.get("plant_strain"),
            "growbox": self.coordinator.data.get("growbox_name"),
        }