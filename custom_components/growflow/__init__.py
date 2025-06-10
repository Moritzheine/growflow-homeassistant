"""The GrowFlow integration."""
import logging
from datetime import datetime

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Platforms die wir unterstützen
PLATFORMS = ["sensor", "select"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up GrowFlow from a config entry."""
    
    _LOGGER.info("Setting up GrowFlow entry: %s", entry.data["name"])
    
    # Stelle sicher dass planted_date ein datetime object ist
    planted_date_str = entry.data["planted_date"]
    if isinstance(planted_date_str, str):
        try:
            planted_date = datetime.fromisoformat(planted_date_str)
        except ValueError:
            # Fallback für verschiedene Datumsformate
            try:
                planted_date = datetime.strptime(planted_date_str, "%Y-%m-%d")
            except ValueError:
                _LOGGER.error("Invalid planted_date format: %s", planted_date_str)
                planted_date = datetime.now()
    else:
        planted_date = planted_date_str
    
    # Stelle sicher dass phase_start_date auch korrekt ist
    phase_start_str = entry.options.get("phase_start_date")
    if phase_start_str:
        try:
            phase_start_date = datetime.fromisoformat(phase_start_str)
        except ValueError:
            try:
                phase_start_date = datetime.strptime(phase_start_str, "%Y-%m-%d")
            except ValueError:
                phase_start_date = planted_date
    else:
        phase_start_date = planted_date
    
    # Erstelle grow data dictionary
    grow_data = {
        "name": entry.data["name"],
        "grow_type": entry.data["grow_type"], 
        "planted_date": planted_date,
        "current_phase": entry.options.get("current_phase", "germination"),
        "phase_start_date": phase_start_date,
        "notes": entry.options.get("notes", ""),
        "watering_history": entry.options.get("watering_history", []),
        "nutrients_history": entry.options.get("nutrients_history", [])
    }
    
    # Speichere data in hass.data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = grow_data
    
    # Erstelle Device Registry Entry
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        manufacturer="GrowFlow",
        name=entry.data["name"],
        model=f"Cannabis Grow - {entry.data['grow_type'].title()}",
        sw_version="0.1.0",
        suggested_area="Grow Room"
    )
    
    # Setup Platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Registriere Update Listener für Options Flow - OHNE reload!
    entry.async_on_unload(entry.add_update_listener(async_update_options))
    
    _LOGGER.info("GrowFlow setup completed for %s", entry.data["name"])
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading GrowFlow entry: %s", entry.data["name"])
    
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    # Remove from hass.data
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok

async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options - NO RELOAD to prevent infinite loop."""
    _LOGGER.info("Updating options for GrowFlow entry: %s", entry.data["name"])
    
    # Update grow_data in hass.data
    if entry.entry_id in hass.data[DOMAIN]:
        grow_data = hass.data[DOMAIN][entry.entry_id]
        grow_data["current_phase"] = entry.options.get("current_phase", "germination")
        grow_data["notes"] = entry.options.get("notes", "")
        
        # Update phase_start_date wenn vorhanden
        phase_start_str = entry.options.get("phase_start_date")
        if phase_start_str:
            try:
                grow_data["phase_start_date"] = datetime.fromisoformat(phase_start_str)
            except ValueError:
                try:
                    grow_data["phase_start_date"] = datetime.strptime(phase_start_str, "%Y-%m-%d")
                except ValueError:
                    pass  # Keep old value
        
        # Trigger state update für alle entities
        hass.async_create_task(async_update_entities(hass, entry.entry_id))

async def async_update_entities(hass: HomeAssistant, entry_id: str) -> None:
    """Update all entities for this config entry."""
    # Trigger update für alle Entities dieser Integration
    from homeassistant.helpers import entity_registry as er
    
    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(entity_registry, entry_id)
    
    for entity_entry in entities:
        if entity_entry.entity_id:
            entity = hass.states.get(entity_entry.entity_id)
            if entity:
                # Schedule state update
                hass.async_create_task(
                    hass.states.async_set(entity_entry.entity_id, entity.state, entity.attributes)
                )

async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove a config entry."""
    _LOGGER.info("Removing GrowFlow entry: %s", entry.data["name"])