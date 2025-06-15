"""Number entities for Plant watering."""
from __future__ import annotations

import logging

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..const import DOMAIN, MANUFACTURER, UNIT_ML
from .coordinator import PlantCoordinator

_LOGGER = logging.getLogger(__name__)


class PlantNumberBase(CoordinatorEntity, NumberEntity):
    """Base class for Plant number entities."""

    def __init__(self, coordinator: PlantCoordinator) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"plant_{coordinator.plant_id}")},
            "name": f"{coordinator.plant_name} ({coordinator.plant_strain})",
            "manufacturer": MANUFACTURER,
            "model": "Plant",
            "via_device": (DOMAIN, coordinator.growbox_name),
        }


class PlantDefaultWaterVolumeNumber(PlantNumberBase):
    """Default water volume number entity."""

    def __init__(self, coordinator: PlantCoordinator) -> None:
        """Initialize default water volume number."""
        super().__init__(coordinator)
        self._attr_unique_id = f"plant_{coordinator.plant_id}_default_water_volume"
        self._attr_name = f"{coordinator.plant_name} Standard Wassermenge"
        self._attr_icon = "mdi:cup-water"
        self._attr_native_unit_of_measurement = UNIT_ML
        self._attr_mode = NumberMode.BOX
        self._attr_native_min_value = 100
        self._attr_native_max_value = 5000
        self._attr_native_step = 50
        
        # ✅ Explicitly ensure this is a Number Entity
        self._attr_should_poll = False

    @property
    def native_value(self) -> float:
        """Return the current default water volume."""
        return float(self.coordinator.default_water_volume)

    async def async_set_native_value(self, value: float) -> None:
        """Set new default water volume."""
        volume_ml = int(value)
        await self.coordinator.async_update_default_water_volume(volume_ml)
        _LOGGER.info("Updated default water volume for %s: %s ml", 
                    self.coordinator.plant_name, volume_ml)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success