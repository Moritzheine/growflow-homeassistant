"""Sensor entities for Growbox."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..const import DOMAIN, UNIT_KPA, MANUFACTURER, MODEL
from .coordinator import GrowboxCoordinator
from ..utils import get_vpd_status

_LOGGER = logging.getLogger(__name__)


class GrowboxSensorBase(CoordinatorEntity, SensorEntity):
    """Base class for Growbox sensors."""

    def __init__(self, coordinator: GrowboxCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.growbox_name)},
            "name": coordinator.growbox_name,
            "manufacturer": MANUFACTURER,
            "model": MODEL,
        }


class GrowboxTemperatureSensor(GrowboxSensorBase):
    """Temperature sensor for growbox."""

    def __init__(self, coordinator: GrowboxCoordinator) -> None:
        """Initialize temperature sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.growbox_name}_temperature"
        self._attr_name = f"{coordinator.growbox_name} Temperature"
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> float | None:
        """Return temperature value."""
        return self.coordinator.data.get("temperature")


class GrowboxHumiditySensor(GrowboxSensorBase):
    """Humidity sensor for growbox."""

    def __init__(self, coordinator: GrowboxCoordinator) -> None:
        """Initialize humidity sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.growbox_name}_humidity"
        self._attr_name = f"{coordinator.growbox_name} Humidity"
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_device_class = SensorDeviceClass.HUMIDITY
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> float | None:
        """Return humidity value."""
        return self.coordinator.data.get("humidity")


class GrowboxVPDSensor(GrowboxSensorBase):
    """VPD sensor for growbox."""

    def __init__(self, coordinator: GrowboxCoordinator) -> None:
        """Initialize VPD sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.growbox_name}_vpd"
        self._attr_name = f"{coordinator.growbox_name} VPD"
        self._attr_native_unit_of_measurement = UNIT_KPA
        self._attr_device_class = SensorDeviceClass.PRESSURE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:water-percent"

    @property
    def native_value(self) -> float | None:
        """Return VPD value."""
        return self.coordinator.data.get("vpd")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        vpd = self.coordinator.data.get("vpd")
        if vpd is not None:
            return {
                "status": get_vpd_status(vpd),
                "temperature": self.coordinator.data.get("temperature"),
                "humidity": self.coordinator.data.get("humidity"),
                "target_vpd": self.coordinator.data.get("target_vpd"),
                "target_humidity": self.coordinator.data.get("target_humidity"),
            }
        return {}


class GrowboxTargetHumiditySensor(GrowboxSensorBase):
    """Target humidity sensor for growbox."""

    def __init__(self, coordinator: GrowboxCoordinator) -> None:
        """Initialize target humidity sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.growbox_name}_target_humidity"
        self._attr_name = f"{coordinator.growbox_name} Target Humidity"
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_device_class = SensorDeviceClass.HUMIDITY
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:water-percent-alert"

    @property
    def native_value(self) -> float | None:
        """Return target humidity value."""
        return self.coordinator.data.get("target_humidity")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        return {
            "target_vpd": self.coordinator.data.get("target_vpd"),
            "current_humidity": self.coordinator.data.get("humidity"),
            "humidity_diff": (
                self.coordinator.data.get("target_humidity", 0) - 
                self.coordinator.data.get("humidity", 0)
            ),
        }