"""Button entities for Plant watering."""
from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..const import DOMAIN, MANUFACTURER
from .coordinator import PlantCoordinator

_LOGGER = logging.getLogger(__name__)


class PlantButtonBase(CoordinatorEntity, ButtonEntity):
    """Base class for Plant button entities."""

    def __init__(self, coordinator: PlantCoordinator) -> None:
        """Initialize the button entity."""
        super().__init__(coordinator)
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"plant_{coordinator.plant_id}")},
            "name": f"{coordinator.plant_name} ({coordinator.plant_strain})",
            "manufacturer": MANUFACTURER,
            "model": "Plant",
            "via_device": (DOMAIN, coordinator.growbox_name),
        }


class PlantWaterQuickButton(PlantButtonBase):
    """Quick water button with default volume."""

    def __init__(self, coordinator: PlantCoordinator) -> None:
        """Initialize quick water button."""
        super().__init__(coordinator)
        self._attr_unique_id = f"plant_{coordinator.plant_id}_water_quick"
        self._attr_name = f"{coordinator.plant_name} Gießen"
        self._attr_icon = "mdi:watering-can"

    async def async_press(self) -> None:
        """Handle button press - water with default volume."""
        await self.coordinator.async_water_plant_quick()
        _LOGGER.info("Quick watered %s with %s ml", 
                    self.coordinator.plant_name, 
                    self.coordinator.default_water_volume)