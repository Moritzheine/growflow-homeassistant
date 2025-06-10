"""GrowFlow select platform."""
import logging
from datetime import datetime
from typing import Optional

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo

from .const import (
    DOMAIN, 
    GROW_PHASES, 
    PHASE_NAMES,
    PHASE_ICONS,
    EVENT_PHASE_CHANGED
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up GrowFlow select entities."""
    
    grow_data = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = [
        PhaseSelectEntity(config_entry, grow_data),
    ]
    
    async_add_entities(entities)

class PhaseSelectEntity(SelectEntity):
    """Select entity für Phasen-Auswahl."""

    def __init__(self, config_entry: ConfigEntry, grow_data: dict):
        """Initialize the select entity."""
        self._config_entry = config_entry
        self._grow_data = grow_data
        self._attr_name = f"{grow_data['name']} Phase"
        self._attr_unique_id = f"{config_entry.entry_id}_phase_select"
        self._attr_options = [PHASE_NAMES[phase] for phase in GROW_PHASES]
        
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=grow_data["name"],
            manufacturer="GrowFlow",
            model=f"Cannabis Grow - {grow_data['grow_type'].title()}",
            sw_version="0.1.0"
        )

    @property
    def grow_data(self) -> dict:
        """Get current grow data."""
        return self.hass.data[DOMAIN][self._config_entry.entry_id]

    @property
    def current_option(self) -> Optional[str]:
        """Return the current option."""
        phase_key = self.grow_data["current_phase"]
        return PHASE_NAMES.get(phase_key, phase_key)

    @property
    def icon(self) -> str:
        """Return the icon."""
        phase_key = self.grow_data["current_phase"]
        return PHASE_ICONS.get(phase_key, "mdi:flower-outline")

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional attributes."""
        return {
            "phase_key": self.grow_data["current_phase"],
            "grow_type": self.grow_data["grow_type"],
            "notes": self.grow_data.get("notes", ""),
        }

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        # Finde phase_key für gewählte option
        phase_key = None
        for key, name in PHASE_NAMES.items():
            if name == option:
                phase_key = key
                break
        
        if not phase_key:
            _LOGGER.error("Invalid phase option: %s", option)
            return

        old_phase = self.grow_data["current_phase"]
        
        # Update hass.data
        self.hass.data[DOMAIN][self._config_entry.entry_id]["current_phase"] = phase_key
        self.hass.data[DOMAIN][self._config_entry.entry_id]["phase_start_date"] = datetime.now().isoformat()
        
        # Update config entry options
        new_options = dict(self._config_entry.options)
        new_options["current_phase"] = phase_key
        new_options["phase_start_date"] = datetime.now().isoformat()
        
        self.hass.config_entries.async_update_entry(
            self._config_entry, options=new_options
        )
        
        # Fire event
        self.hass.bus.async_fire(EVENT_PHASE_CHANGED, {
            "entity_id": self.entity_id,
            "device_id": self._config_entry.entry_id,
            "grow_name": self.grow_data["name"],
            "old_phase": old_phase,
            "new_phase": phase_key,
            "old_phase_name": PHASE_NAMES.get(old_phase, old_phase),
            "new_phase_name": PHASE_NAMES.get(phase_key, phase_key),
            "timestamp": datetime.now().isoformat(),
        })
        
        # Update state
        self.async_write_ha_state()
        
        _LOGGER.info(
            "Phase changed from %s to %s for %s", 
            PHASE_NAMES.get(old_phase, old_phase),
            option, 
            self.grow_data["name"]
        )