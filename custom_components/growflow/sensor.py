"""GrowFlow sensor platform."""
import logging
from datetime import datetime, timedelta, date
from typing import Optional

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo

from .const import (
    DOMAIN, 
    PHASE_NAMES, 
    PHASE_ICONS,
    PHASE_DURATIONS,
    ATTR_PLANTED_DATE,
    ATTR_GROW_TYPE,
    ATTR_PHASE_KEY,
    ATTR_NOTES,
    ATTR_PHASE_START_DATE
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up GrowFlow sensors."""
    
    grow_data = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = [
        DaysSincePlantedSensor(config_entry, grow_data),
        CurrentPhaseSensor(config_entry, grow_data),
        DaysInPhaseSensor(config_entry, grow_data),
        TotalGrowDaysSensor(config_entry, grow_data),
        ExpectedHarvestSensor(config_entry, grow_data),
    ]
    
    async_add_entities(entities)

class GrowFlowSensorBase(SensorEntity):
    """Base class for GrowFlow sensors."""

    def __init__(self, config_entry: ConfigEntry, grow_data: dict):
        """Initialize the sensor."""
        self._config_entry = config_entry
        self._grow_data = grow_data
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
    def should_poll(self) -> bool:
        """No polling needed."""
        return False

class DaysSincePlantedSensor(GrowFlowSensorBase):
    """Sensor für Tage seit Einpflanzen."""

    def __init__(self, config_entry: ConfigEntry, grow_data: dict):
        """Initialize the sensor."""
        super().__init__(config_entry, grow_data)
        self._attr_name = f"{grow_data['name']} Days Since Planted"
        self._attr_unique_id = f"{config_entry.entry_id}_days_since_planted"
        self._attr_icon = "mdi:calendar-today"
        self._attr_native_unit_of_measurement = "days"
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING

    @property
    def native_value(self) -> int:
        """Return the state of the sensor."""
        planted_date = self.grow_data["planted_date"]
        if isinstance(planted_date, str):
            try:
                planted_date = datetime.fromisoformat(planted_date)
            except ValueError:
                planted_date = datetime.now()
        
        days_diff = (datetime.now() - planted_date).days
        return max(0, days_diff)

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional attributes."""
        planted_date = self.grow_data["planted_date"]
        if isinstance(planted_date, str):
            date_str = planted_date
        else:
            date_str = planted_date.strftime("%Y-%m-%d")
            
        return {
            ATTR_PLANTED_DATE: date_str,
            ATTR_GROW_TYPE: self.grow_data["grow_type"],
        }

class CurrentPhaseSensor(GrowFlowSensorBase):
    """Sensor für aktuelle Phase."""

    def __init__(self, config_entry: ConfigEntry, grow_data: dict):
        """Initialize the sensor."""
        super().__init__(config_entry, grow_data)
        self._attr_name = f"{grow_data['name']} Current Phase"
        self._attr_unique_id = f"{config_entry.entry_id}_current_phase"

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        phase = self.grow_data["current_phase"]
        return PHASE_NAMES.get(phase, phase)

    @property
    def icon(self) -> str:
        """Return the icon."""
        phase = self.grow_data["current_phase"]
        return PHASE_ICONS.get(phase, "mdi:flower")

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional attributes."""
        phase_start = self.grow_data.get("phase_start_date")
        if isinstance(phase_start, datetime):
            phase_start_str = phase_start.isoformat()
        else:
            phase_start_str = str(phase_start) if phase_start else ""
            
        return {
            ATTR_PHASE_KEY: self.grow_data["current_phase"],
            ATTR_NOTES: self.grow_data.get("notes", ""),
            ATTR_PHASE_START_DATE: phase_start_str,
        }

class DaysInPhaseSensor(GrowFlowSensorBase):
    """Sensor für Tage in aktueller Phase."""

    def __init__(self, config_entry: ConfigEntry, grow_data: dict):
        """Initialize the sensor."""
        super().__init__(config_entry, grow_data)
        self._attr_name = f"{grow_data['name']} Days in Phase"
        self._attr_unique_id = f"{config_entry.entry_id}_days_in_phase"
        self._attr_icon = "mdi:timer-outline"
        self._attr_native_unit_of_measurement = "days"
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> int:
        """Return the state of the sensor."""
        phase_start = self.grow_data.get("phase_start_date")
        
        if not phase_start:
            # Fallback zu planted_date
            phase_start = self.grow_data["planted_date"]
        
        # Handle verschiedene Datumsformate
        if isinstance(phase_start, str):
            try:
                phase_start = datetime.fromisoformat(phase_start)
            except ValueError:
                try:
                    phase_start = datetime.strptime(phase_start, "%Y-%m-%d")
                except ValueError:
                    phase_start = datetime.now()
        
        days_diff = (datetime.now() - phase_start).days
        return max(0, days_diff)

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional attributes."""
        phase = self.grow_data["current_phase"]
        grow_type = self.grow_data["grow_type"]
        expected_duration = PHASE_DURATIONS.get(grow_type, {}).get(phase, 0)
        
        return {
            "current_phase": PHASE_NAMES.get(phase, phase),
            "expected_duration_days": expected_duration,
        }

class TotalGrowDaysSensor(GrowFlowSensorBase):
    """Sensor für Gesamttage des Grows."""

    def __init__(self, config_entry: ConfigEntry, grow_data: dict):
        """Initialize the sensor."""
        super().__init__(config_entry, grow_data)
        self._attr_name = f"{grow_data['name']} Total Grow Days"
        self._attr_unique_id = f"{config_entry.entry_id}_total_grow_days"
        self._attr_icon = "mdi:calendar-range"
        self._attr_native_unit_of_measurement = "days"
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING

    @property
    def native_value(self) -> int:
        """Return the state of the sensor."""
        planted_date = self.grow_data["planted_date"]
        if isinstance(planted_date, str):
            try:
                planted_date = datetime.fromisoformat(planted_date)
            except ValueError:
                planted_date = datetime.now()
                
        days_diff = (datetime.now() - planted_date).days
        return max(0, days_diff)

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional attributes."""
        grow_type = self.grow_data["grow_type"]
        
        # Berechne erwartete Gesamtdauer
        total_expected = sum(PHASE_DURATIONS.get(grow_type, {}).values())
        
        return {
            "expected_total_days": total_expected,
            "grow_type": grow_type,
            "completion_percentage": round((self.native_value / total_expected * 100), 1) if total_expected > 0 else 0,
        }

class ExpectedHarvestSensor(GrowFlowSensorBase):
    """Sensor für erwartetes Erntedatum."""

    def __init__(self, config_entry: ConfigEntry, grow_data: dict):
        """Initialize the sensor."""
        super().__init__(config_entry, grow_data)
        self._attr_name = f"{grow_data['name']} Expected Harvest"
        self._attr_unique_id = f"{config_entry.entry_id}_expected_harvest"
        self._attr_icon = "mdi:calendar-clock"
        # KEIN device_class = DATE! Das verursacht den Fehler
        # self._attr_device_class = SensorDeviceClass.DATE

    @property
    def native_value(self) -> Optional[str]:
        """Return the expected harvest date as string."""
        planted_date = self.grow_data["planted_date"]
        if isinstance(planted_date, str):
            try:
                planted_date = datetime.fromisoformat(planted_date)
            except ValueError:
                return None
                
        grow_type = self.grow_data["grow_type"]
        
        # Berechne erwartete Gesamtdauer bis Ernte
        durations = PHASE_DURATIONS.get(grow_type, {})
        total_days = sum([
            durations.get("germination", 0),
            durations.get("seedling", 0),
            durations.get("vegetative", 0),
            durations.get("flowering", 0),
        ])
        
        if total_days > 0:
            expected_harvest = planted_date + timedelta(days=total_days)
            return expected_harvest.strftime("%Y-%m-%d")
        
        return None

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional attributes."""
        grow_type = self.grow_data["grow_type"]
        durations = PHASE_DURATIONS.get(grow_type, {})
        
        return {
            "grow_type": grow_type,
            "expected_germination_days": durations.get("germination", 0),
            "expected_seedling_days": durations.get("seedling", 0),
            "expected_vegetative_days": durations.get("vegetative", 0),
            "expected_flowering_days": durations.get("flowering", 0),
        }