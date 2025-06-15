# 🌱 GrowFlow - Cannabis Plant Tracker for Home Assistant

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)
[![hacs][hacsbadge]][hacs]
[![Community Forum][forum-shield]][forum]

**Track your cannabis plants like a pro with Home Assistant!**

GrowFlow is a comprehensive Home Assistant integration for tracking cannabis cultivation. Monitor growth phases, watering schedules, and plant development with detailed analytics and automation capabilities.

![GrowFlow Dashboard](https://raw.githubusercontent.com/moritzheine/growflow-homeassistant/main/images/dashboard-preview.png)

## ✨ Features

### 🌿 **Growth Phase Tracking**

- **6 Detailed Growth Phases**: Early Veg, Mid Late VEG, Early Flower, Mid Late Flower, Flushing, Done
- **Automatic Time Tracking**: Days in each phase with persistent history
- **Phase Transition Logging**: Complete timeline of your plant's development
- **Visual Phase Icons**: Clear UI indicators for each growth stage

### 💧 **Watering System**

- **One-Click Watering**: Quick watering button with customizable default volumes
- **Detailed Water Logging**: Track volume, timing, and notes for every watering
- **Smart Analytics**: Weekly consumption, average per session, frequency patterns
- **Watering Reminders**: Days since last watering with status indicators

### 📊 **Comprehensive Analytics**

- **Growth Statistics**: Total days, phase breakdowns, development patterns
- **Water Analytics**: Consumption trends, frequency analysis, session averages
- **Historical Data**: Complete plant timeline from seed to harvest
- **Debug Sensors**: Detailed tracking information for troubleshooting

### 🏠 **Growbox Integration**

- **Multi-Device Support**: Track multiple plants across different growboxes
- **Device Hierarchy**: Organize plants under their respective growing environments
- **Automatic Naming**: Smart plant naming with strain-based numbering

### 🔧 **Home Assistant Native**

- **Config Flow Setup**: Easy configuration through the UI
- **Entity Management**: Date, Text, Select, Button, Number, and Sensor entities
- **Service Integration**: Automate watering logs and phase changes
- **YAML Configuration**: Full automation support with service calls

## 📦 Installation

### HACS (Recommended)

1. **Add Custom Repository**:

   - Go to HACS → Integrations → ⋮ → Custom repositories
   - Add: `https://github.com/moritzheine/growflow-homeassistant`
   - Category: `Integration`

2. **Install GrowFlow**:

   - Search for "GrowFlow" in HACS
   - Click Install → Install
   - Restart Home Assistant

3. **Add Integration**:
   - Go to Settings → Devices & Services → Add Integration
   - Search for "GrowFlow" → Add

### Manual Installation

1. Download the `growflow` folder from the latest release
2. Copy to `custom_components/growflow/` in your Home Assistant configuration
3. Restart Home Assistant
4. Add the integration via Settings → Devices & Services

## 🔧 Configuration

### Adding a Growbox

1. **Settings** → **Devices & Services** → **Add Integration**
2. Search for **"GrowFlow"** → Select **"growbox"**
3. Configure:
   - **Growbox Name**: e.g., "Tent 1"
   - **Temperature Sensor** (optional): Link existing sensor
   - **Humidity Sensor** (optional): Link existing sensor
   - **Hygrostat Control** (optional): Link humidity control device

### Adding a Plant

1. **Add Integration** → **GrowFlow** → Select **"plant"**
2. Configure:
   - **Strain Name**: e.g., "Blue Dream"
   - **Planted Date**: When you planted/started the seed
   - **Growth Phase**: Current stage (default: Early Veg)
   - **Growbox**: Select from existing growboxes

**Automatic Naming**: Plants are automatically named like "Blue Dream 1", "White Widow 2", etc.

## 🎮 Usage

### Entity Overview

Each plant creates the following entities:

#### **User Controls**

- `button.plant_name_water_quick` - Quick watering with default volume
- `number.plant_name_default_water_volume` - Adjust default water amount (100-5000ml)
- `date.plant_name_planted_date` - Edit planting date
- `text.plant_name_strain` - Edit strain name
- `select.plant_name_growth_phase` - Change growth phase

#### **Growth Tracking Sensors**

- `sensor.plant_name_days_since_planted` - Total days since planting
- `sensor.plant_name_days_in_current_phase` - Days in current growth phase
- `sensor.plant_name_days_in_early_veg` - Time spent in Early Veg
- `sensor.plant_name_days_in_mid_late_veg` - Time spent in Mid Late VEG
- `sensor.plant_name_days_in_early_flower` - Time spent in Early Flower
- `sensor.plant_name_days_in_mid_late_flower` - Time spent in Mid Late Flower
- `sensor.plant_name_days_in_flushing` - Time spent flushing
- `sensor.plant_name_total_veg_days` - Total vegetative days
- `sensor.plant_name_total_flower_days` - Total flowering days

#### **Watering Tracking Sensors**

- `sensor.plant_name_last_watering` - Timestamp of last watering
- `sensor.plant_name_days_since_watering` - Days since last watering
- `sensor.plant_name_water_this_week` - Water volume in last 7 days
- `sensor.plant_name_avg_water_per_session` - Average ml per watering
- `sensor.plant_name_watering_frequency` - Average days between waterings

### Services

#### **growflow.water_plant**

Log a watering session with custom volume:

```yaml
service: growflow.water_plant
data:
  entity_id: sensor.blue_dream_1_days_since_planted
  volume_ml: 2000
  notes: "Post-fertilizer watering"
```

#### **growflow.water_plant_quick**

Quick watering with default volume:

```yaml
service: growflow.water_plant_quick
data:
  entity_id: sensor.blue_dream_1_days_since_planted
```

#### **growflow.change_phase**

Change growth phase:

```yaml
service: growflow.change_phase
data:
  entity_id: sensor.blue_dream_1_days_since_planted
  new_stage: mid_late_flower
  notes: "Switched to 12/12 light cycle"
```

## 📱 Dashboard Examples

### Basic Plant Card

```yaml
type: entities
title: Blue Dream 1
entities:
  - entity: button.blue_dream_1_water_quick
    name: "💧 Water Plant"
  - entity: sensor.blue_dream_1_days_since_planted
    name: "📅 Total Days"
  - entity: sensor.blue_dream_1_days_in_current_phase
    name: "🌱 Current Phase Days"
  - entity: sensor.blue_dream_1_days_since_watering
    name: "💦 Days Since Watering"
  - entity: select.blue_dream_1_growth_phase
    name: "🔄 Growth Phase"
```

### Watering Analytics

```yaml
type: entities
title: Watering Analytics
entities:
  - sensor.blue_dream_1_water_this_week
  - sensor.blue_dream_1_avg_water_per_session
  - sensor.blue_dream_1_watering_frequency
  - sensor.blue_dream_1_last_watering
```

## 🤖 Automation Examples

### Watering Reminder

```yaml
automation:
  - alias: "Plant Watering Reminder"
    trigger:
      platform: numeric_state
      entity_id: sensor.blue_dream_1_days_since_watering
      above: 3
    action:
      service: notify.mobile_app_your_phone
      data:
        title: "🌱 Plant Care Reminder"
        message: "Blue Dream 1 hasn't been watered for {{ states('sensor.blue_dream_1_days_since_watering') }} days!"
```

### Auto-Log Irrigation System

```yaml
automation:
  - alias: "Auto-Log Drip System"
    trigger:
      platform: state
      entity_id: switch.drip_system_zone_1
      to: "off"
    action:
      service: growflow.water_plant
      data:
        entity_id: sensor.blue_dream_1_days_since_planted
        volume_ml: 1500
        notes: "Automated drip irrigation"
```

### Phase Change Notifications

```yaml
automation:
  - alias: "Growth Phase Changed"
    trigger:
      platform: state
      entity_id: select.blue_dream_1_growth_phase
    action:
      service: notify.family
      data:
        title: "🌿 Plant Update"
        message: "Blue Dream 1 entered {{ states('select.blue_dream_1_growth_phase') }} phase!"
```

## 🔧 Advanced Configuration

### Multiple Growboxes

You can track multiple growing environments:

1. **Tent 1** (Vegetative)

   - Blue Dream 1 (Early Veg)
   - White Widow 1 (Mid Late VEG)

2. **Tent 2** (Flowering)
   - Gorilla Glue 1 (Early Flower)
   - OG Kush 1 (Flushing)

### Data Persistence

All data is stored in Home Assistant's configuration:

- **Growth phases**: State history array in config entry options
- **Watering logs**: Persistent watering history array
- **Plant settings**: Strain, planted date, default volumes

### Migration Support

The integration automatically migrates from older phase systems:

- Old 8-phase system → New 6-phase system
- Legacy phase names are automatically converted
- Existing data is preserved and consolidated

## 🚀 Roadmap

- [ ] **Grow Medium Support**: Soil, Hydro, Coco tracking
- [ ] **Nutrient Logging**: EC, pH, fertilizer schedules
- [ ] **Environmental Integration**: Temperature, humidity correlations
- [ ] **Harvest Tracking**: Yield logging and analytics
- [ ] **Photo Timeline**: Image attachments for growth documentation
- [ ] **Strain Database**: Pre-configured strain profiles
- [ ] **Mobile App**: Dedicated companion app

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/moritzheine/growflow-homeassistant/issues)
- **Community**: [Home Assistant Community](https://community.home-assistant.io/)
- **Documentation**: [Wiki](https://github.com/moritzheine/growflow-homeassistant/wiki)

---

**🌱 Happy Growing with Home Assistant! 🏠**

[releases-shield]: https://img.shields.io/github/release/moritzheine/growflow-homeassistant.svg?style=for-the-badge
[releases]: https://github.com/moritzheine/growflow-homeassistant/releases
[commits-shield]: https://img.shields.io/github/commit-activity/y/moritzheine/growflow-homeassistant.svg?style=for-the-badge
[commits]: https://github.com/moritzheine/growflow-homeassistant/commits/main
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/
[license-shield]: https://img.shields.io/github/license/moritzheine/growflow-homeassistant.svg?style=for-the-badge
