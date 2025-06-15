"""Select entities for Plant."""
from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..const import (
    DOMAIN, 
    MANUFACTURER, 
    GROWTH_STAGES, 
    GROWTH_STAGE_LABELS
)
from .coordinator import PlantCoordinator

_LOGGER = logging.getLogger(__name__)


class PlantSelectBase(CoordinatorEntity, SelectEntity):
    """Base class for Plant select entities."""

    def __init__(self, coordinator: PlantCoordinator) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"plant_{coordinator.plant_name}")},
            "name": f"{coordinator.plant_name} ({coordinator.plant_strain})",
            "manufacturer": MANUFACTURER,
            "model": "Plant",
            "via_device": (DOMAIN, coordinator.growbox_name),
        }


class PlantGrowthPhaseSelect(PlantSelectBase):
    """Growth phase select entity for plant."""

    def __init__(self, coordinator: PlantCoordinator) -> None:
        """Initialize growth phase select entity."""
        super().__init__(coordinator)
        plant_id = coordinator.plant_name.lower().replace(" ", "_")
        self._attr_unique_id = f"plant_{plant_id}_growth_phase"
        self._attr_name = f"{coordinator.plant_name} Wachstumsphase"
        self._attr_icon = "mdi:sprout-outline"
        self._attr_options = [GROWTH_STAGE_LABELS[stage] for stage in GROWTH_STAGES]

    @property
    def current_option(self) -> str | None:
        """Return the current growth phase label."""
        current_stage = self.coordinator.growth_stage
        return GROWTH_STAGE_LABELS.get(current_stage)

    async def async_select_option(self, option: str) -> None:
        """Select new growth phase."""
        # Find stage key by label
        stage_key = None
        for key, label in GROWTH_STAGE_LABELS.items():
            if label == option:
                stage_key = key
                break
        
        if stage_key:
            await self.coordinator.async_change_growth_stage(stage_key)
            _LOGGER.info("Changed growth phase for %s: %s", self.coordinator.plant_name, option)
        else:
            _LOGGER.error("Unknown growth phase option: %s", option)