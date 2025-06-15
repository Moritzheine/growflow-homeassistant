"""Text entities for Plant."""
from __future__ import annotations

import logging
import re

from homeassistant.components.text import TextEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..const import DOMAIN, MANUFACTURER
from .coordinator import PlantCoordinator

_LOGGER = logging.getLogger(__name__)


class PlantTextBase(CoordinatorEntity, TextEntity):
    """Base class for Plant text entities."""

    def __init__(self, coordinator: PlantCoordinator) -> None:
        """Initialize the text entity."""
        super().__init__(coordinator)
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"plant_{coordinator.plant_name}")},
            "name": f"{coordinator.plant_name} ({coordinator.plant_strain})",
            "manufacturer": MANUFACTURER,
            "model": "Plant",
            "via_device": (DOMAIN, coordinator.growbox_name),
        }


class PlantStrainEntity(PlantTextBase):
    """Strain text entity for plant."""

    def __init__(self, coordinator: PlantCoordinator) -> None:
        """Initialize strain text entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"plant_{coordinator.plant_name}_strain"
        self._attr_name = f"{coordinator.plant_name} Strain"
        self._attr_icon = "mdi:cannabis"
        self._attr_pattern = r"^[a-zA-Z0-9\s\-_]+$"
        self._attr_max = 50
        self._attr_min = 1

    @property
    def native_value(self) -> str | None:
        """Return the strain name."""
        return self.coordinator.plant_strain

    async def async_set_value(self, value: str) -> None:
        """Set new strain name."""
        await self.coordinator.async_update_strain(value)
        _LOGGER.info("Updated strain for %s: %s", self.coordinator.plant_name, value)