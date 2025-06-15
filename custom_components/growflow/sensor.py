"""Sensor platform for GrowFlow."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CONF_GROWBOX_NAME, CONF_PLANT_NAME
from .growbox.coordinator import GrowboxCoordinator
from .growbox.sensors import (
    GrowboxTemperatureSensor,
    GrowboxHumiditySensor,
    GrowboxVPDSensor,
    GrowboxTargetHumiditySensor,
)
from .plant.coordinator import PlantCoordinator
from .plant.sensors import (
    # Phase tracking sensors (updated with new phases)
    PlantDaysInCurrentPhaseSensor,
    PlantEarlyVegSensor,
    PlantMidLateVegSensor,
    PlantEarlyFlowerSensor,
    PlantMidLateFlowerSensor,
    PlantFlushingSensor,
    PlantDryingSensor,         # ✅ NEW: Drying phase sensor
    PlantCuringSensor,         # ✅ NEW: Curing phase sensor
    PlantTotalVegDaysSensor,
    PlantTotalFlowerDaysSensor,
    PlantTotalPostHarvestDaysSensor,  # ✅ NEW: Post-harvest summary
    PlantDaysSincePlantedSensor,
    PlantHistoryDebugSensor,
    # Watering sensors
    PlantLastWateringSensor,
    PlantDaysSinceWateringSensor,
    PlantWaterThisWeekSensor,
    PlantAvgWaterPerSessionSensor,
    PlantWateringFrequencySensor,
    PlantWateringDebugSensor,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up GrowFlow sensors."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    if isinstance(coordinator, GrowboxCoordinator):
        # Growbox Sensoren
        sensors = [
            GrowboxTemperatureSensor(coordinator),
            GrowboxHumiditySensor(coordinator),
            GrowboxVPDSensor(coordinator),
            GrowboxTargetHumiditySensor(coordinator),
        ]
    elif isinstance(coordinator, PlantCoordinator):
        # ✅ UPDATED: Plant Sensoren with new phases (Drying and Curing)
        sensors = [
            # Basic sensors
            PlantDaysSincePlantedSensor(coordinator),
            
            # Phase tracking sensors
            PlantDaysInCurrentPhaseSensor(coordinator),
            
            # Individual phase sensors (7 phases total)
            PlantEarlyVegSensor(coordinator),
            PlantMidLateVegSensor(coordinator),
            PlantEarlyFlowerSensor(coordinator),
            PlantMidLateFlowerSensor(coordinator),
            PlantFlushingSensor(coordinator),
            PlantDryingSensor(coordinator),         # ✅ NEW
            PlantCuringSensor(coordinator),         # ✅ NEW
            
            # Summary sensors
            PlantTotalVegDaysSensor(coordinator),
            PlantTotalFlowerDaysSensor(coordinator),
            PlantTotalPostHarvestDaysSensor(coordinator),  # ✅ NEW
            
            # Watering sensors
            PlantLastWateringSensor(coordinator),
            PlantDaysSinceWateringSensor(coordinator),
            PlantWaterThisWeekSensor(coordinator),
            PlantAvgWaterPerSessionSensor(coordinator),
            PlantWateringFrequencySensor(coordinator),
            
            # Debug sensors (disabled by default)
            PlantHistoryDebugSensor(coordinator),
            PlantWateringDebugSensor(coordinator),
        ]
    else:
        _LOGGER.error("Unknown coordinator type: %s", type(coordinator))
        return
    
    async_add_entities(sensors)