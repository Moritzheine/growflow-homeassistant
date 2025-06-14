"""Services for Plant management."""
from __future__ import annotations

import logging
import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.util import dt as dt_util

from ..const import (
    DOMAIN,
    SERVICE_WATER_PLANT,
    SERVICE_FERTILIZE_PLANT,
    SERVICE_CHANGE_PHASE,
    SERVICE_ADD_NOTE,
    GROWTH_STAGES,
)
from .coordinator import PlantCoordinator

_LOGGER = logging.getLogger(__name__)

# Service schemas
WATER_PLANT_SCHEMA = vol.Schema({
    vol.Required("entity_id"): cv.entity_id,
    vol.Required("volume"): vol.Coerce(float),
    vol.Optional("ec"): vol.Coerce(float),
    vol.Optional("ph"): vol.Coerce(float),
    vol.Optional("notes"): cv.string,
})

FERTILIZE_PLANT_SCHEMA = vol.Schema({
    vol.Required("entity_id"): cv.entity_id,
    vol.Required("fertilizer"): cv.string,
    vol.Optional("ec"): vol.Coerce(float),
    vol.Optional("ph"): vol.Coerce(float),
    vol.Optional("notes"): cv.string,
})

CHANGE_PHASE_SCHEMA = vol.Schema({
    vol.Required("entity_id"): cv.entity_id,
    vol.Required("new_stage"): vol.In(GROWTH_STAGES),
    vol.Optional("notes"): cv.string,
})

ADD_NOTE_SCHEMA = vol.Schema({
    vol.Required("entity_id"): cv.entity_id,
    vol.Required("note"): cv.string,
})


def async_setup_services(hass: HomeAssistant) -> None:
    """Set up the plant services."""

    async def water_plant(call: ServiceCall) -> None:
        """Handle water plant service call."""
        entity_id = call.data["entity_id"]
        volume = call.data["volume"]
        ec = call.data.get("ec")
        ph = call.data.get("ph")
        notes = call.data.get("notes")
        
        # Find coordinator by entity_id
        coordinator = _get_plant_coordinator_by_entity(hass, entity_id)
        if coordinator:
            await coordinator.async_add_water_entry(volume, ec, ph, notes)
            _LOGGER.info("Watered plant %s: %s ml", coordinator.plant_name, volume)
        else:
            _LOGGER.error("Plant coordinator not found for entity %s", entity_id)

    async def fertilize_plant(call: ServiceCall) -> None:
        """Handle fertilize plant service call."""
        entity_id = call.data["entity_id"]
        fertilizer = call.data["fertilizer"]
        ec = call.data.get("ec")
        ph = call.data.get("ph")
        notes = call.data.get("notes")
        
        coordinator = _get_plant_coordinator_by_entity(hass, entity_id)
        if coordinator:
            await coordinator.async_add_fertilizer_entry(fertilizer, ec, ph, notes)
            _LOGGER.info("Fertilized plant %s: %s", coordinator.plant_name, fertilizer)
        else:
            _LOGGER.error("Plant coordinator not found for entity %s", entity_id)

    async def change_phase(call: ServiceCall) -> None:
        """Handle change phase service call."""
        entity_id = call.data["entity_id"]
        new_stage = call.data["new_stage"]
        notes = call.data.get("notes")
        
        coordinator = _get_plant_coordinator_by_entity(hass, entity_id)
        if coordinator:
            await coordinator.async_change_growth_stage(new_stage, notes)
            _LOGGER.info("Changed phase for plant %s: %s", coordinator.plant_name, new_stage)
        else:
            _LOGGER.error("Plant coordinator not found for entity %s", entity_id)

    async def add_note(call: ServiceCall) -> None:
        """Handle add note service call."""
        entity_id = call.data["entity_id"]
        note = call.data["note"]
        
        coordinator = _get_plant_coordinator_by_entity(hass, entity_id)
        if coordinator:
            # Add note as a special entry
            entry = {
                "type": "note",
                "timestamp": dt_util.now(),
                "note": note,
            }
            coordinator.plant_history.append(entry)
            await coordinator.async_request_refresh()
            _LOGGER.info("Added note to plant %s: %s", coordinator.plant_name, note)
        else:
            _LOGGER.error("Plant coordinator not found for entity %s", entity_id)

    # Register services
    hass.services.async_register(
        DOMAIN, SERVICE_WATER_PLANT, water_plant, schema=WATER_PLANT_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_FERTILIZE_PLANT, fertilize_plant, schema=FERTILIZE_PLANT_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_CHANGE_PHASE, change_phase, schema=CHANGE_PHASE_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_ADD_NOTE, add_note, schema=ADD_NOTE_SCHEMA
    )


def _get_plant_coordinator_by_entity(hass: HomeAssistant, entity_id: str) -> PlantCoordinator | None:
    """Get plant coordinator by entity ID."""
    # Extract plant name from entity_id (e.g., "sensor.my_plant_soil_moisture" -> "my_plant")
    if not entity_id.startswith("sensor.") or "_plant_" not in entity_id:
        return None
    
    # Simple approach: try to find matching coordinator
    for entry_id, coordinator in hass.data.get(DOMAIN, {}).items():
        if isinstance(coordinator, PlantCoordinator):
            # Check if entity belongs to this plant
            plant_id = f"plant_{coordinator.plant_name}"
            if plant_id in entity_id:
                return coordinator
    
    return None


def async_unload_services(hass: HomeAssistant) -> None:
    """Unload the plant services."""
    hass.services.async_remove(DOMAIN, SERVICE_WATER_PLANT)
    hass.services.async_remove(DOMAIN, SERVICE_FERTILIZE_PLANT)
    hass.services.async_remove(DOMAIN, SERVICE_CHANGE_PHASE)
    hass.services.async_remove(DOMAIN, SERVICE_ADD_NOTE)