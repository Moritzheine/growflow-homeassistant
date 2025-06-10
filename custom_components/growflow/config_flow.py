"""Config flow for GrowFlow integration."""
import logging
from datetime import datetime
from typing import Any, Dict, Optional

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, GROW_TYPES, GROW_PHASES, GROW_TYPE_NAMES, PHASE_NAMES

_LOGGER = logging.getLogger(__name__)

class GrowFlowConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for GrowFlow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}
        
        if user_input is not None:
            # Validate unique name
            existing_entries = [
                entry.data["name"] for entry in self._async_current_entries()
            ]
            
            if user_input["name"] in existing_entries:
                errors["name"] = "name_exists"
            else:
                # Parse date string to datetime
                try:
                    planted_date = datetime.strptime(user_input["planted_date"], "%Y-%m-%d")
                except ValueError:
                    errors["planted_date"] = "invalid_date"
                else:
                    # Create entry
                    return self.async_create_entry(
                        title=user_input["name"],
                        data={
                            "name": user_input["name"],
                            "grow_type": user_input["grow_type"],
                            "planted_date": planted_date.isoformat(),
                        },
                        options={
                            "current_phase": "germination",
                            "phase_start_date": planted_date.isoformat(),
                            "notes": "",
                            "watering_history": [],
                            "nutrients_history": []
                        }
                    )

        # Schema für User Input
        data_schema = vol.Schema({
            vol.Required("name"): str,
            vol.Required("grow_type", default="soil"): vol.In(GROW_TYPES),
            vol.Required("planted_date", default=datetime.now().strftime("%Y-%m-%d")): str,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "grow_types": ", ".join([GROW_TYPE_NAMES[t] for t in GROW_TYPES])
            }
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get options flow."""
        return GrowFlowOptionsFlowHandler(config_entry)

class GrowFlowOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle GrowFlow options flow."""

    def __init__(self, config_entry: config_entries.ConfigEntry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Manage the options."""
        errors = {}
        
        if user_input is not None:
            # Prüfe ob Phase sich geändert hat
            old_phase = self.config_entry.options.get("current_phase", "germination")
            new_phase = user_input["current_phase"]
            
            options = dict(self.config_entry.options)
            options.update(user_input)
            
            # Wenn Phase gewechselt hat, update phase_start_date
            if old_phase != new_phase:
                options["phase_start_date"] = datetime.now().isoformat()
                _LOGGER.info(
                    "Phase changed from %s to %s for %s", 
                    old_phase, new_phase, self.config_entry.data["name"]
                )
            
            return self.async_create_entry(title="", data=options)

        # Current values
        current_phase = self.config_entry.options.get("current_phase", "germination")
        current_notes = self.config_entry.options.get("notes", "")
        
        data_schema = vol.Schema({
            vol.Required("current_phase", default=current_phase): vol.In(GROW_PHASES),
            vol.Optional("notes", default=current_notes): str,
        })

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "current_grow": self.config_entry.data["name"],
                "grow_type": GROW_TYPE_NAMES[self.config_entry.data["grow_type"]],
                "phases": ", ".join([PHASE_NAMES[p] for p in GROW_PHASES])
            }
        )