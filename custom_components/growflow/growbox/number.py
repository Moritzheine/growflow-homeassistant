"""Number entities for Growbox."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..const import DOMAIN, UNIT_KPA, MANUFACTURER, MODEL, VPD_MIN, VPD_MAX
from .coordinator import GrowboxCoordinator

_LOGGER = logging.getLogger(__name__)


class GrowboxTargetVPDNumber(CoordinatorEntity, NumberEntity):
    """Target VPD number input for growbox."""

    def __init__(self, coordinator: GrowboxCoordinator) -> None:
        """Initialize the target VPD number."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.growbox_name}_target_vpd"
        self._attr_name = f"{coordinator.growbox_name} Target VPD"
        self._attr_native_unit_of_measurement = UNIT_KPA
        self._attr_native_min_value = VPD_MIN
        self._attr_native_max_value = VPD_MAX
        self._attr_native_step = 0.1
        self._attr_mode = NumberMode.BOX
        self._attr_icon = "mdi:target"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.growbox_name)},
            "name": coordinator.growbox_name,
            "manufacturer": MANUFACTURER,
            "model": MODEL,
        }

    @property
    def native_value(self) -> float:
        """Return the current target VPD value."""
        return self.coordinator.target_vpd

    async def async_set_native_value(self, value: float) -> None:
        """Set the target VPD value."""
        await self.coordinator.async_set_target_vpd(value)
        self.async_write_ha_state()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        return {
            "current_vpd": self.coordinator.data.get("vpd"),
            "calculated_target_humidity": self.coordinator.data.get("target_humidity"),
            "current_temperature": self.coordinator.data.get("temperature"),
        }