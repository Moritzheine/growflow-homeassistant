"""Number platform for GrowFlow."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CONF_GROWBOX_NAME
from .growbox.coordinator import GrowboxCoordinator
from .growbox.number import GrowboxTargetVPDNumber
from .plant.coordinator import PlantCoordinator
from .plant.number import PlantDefaultWaterVolumeNumber

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up GrowFlow number entities."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    if isinstance(coordinator, GrowboxCoordinator):
        # Growbox Number Entitäten
        numbers = [
            GrowboxTargetVPDNumber(coordinator),
        ]
        async_add_entities(numbers)
        _LOGGER.debug("Added Growbox number entities")
    elif isinstance(coordinator, PlantCoordinator):
        # Plant Number Entitäten
        numbers = [
            PlantDefaultWaterVolumeNumber(coordinator),
        ]
        async_add_entities(numbers)
        _LOGGER.debug("Added Plant number entities for %s", coordinator.plant_name)
    else:
        _LOGGER.error("Unknown coordinator type: %s", type(coordinator))