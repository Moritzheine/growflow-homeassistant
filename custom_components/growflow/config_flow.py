"""Config flow for GrowFlow integration."""
from __future__ import annotations

import logging
import re
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    DOMAIN, 
    CONF_GROWBOX_NAME,
    CONF_TEMPERATURE_ENTITY,
    CONF_HUMIDITY_ENTITY,
    CONF_HYGROSTAT_ENTITY,
    CONF_TARGET_VPD,
    DEFAULT_TARGET_VPD,
    # Plant constants
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
        vol.Required(CONF_PLANTED_DATE): selector.DateSelector(),
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
    ) -> GrowFlowOptionsFlow:
        """Create the options flow."""
        return GrowFlowOptionsFlow(config_entry)

    def _generate_plant_name(self, strain: str) -> str:
        """Generate unique plant name with auto-numbering."""
        # Sanitize strain name
        clean_strain = re.sub(r'[^a-zA-Z0-9\s]', '', strain).strip()
        if not clean_strain:
            clean_strain = "Unknown"
        
        # Get existing plant entries
        existing_entries = self._async_current_entries()
        existing_numbers = set()
        
        # Find existing numbers for this strain
        for entry in existing_entries:
            if entry.data.get(CONF_PLANT_NAME):
                plant_name = entry.data[CONF_PLANT_NAME]
                # Extract number from name like "Blue Dream 1" -> 1
                if plant_name.startswith(clean_strain):
                    remaining = plant_name[len(clean_strain):].strip()
                    if remaining.isdigit():
                        existing_numbers.add(int(remaining))
        
        # Find next available number
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
            # Prüfen ob Growbox-Name bereits verwendet wird
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
            # Generate automatic plant name
            strain = user_input[CONF_PLANT_STRAIN]
            plant_name = self._generate_plant_name(strain)
            user_input[CONF_PLANT_NAME] = plant_name
            
            # Verfügbare Growboxen finden
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
            
            # Plant Entry direkt erstellen (keine Sensoren mehr)
            return self.async_create_entry(
                title=self._data[CONF_PLANT_NAME],
                data=self._data,
            )

        # Verfügbare Growboxen finden
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
            # Alle Daten zusammenführen
            self._data.update(user_input)
            
            # Growbox Entry erstellen
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
    """Handle options flow for GrowFlow."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            # Coordinator über die Änderungen informieren
            coordinator = self.hass.data[DOMAIN][self.config_entry.entry_id]
            coordinator.update_config(user_input)
            await coordinator.async_request_refresh()
            
            return self.async_create_entry(title="", data=user_input)

        # Aktuelle Werte als Default verwenden
        current_data = {**self.config_entry.data, **self.config_entry.options}
        
        # Unterschiedliche Schemas je nach Device-Typ
        if CONF_GROWBOX_NAME in current_data:
            # Growbox Options
            options_schema = vol.Schema(
                {
                    vol.Optional(
                        CONF_TEMPERATURE_ENTITY,
                        default=current_data.get(CONF_TEMPERATURE_ENTITY),
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="sensor", device_class="temperature")
                    ),
                    vol.Optional(
                        CONF_HUMIDITY_ENTITY,
                        default=current_data.get(CONF_HUMIDITY_ENTITY),
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="sensor", device_class="humidity")
                    ),
                    vol.Optional(
                        CONF_HYGROSTAT_ENTITY,
                        default=current_data.get(CONF_HYGROSTAT_ENTITY),
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain=["switch", "fan", "humidifier"])
                    ),
                    vol.Optional(
                        CONF_TARGET_VPD,
                        default=current_data.get(CONF_TARGET_VPD, DEFAULT_TARGET_VPD),
                    ): vol.All(vol.Coerce(float), vol.Range(min=0.4, max=2.0)),
                }
            )
        else:
            # Plant Options - keine Sensor-Konfiguration mehr
            options_schema = vol.Schema({})

        return self.async_show_form(
            step_id="init",
            data_schema=options_schema,
            description_placeholders={
                "device_name": self.config_entry.title,
            },
        )