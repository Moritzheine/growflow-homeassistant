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
    elif isinstance(coordinator, PlantCoordinator):
        # Plants haben erstmal keine Number-Entitäten
        pass
    else:
        _LOGGER.error("Unknown coordinator type: %s", type(coordinator))