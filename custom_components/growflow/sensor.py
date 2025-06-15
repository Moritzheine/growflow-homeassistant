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
    # Phase tracking sensors
    PlantDaysInCurrentPhaseSensor,
    PlantEarlyVegSensor,
    PlantMidVegSensor,
    PlantLateVegSensor,
    PlantEarlyFlowerSensor,
    PlantMidFlowerSensor,
    PlantLateFlowerSensor,
    PlantFlushingSensor,
    PlantTotalVegDaysSensor,
    PlantTotalFlowerDaysSensor,
    PlantDaysSincePlantedSensor,
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
        # Plant Sensoren (nur Phase-Tracking)
        sensors = [
            # Basic sensors
            PlantDaysSincePlantedSensor(coordinator),
            
            # Phase tracking sensors
            PlantDaysInCurrentPhaseSensor(coordinator),
            
            # Individual phase sensors
            PlantEarlyVegSensor(coordinator),
            PlantMidVegSensor(coordinator),
            PlantLateVegSensor(coordinator),
            PlantEarlyFlowerSensor(coordinator),
            PlantMidFlowerSensor(coordinator),
            PlantLateFlowerSensor(coordinator),
            PlantFlushingSensor(coordinator),
            
            # Summary sensors
            PlantTotalVegDaysSensor(coordinator),
            PlantTotalFlowerDaysSensor(coordinator),
        ]
    else:
        _LOGGER.error("Unknown coordinator type: %s", type(coordinator))
        return
    
    async_add_entities(sensors)