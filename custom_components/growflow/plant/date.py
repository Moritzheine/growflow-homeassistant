"""Date entities for Plant."""
from __future__ import annotations

import logging
from datetime import date

from homeassistant.components.date import DateEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from ..const import DOMAIN, MANUFACTURER
from .coordinator import PlantCoordinator

_LOGGER = logging.getLogger(__name__)


class PlantDateBase(CoordinatorEntity, DateEntity):
    """Base class for Plant date entities."""

    def __init__(self, coordinator: PlantCoordinator) -> None:
        """Initialize the date entity."""
        super().__init__(coordinator)
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"plant_{coordinator.plant_id}")},
            "name": f"{coordinator.plant_name} ({coordinator.plant_strain})",
            "manufacturer": MANUFACTURER,
            "model": "Plant",
            "via_device": (DOMAIN, coordinator.growbox_name),
        }


class PlantPlantedDateEntity(PlantDateBase):
    """Planted date entity for plant."""

    def __init__(self, coordinator: PlantCoordinator) -> None:
        """Initialize planted date entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"plant_{coordinator.plant_name}_planted_date"
        self._attr_name = f"{coordinator.plant_name} Einpflanzdatum"
        self._attr_icon = "mdi:calendar-plus"

    @property
    def native_value(self) -> date | None:
        """Return the planted date."""
        return self.coordinator.planted_date

    async def async_set_value(self, value: date) -> None:
        """Set new planted date."""
        await self.coordinator.async_update_planted_date(value)
        _LOGGER.info("Updated planted date for %s: %s", self.coordinator.plant_name, value)