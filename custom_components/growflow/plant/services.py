"""Services for Plant management with history-based tracking."""
from __future__ import annotations

import logging
import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.util import dt as dt_util

from ..const import (
    DOMAIN,
    SERVICE_CHANGE_PHASE,
    SERVICE_ADD_NOTE,
    SERVICE_WATER_PLANT,
    SERVICE_WATER_PLANT_QUICK,
    GROWTH_STAGES,
    GROWTH_STAGE_LABELS,
)
from .coordinator import PlantCoordinator

_LOGGER = logging.getLogger(__name__)

# Service schemas
CHANGE_PHASE_SCHEMA = vol.Schema({
    vol.Required("entity_id"): cv.entity_id,
    vol.Required("new_stage"): vol.In(GROWTH_STAGES),
    vol.Optional("notes"): cv.string,
})

ADD_NOTE_SCHEMA = vol.Schema({
    vol.Required("entity_id"): cv.entity_id,
    vol.Required("note"): cv.string,
})

# ✅ NEW: Watering service schemas
WATER_PLANT_SCHEMA = vol.Schema({
    vol.Required("entity_id"): cv.entity_id,
    vol.Required("volume_ml"): vol.All(vol.Coerce(int), vol.Range(min=1, max=10000)),
    vol.Optional("notes"): cv.string,
})

WATER_PLANT_QUICK_SCHEMA = vol.Schema({
    vol.Required("entity_id"): cv.entity_id,
})


def async_setup_services(hass: HomeAssistant) -> None:
    """Set up the plant services for history-based tracking."""

    async def change_phase(call: ServiceCall) -> None:
        """Handle change phase service call."""
        entity_id = call.data["entity_id"]
        new_stage = call.data["new_stage"]
        notes = call.data.get("notes")
        
        coordinator = _get_plant_coordinator_by_entity(hass, entity_id)
        if coordinator:
            # Update the coordinator
            await coordinator.async_change_growth_stage(new_stage, notes)
            
            # Also update the select entity to maintain consistency
            select_entity_id = coordinator.select_entity_id
            select_entity = hass.states.get(select_entity_id)
            
            if select_entity:
                # Get the label for the new stage
                new_stage_label = GROWTH_STAGE_LABELS.get(new_stage, new_stage)
                
                # Call the select entity's service to update it
                await hass.services.async_call(
                    "select",
                    "select_option",
                    {
                        "entity_id": select_entity_id,
                        "option": new_stage_label,
                    },
                    blocking=True,
                )
            
            stage_label = GROWTH_STAGE_LABELS.get(new_stage, new_stage)
            _LOGGER.info("Changed phase for plant %s: %s (via service)", coordinator.plant_name, stage_label)
        else:
            _LOGGER.error("Plant coordinator not found for entity %s", entity_id)

    # ✅ NEW: Watering service handlers
    async def water_plant(call: ServiceCall) -> None:
        """Handle water plant service call."""
        entity_id = call.data["entity_id"]
        volume_ml = call.data["volume_ml"]
        notes = call.data.get("notes")
        
        coordinator = _get_plant_coordinator_by_entity(hass, entity_id)
        if coordinator:
            await coordinator.async_add_watering_entry(volume_ml, notes)
            _LOGGER.info("Watered plant %s: %s ml", coordinator.plant_name, volume_ml)
        else:
            _LOGGER.error("Plant coordinator not found for entity %s", entity_id)

    async def water_plant_quick(call: ServiceCall) -> None:
        """Handle quick water plant service call."""
        entity_id = call.data["entity_id"]
        
        coordinator = _get_plant_coordinator_by_entity(hass, entity_id)
        if coordinator:
            await coordinator.async_water_plant_quick()
            _LOGGER.info("Quick watered plant %s: %s ml", 
                        coordinator.plant_name, coordinator.default_water_volume)
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
        DOMAIN, SERVICE_CHANGE_PHASE, change_phase, schema=CHANGE_PHASE_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_ADD_NOTE, add_note, schema=ADD_NOTE_SCHEMA
    )
    # ✅ NEW: Watering services
    hass.services.async_register(
        DOMAIN, SERVICE_WATER_PLANT, water_plant, schema=WATER_PLANT_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_WATER_PLANT_QUICK, water_plant_quick, schema=WATER_PLANT_QUICK_SCHEMA
    )

    _LOGGER.info("Plant services registered (including watering system)")


def _get_plant_coordinator_by_entity(hass: HomeAssistant, entity_id: str) -> PlantCoordinator | None:
    """Get plant coordinator by entity ID (optimized for history-based system)."""
    # Extract plant identifier from entity_id 
    if not ("sensor." in entity_id or "date." in entity_id or "text." in entity_id or "select." in entity_id):
        return None
    
    # Remove domain prefix (sensor., date., etc.)
    entity_name = entity_id.split(".", 1)[1]
    
    # Try to find matching coordinator
    for entry_id, coordinator in hass.data.get(DOMAIN, {}).items():
        if isinstance(coordinator, PlantCoordinator):
            # Check if entity belongs to this plant using the plant_id
            if entity_name.startswith(coordinator.plant_id):
                return coordinator
    
    return None


def async_unload_services(hass: HomeAssistant) -> None:
    """Unload the plant services."""
    hass.services.async_remove(DOMAIN, SERVICE_CHANGE_PHASE)
    hass.services.async_remove(DOMAIN, SERVICE_ADD_NOTE)
    # ✅ NEW: Remove watering services
    hass.services.async_remove(DOMAIN, SERVICE_WATER_PLANT)
    hass.services.async_remove(DOMAIN, SERVICE_WATER_PLANT_QUICK)
    _LOGGER.info("Plant services unloaded")