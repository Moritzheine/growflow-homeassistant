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

# Plant config
CONF_PLANT_NAME = "plant_name"
CONF_PLANT_STRAIN = "plant_strain"
CONF_PLANT_GROWBOX = "plant_growbox"
CONF_PLANTED_DATE = "planted_date"
CONF_GROWTH_STAGE = "growth_stage"
CONF_SOIL_MOISTURE_ENTITY = "soil_moisture_entity"
CONF_EC_ENTITY = "ec_entity"
CONF_PH_ENTITY = "ph_entity"

# Growth stages
GROWTH_STAGE_SEEDLING = "seedling"
GROWTH_STAGE_VEGETATIVE = "vegetative"
GROWTH_STAGE_FLOWERING = "flowering"
GROWTH_STAGE_HARVEST = "harvest"

GROWTH_STAGES = [
    GROWTH_STAGE_SEEDLING,
    GROWTH_STAGE_VEGETATIVE,
    GROWTH_STAGE_FLOWERING,
    GROWTH_STAGE_HARVEST,
]

# Plant device classes
PLANT_DEVICE_CLASS_MOISTURE = "moisture"
PLANT_DEVICE_CLASS_EC = "voltage"  # mS/cm ähnlich voltage
PLANT_DEVICE_CLASS_PH = "ph"

# Plant units
UNIT_DAYS = "days"
UNIT_EC = "mS/cm"
UNIT_PH = "pH"
UNIT_ML = "ml"

# Services
SERVICE_WATER_PLANT = "water_plant"
SERVICE_FERTILIZE_PLANT = "fertilize_plant"
SERVICE_CHANGE_PHASE = "change_phase"
SERVICE_ADD_NOTE = "add_note"