"""Constants for GrowFlow integration."""
from datetime import datetime

DOMAIN = "growflow"

# Grow Types
GROW_TYPES = [
    "soil",          # Erde/Substrat
    "hydroponic",    # Hydroponik/DWC
    "autoflower"     # Autoflower
]

# Grow Phases
GROW_PHASES = [
    "germination",   # Keimung
    "seedling",      # Sämling
    "vegetative",    # Wachstumsphase
    "flowering",     # Blütephase
    "harvest",       # Ernte
    "drying"         # Trocknung
]

# Übersetzungen für UI
GROW_TYPE_NAMES = {
    "soil": "Erde/Substrat",
    "hydroponic": "Hydroponik/DWC", 
    "autoflower": "Autoflower"
}

PHASE_NAMES = {
    "germination": "Keimung",
    "seedling": "Sämling", 
    "vegetative": "Wachstumsphase",
    "flowering": "Blütephase",
    "harvest": "Ernte",
    "drying": "Trocknung"
}

# Phase Icons
PHASE_ICONS = {
    "germination": "mdi:seed",
    "seedling": "mdi:sprout",
    "vegetative": "mdi:leaf",
    "flowering": "mdi:flower",
    "harvest": "mdi:cannabis",
    "drying": "mdi:hair-dryer"
}

# Default phase durations (in days) - für UI hints
PHASE_DURATIONS = {
    "soil": {
        "germination": 7,
        "seedling": 14,
        "vegetative": 42,
        "flowering": 56,
        "harvest": 1,
        "drying": 14
    },
    "hydroponic": {
        "germination": 5,
        "seedling": 10,
        "vegetative": 35,
        "flowering": 49,
        "harvest": 1,
        "drying": 14
    },
    "autoflower": {
        "germination": 5,
        "seedling": 14,
        "vegetative": 28,
        "flowering": 35,
        "harvest": 1,
        "drying": 14
    }
}

# Event names
EVENT_PHASE_CHANGED = f"{DOMAIN}_phase_changed"
EVENT_WATERING_ADDED = f"{DOMAIN}_watering_added"
EVENT_NUTRIENTS_CHANGED = f"{DOMAIN}_nutrients_changed"

# Service names
SERVICE_ADD_WATERING = "add_watering"
SERVICE_CHANGE_PHASE = "change_phase"
SERVICE_CHANGE_NUTRIENTS = "change_nutrients"

# Attribute names
ATTR_PLANTED_DATE = "planted_date"
ATTR_GROW_TYPE = "grow_type"
ATTR_PHASE_KEY = "phase_key"
ATTR_NOTES = "notes"
ATTR_AMOUNT_ML = "amount_ml"
ATTR_TIMESTAMP = "timestamp"
ATTR_PHASE_START_DATE = "phase_start_date"