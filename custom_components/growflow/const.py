"""Constants for the GrowFlow integration."""

# Integration info
DOMAIN = "growflow"
MANUFACTURER = "GrowFlow"
MODEL = "Growbox"

# Config flow
CONF_GROWBOX_NAME = "growbox_name"
CONF_TEMPERATURE_ENTITY = "temperature_entity"
CONF_HUMIDITY_ENTITY = "humidity_entity"
CONF_HYGROSTAT_ENTITY = "hygrostat_entity"
CONF_LIGHT_SCHEDULE = "light_schedule"
CONF_TARGET_VPD = "target_vpd"

# Device classes
DEVICE_CLASS_TEMPERATURE = "temperature"
DEVICE_CLASS_HUMIDITY = "humidity"
DEVICE_CLASS_PRESSURE = "pressure"  # VPD

# Units
UNIT_CELSIUS = "°C"
UNIT_PERCENT = "%" 
UNIT_KPA = "kPa"

# VPD Konstanten (vereinfacht)
VPD_MIN = 0.5  # kPa
VPD_MAX = 1.5  # kPa
VPD_OPTIMAL = 1.0  # kPa

# Update intervals
SCAN_INTERVAL = 30  # seconds

# Entry types
ENTRY_TYPE_SERVICE = "service"
ENTRY_TYPE_DEVICE = "device"

# Default values
DEFAULT_TARGET_VPD = 1.0
DEFAULT_UPDATE_INTERVAL = 30

# Attributes
ATTR_TARGET_VPD = "target_vpd"
ATTR_TARGET_HUMIDITY = "target_humidity"
ATTR_VPD_STATUS = "vpd_status"

# Plant config (simplified)
CONF_PLANT_NAME = "plant_name"
CONF_PLANT_STRAIN = "plant_strain"
CONF_PLANT_GROWBOX = "plant_growbox"
CONF_PLANTED_DATE = "planted_date"
CONF_GROWTH_STAGE = "growth_stage"

# Watering System
CONF_DEFAULT_WATER_VOLUME = "default_water_volume"
DEFAULT_WATER_VOLUME = 2000  # 2 Liter in ml

# New Growth stages (detailed)
GROWTH_STAGE_EARLY_VEG = "early_veg"
GROWTH_STAGE_MID_VEG = "mid_veg"
GROWTH_STAGE_LATE_VEG = "late_veg"
GROWTH_STAGE_EARLY_FLOWER = "early_flower"
GROWTH_STAGE_MID_FLOWER = "mid_flower"
GROWTH_STAGE_LATE_FLOWER = "late_flower"
GROWTH_STAGE_FLUSHING = "flushing"
GROWTH_STAGE_DONE = "done"

# Growth stage labels for UI
GROWTH_STAGE_LABELS = {
    GROWTH_STAGE_EARLY_VEG: "Early Veg",
    GROWTH_STAGE_MID_VEG: "Mid Veg",
    GROWTH_STAGE_LATE_VEG: "Late Veg",
    GROWTH_STAGE_EARLY_FLOWER: "Early Flower",
    GROWTH_STAGE_MID_FLOWER: "Mid Flower",
    GROWTH_STAGE_LATE_FLOWER: "Late Flower",
    GROWTH_STAGE_FLUSHING: "Flushing",
    GROWTH_STAGE_DONE: "Ernte/Fertig",
}

GROWTH_STAGES = [
    GROWTH_STAGE_EARLY_VEG,
    GROWTH_STAGE_MID_VEG,
    GROWTH_STAGE_LATE_VEG,
    GROWTH_STAGE_EARLY_FLOWER,
    GROWTH_STAGE_MID_FLOWER,
    GROWTH_STAGE_LATE_FLOWER,
    GROWTH_STAGE_FLUSHING,
    GROWTH_STAGE_DONE,
]

# Legacy growth stages (for backward compatibility) 
GROWTH_STAGE_SEEDLING = "early_veg"  # Map to new system
GROWTH_STAGE_VEGETATIVE = "mid_veg"
GROWTH_STAGE_FLOWERING = "early_flower"
GROWTH_STAGE_HARVEST = "done"

# Plant device classes (not used anymore)
# PLANT_DEVICE_CLASS_MOISTURE = "moisture"

# Plant units (simplified)
UNIT_DAYS = "days"
UNIT_ML = "ml"

# Services (simplified)
SERVICE_CHANGE_PHASE = "change_phase"
SERVICE_ADD_NOTE = "add_note"
# Watering Services
SERVICE_WATER_PLANT = "water_plant"
SERVICE_WATER_PLANT_QUICK = "water_plant_quick"

# Phase tracking attributes
ATTR_PHASE_HISTORY = "phase_history"
ATTR_CURRENT_PHASE_START = "current_phase_start"
ATTR_TOTAL_VEG_DAYS = "total_veg_days"
ATTR_TOTAL_FLOWER_DAYS = "total_flower_days"

# Vegetative and flowering phase lists
VEG_PHASES = [GROWTH_STAGE_EARLY_VEG, GROWTH_STAGE_MID_VEG, GROWTH_STAGE_LATE_VEG]
FLOWER_PHASES = [GROWTH_STAGE_EARLY_FLOWER, GROWTH_STAGE_MID_FLOWER, GROWTH_STAGE_LATE_FLOWER, GROWTH_STAGE_FLUSHING]