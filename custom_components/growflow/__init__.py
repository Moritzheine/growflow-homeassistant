"""The GrowFlow integration."""
from __future__ import annotations

import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_GROWBOX_NAME, CONF_PLANT_NAME
from .growbox.coordinator import GrowboxCoordinator
from .plant.coordinator import PlantCoordinator
from .plant.services import async_setup_services, async_unload_services

_LOGGER = logging.getLogger(__name__)

# Platforms die wir unterstützen
PLATFORMS: list[Platform] = [
    Platform.SENSOR, 
    Platform.NUMBER, 
    Platform.DATE, 
    Platform.TEXT, 
    Platform.SELECT
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up GrowFlow from a config entry."""
    
    # Bestimme Geräte-Typ basierend auf Config-Daten
    if CONF_GROWBOX_NAME in entry.data:
        # Growbox Coordinator erstellen
        coordinator = GrowboxCoordinator(hass, entry)
        device_type = "growbox"
        # Growbox verwendet nur sensor und number platforms
        platforms = [Platform.SENSOR, Platform.NUMBER]
    elif CONF_PLANT_NAME in entry.data:
        # Plant Coordinator erstellen
        coordinator = PlantCoordinator(hass, entry)
        device_type = "plant"
        # Plant verwendet alle platforms
        platforms = PLATFORMS
    else:
        _LOGGER.error("Unknown device type in config entry: %s", entry.data)
        return False
    
    await coordinator.async_config_entry_first_refresh()
    
    # Coordinator in hass.data speichern
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    # Plant Services einmalig registrieren (beim ersten Plant)
    if device_type == "plant":
        if not any(
            isinstance(coord, PlantCoordinator) 
            for coord in hass.data[DOMAIN].values() 
            if coord != coordinator
        ):
            async_setup_services(hass)
    
    # Platforms laden
    await hass.config_entries.async_forward_entry_setups(entry, platforms)
    
    _LOGGER.info("GrowFlow %s setup completed for %s", device_type, entry.title)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    
    # Determine platforms to unload
    if CONF_GROWBOX_NAME in entry.data:
        platforms = [Platform.SENSOR, Platform.NUMBER]
    else:
        platforms = PLATFORMS
    
    # Platforms entladen
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, platforms):
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        
        # Plant Services entladen wenn das der letzte Plant war
        if isinstance(coordinator, PlantCoordinator):
            remaining_plants = any(
                isinstance(coord, PlantCoordinator) 
                for coord in hass.data[DOMAIN].values()
            )
            if not remaining_plants:
                async_unload_services(hass)
    
    return unload_ok