"""Text platform for GrowFlow."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .plant.coordinator import PlantCoordinator
from .plant.text import PlantStrainEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up GrowFlow text entities."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    if isinstance(coordinator, PlantCoordinator):
        # Plant Text Entitäten
        entities = [
            PlantStrainEntity(coordinator),
        ]
        async_add_entities(entities)
    else:
        _LOGGER.debug("No text entities for coordinator type: %s", type(coordinator))