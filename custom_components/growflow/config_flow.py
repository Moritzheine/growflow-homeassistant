"""Config flow for GrowFlow integration."""
from __future__ import annotations

import logging
import re
from typing import Any
from datetime import date

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN, 
    CONF_GROWBOX_NAME,
    CONF_TEMPERATURE_ENTITY,
    CONF_HUMIDITY_ENTITY,
    CONF_HYGROSTAT_ENTITY,
    CONF_TARGET_VPD,
    DEFAULT_TARGET_VPD,
    CONF_PLANT_NAME,
    CONF_PLANT_STRAIN,
    CONF_PLANT_GROWBOX,
    CONF_PLANTED_DATE,
    CONF_GROWTH_STAGE,
    GROWTH_STAGES,
    GROWTH_STAGE_EARLY_VEG,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("device_type", default="growbox"): vol.In(["growbox", "plant"]),
    }
)

STEP_GROWBOX_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_GROWBOX_NAME, default="Growbox 1"): str,
    }
)

STEP_PLANT_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_PLANT_STRAIN, default="Unknown"): str,
        vol.Required(CONF_PLANTED_DATE, default=dt_util.now().date()): selector.DateSelector(),
        vol.Optional(CONF_GROWTH_STAGE, default=GROWTH_STAGE_EARLY_VEG): vol.In(GROWTH_STAGES),
    }
)

STEP_SENSORS_DATA_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_TEMPERATURE_ENTITY): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="sensor", device_class="temperature")
        ),
        vol.Optional(CONF_HUMIDITY_ENTITY): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="sensor", device_class="humidity")
        ),
        vol.Optional(CONF_HYGROSTAT_ENTITY): selector.EntitySelector(
            selector.EntitySelectorConfig(domain=["switch", "fan", "humidifier"])
        ),
        vol.Optional(CONF_TARGET_VPD, default=DEFAULT_TARGET_VPD): vol.All(
            vol.Coerce(float), vol.Range(min=0.4, max=2.0)
        ),
    }
)


class GrowFlowConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for GrowFlow."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize config flow."""
        self._data: dict[str, Any] = {}
        self._device_type: str | None = None

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> GrowFlowOptionsFlow | None:
        """Create the options flow only for growboxes."""
        if CONF_GROWBOX_NAME in config_entry.data:
            return GrowFlowOptionsFlow()
        return None

    def _generate_plant_name(self, strain: str) -> str:
        """Generate unique plant name with auto-numbering."""
        clean_strain = re.sub(r'[^a-zA-Z0-9\s]', '', strain).strip()
        if not clean_strain:
            clean_strain = "Unknown"
        
        existing_entries = self._async_current_entries()
        existing_numbers = set()
        
        for entry in existing_entries:
            if entry.data.get(CONF_PLANT_NAME):
                plant_name = entry.data[CONF_PLANT_NAME]
                if plant_name.startswith(clean_strain):
                    remaining = plant_name[len(clean_strain):].strip()
                    if remaining.isdigit():
                        existing_numbers.add(int(remaining))
        
        next_number = 1
        while next_number in existing_numbers:
            next_number += 1
        
        return f"{clean_strain} {next_number}"

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step - choose device type."""
        if user_input is not None:
            self._device_type = user_input["device_type"]
            if self._device_type == "growbox":
                return await self.async_step_growbox()
            else:
                return await self.async_step_plant()

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
        )

    async def async_step_growbox(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle growbox configuration."""
        errors: dict[str, str] = {}

        if user_input is not None:
            existing_entries = self._async_current_entries()
            for entry in existing_entries:
                if entry.data.get(CONF_GROWBOX_NAME) == user_input[CONF_GROWBOX_NAME]:
                    errors["base"] = "name_exists"
                    break

            if not errors:
                self._data.update(user_input)
                return await self.async_step_sensors()

        return self.async_show_form(
            step_id="growbox",
            data_schema=STEP_GROWBOX_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_plant(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle plant configuration."""
        errors: dict[str, str] = {}

        if user_input is not None:
            planted_date = user_input.get(CONF_PLANTED_DATE)
            
            try:
                if planted_date is None or planted_date == "":
                    user_input[CONF_PLANTED_DATE] = dt_util.now().date()
                    _LOGGER.warning("No planted date provided, using today")
                elif isinstance(planted_date, str):
                    if planted_date.strip() == "":
                        user_input[CONF_PLANTED_DATE] = dt_util.now().date()
                    else:
                        parsed_date = dt_util.parse_date(planted_date)
                        if parsed_date:
                            user_input[CONF_PLANTED_DATE] = parsed_date
                        else:
                            user_input[CONF_PLANTED_DATE] = dt_util.now().date()
                            _LOGGER.error("Could not parse planted date: %s", planted_date)
                elif not isinstance(planted_date, date):
                    user_input[CONF_PLANTED_DATE] = dt_util.now().date()
                    _LOGGER.error("Invalid planted date type: %s", type(planted_date))
                
                today = dt_util.now().date()
                if user_input[CONF_PLANTED_DATE] > today:
                    user_input[CONF_PLANTED_DATE] = today
                    _LOGGER.warning("Planted date was in future, using today")
                    
            except Exception as e:
                user_input[CONF_PLANTED_DATE] = dt_util.now().date()
                _LOGGER.error("Error processing planted date: %s", str(e))
            
            strain = user_input[CONF_PLANT_STRAIN]
            plant_name = self._generate_plant_name(strain)
            user_input[CONF_PLANT_NAME] = plant_name
            
            existing_entries = self._async_current_entries()
            available_growboxes = []
            for entry in existing_entries:
                if entry.data.get(CONF_GROWBOX_NAME):
                    available_growboxes.append(entry.data[CONF_GROWBOX_NAME])
            
            if not available_growboxes:
                errors["base"] = "no_growboxes"
            else:
                self._data.update(user_input)
                return await self.async_step_plant_growbox()

        return self.async_show_form(
            step_id="plant",
            data_schema=STEP_PLANT_DATA_SCHEMA,
            errors=errors,
            description_placeholders={
                "info": "Der Gerätename wird automatisch generiert: {Strain} {Nummer}"
            },
        )

    async def async_step_plant_growbox(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle plant growbox assignment."""
        if user_input is not None:
            self._data.update(user_input)
            
            return self.async_create_entry(
                title=self._data[CONF_PLANT_NAME],
                data=self._data,
            )

        existing_entries = self._async_current_entries()
        available_growboxes = []
        for entry in existing_entries:
            if entry.data.get(CONF_GROWBOX_NAME):
                available_growboxes.append(entry.data[CONF_GROWBOX_NAME])

        growbox_schema = vol.Schema({
            vol.Required(CONF_PLANT_GROWBOX): vol.In(available_growboxes),
        })

        return self.async_show_form(
            step_id="plant_growbox",
            data_schema=growbox_schema,
            description_placeholders={
                "plant_name": self._data.get(CONF_PLANT_NAME, "Plant"),
            },
        )

    async def async_step_sensors(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle growbox sensor configuration step."""
        if user_input is not None:
            self._data.update(user_input)
            
            return self.async_create_entry(
                title=self._data[CONF_GROWBOX_NAME],
                data=self._data,
            )

        return self.async_show_form(
            step_id="sensors",
            data_schema=STEP_SENSORS_DATA_SCHEMA,
            description_placeholders={
                "growbox_name": self._data[CONF_GROWBOX_NAME],
            },
        )


class GrowFlowOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for GrowFlow - Growboxes only."""

    def _clean_entity_value(self, value: Any) -> str | None:
        """Clean entity selector value, return None for empty/invalid values."""
        _LOGGER.debug(f"Cleaning entity value: {repr(value)} (type: {type(value)})")
        
        if value is None:
            return None
        if value == "":
            return None
        if value == "None":
            return None
        if isinstance(value, str):
            stripped = value.strip()
            if stripped == "":
                return None
            if stripped.lower() == "none":
                return None
            if stripped == "null":
                return None
            return stripped
        return str(value) if value else None

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options for growboxes only."""
        if user_input is not None:
            _LOGGER.debug(f"Received user input: {user_input}")
            
            # Start fresh - only keep what's actually in user_input
            cleaned_input = {}
            
            # Check all possible entity fields
            entity_fields = [CONF_TEMPERATURE_ENTITY, CONF_HUMIDITY_ENTITY, CONF_HYGROSTAT_ENTITY]
            
            for key in entity_fields:
                if key in user_input:
                    # Entity was present in form - check if valid
                    cleaned_value = self._clean_entity_value(user_input[key])
                    if cleaned_value is not None:
                        cleaned_input[key] = cleaned_value
                        _LOGGER.debug(f"Keeping entity {key}: {cleaned_value}")
                    else:
                        _LOGGER.debug(f"Entity {key} had empty value, removing")
                else:
                    # Entity was NOT in user_input - user cleared it with X button
                    _LOGGER.debug(f"Entity {key} missing from input - was cleared by user")
            
            # Handle non-entity fields (but remove target_vpd as requested)
            for key, value in user_input.items():
                if key not in entity_fields and key != CONF_TARGET_VPD:
                    cleaned_input[key] = value
            
            _LOGGER.debug(f"Final cleaned input: {cleaned_input}")
            
            coordinator = self.hass.data[DOMAIN][self.config_entry.entry_id]
            coordinator.update_config(user_input)
            await coordinator.async_request_refresh()
            
            return self.async_create_entry(title="", data=cleaned_input)

        current_data = {**self.config_entry.data, **self.config_entry.options}
        
        if CONF_GROWBOX_NAME not in current_data:
            return self.async_abort(reason="not_supported")
        
        # Create schema with proper defaults for entity selectors
        # Priority: options > data (options can override/clear entities from data)
        schema_dict = {}
        
        # Check if entity is configured (options override data, None means removed)
        entity_configs = {}
        for entity_key in [CONF_TEMPERATURE_ENTITY, CONF_HUMIDITY_ENTITY, CONF_HYGROSTAT_ENTITY]:
            if entity_key in self.config_entry.options:
                # Options have this key, use its value (could be None if cleared)
                entity_configs[entity_key] = self.config_entry.options[entity_key]
            else:
                # Not in options, use original data value
                entity_configs[entity_key] = self.config_entry.data.get(entity_key)
        
        # Temperature entity
        temp_entity = entity_configs[CONF_TEMPERATURE_ENTITY]
        if temp_entity:
            schema_dict[vol.Optional(CONF_TEMPERATURE_ENTITY, default=temp_entity)] = selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor", device_class="temperature")
            )
        else:
            schema_dict[vol.Optional(CONF_TEMPERATURE_ENTITY)] = selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor", device_class="temperature")
            )
        
        # Humidity entity
        humidity_entity = entity_configs[CONF_HUMIDITY_ENTITY]
        if humidity_entity:
            schema_dict[vol.Optional(CONF_HUMIDITY_ENTITY, default=humidity_entity)] = selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor", device_class="humidity")
            )
        else:
            schema_dict[vol.Optional(CONF_HUMIDITY_ENTITY)] = selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor", device_class="humidity")
            )
        
        # Hygrostat entity
        hygrostat_entity = entity_configs[CONF_HYGROSTAT_ENTITY]
        if hygrostat_entity:
            schema_dict[vol.Optional(CONF_HYGROSTAT_ENTITY, default=hygrostat_entity)] = selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["switch", "fan", "humidifier"])
            )
        else:
            schema_dict[vol.Optional(CONF_HYGROSTAT_ENTITY)] = selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["switch", "fan", "humidifier"])
            )
        
        options_schema = vol.Schema(schema_dict)

        return self.async_show_form(
            step_id="init",
            data_schema=options_schema,
            description_placeholders={
                "device_name": current_data.get(CONF_GROWBOX_NAME, "Growbox"),
            },
        )