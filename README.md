# 🌱 GrowFlow

**Smart Cannabis Grow Management for Home Assistant**

Track your plants from seed to harvest with automated lifecycle management, environmental monitoring, and data logging.

## ✨ Features

- [x] **Multi-Grow Tracking** - Separate device per plant/grow
- [x] **Lifecycle Management** - Automatic phase tracking & transitions
- [x] **Smart Sensors** - Days since planted, current phase, phase duration
- [x] **Phase Control** - Manual phase selection with validation
- [ ] **Watering Logs** - Track irrigation with amounts & dates
- [ ] **Environmental Control** - Automated climate based on growth phase
- [ ] **Hardware Integration** - Link lights, fans, sensors to grows
- [ ] **Harvest Analytics** - Yield tracking & grow comparisons

## 🚀 Installation

### HACS (Future)

1. Add this repository to HACS
2. Download GrowFlow
3. Restart Home Assistant
4. Add Integration: "GrowFlow"

### Manual Installation

1. Copy `custom_components/growflow/` to `<config>/custom_components/`
2. Restart Home Assistant
3. Configuration > Integrations > Add Integration > "GrowFlow"

## 📱 Usage

### Setting up a Grow

1. **Add Integration** → "GrowFlow"
2. **Name your grow** (e.g. "Purple Haze #1")
3. **Select grow type** (Soil, Hydroponic, Autoflower)
4. **Set planted date**
5. **Done!** Your grow device is created

### Managing Growth Phases

- **Automatic tracking** of days since planted
- **Manual phase control** via dropdown
- **Phase-specific targets** (coming soon)

### Supported Grow Types

- **🌱 Soil/Substrate** - Traditional growing in earth-based medium
- **💧 Hydroponic** - DWC, NFT, and other soilless systems
- **⚡ Autoflower** - Auto-flowering strains with different timing

## 🛠️ Development

### Prerequisites

- Docker & Docker Compose
- VS Code (recommended)

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/moritzheine/growflow-homeassistant
cd growflow-homeassistant

# Start Home Assistant with Docker
docker-compose up -d

# Wait ~30 seconds, then open
open http://localhost:8123

```

## Useful commands

````

# Start development environment
docker-compose up -d

# View logs
docker-compose logs -f homeassistant

# Restart Home Assistant
docker-compose restart homeassistant

# Stop everything
docker-compose down

```
````
