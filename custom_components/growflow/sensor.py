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
    PlantSoilMoistureSensor,
    PlantECSensor,
    PlantPHSensor,
    PlantDaysSincePlantedSensor,
    PlantDaysSinceWateringSensor,
    PlantGrowthStageSensor,
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
        # Plant Sensoren
        sensors = [
            PlantSoilMoistureSensor(coordinator),
            PlantECSensor(coordinator),
            PlantPHSensor(coordinator),
            PlantDaysSincePlantedSensor(coordinator),
            PlantDaysSinceWateringSensor(coordinator),
            PlantGrowthStageSensor(coordinator),
        ]
    else:
        _LOGGER.error("Unknown coordinator type: %s", type(coordinator))
        return
    
    async_add_entities(sensors)