# Snapmaker Home Assistant Integration

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)
[![GitHub release](https://img.shields.io/github/v/release/CrunkA3/ha-integration-snapmaker)](https://github.com/CrunkA3/ha-integration-snapmaker/releases)
[![Validate](https://github.com/CrunkA3/ha-integration-snapmaker/actions/workflows/validate.yml/badge.svg)](https://github.com/CrunkA3/ha-integration-snapmaker/actions/workflows/validate.yml)

A [Home Assistant](https://www.home-assistant.io/) custom integration for monitoring [Snapmaker](https://snapmaker.com/) 3D printers.

The integration discovers your Snapmaker printer on the local network via UDP broadcast and polls its API to expose live print status as Home Assistant entities.

![Sensors](https://github.com/CrunkA3/ha-integration-snapmaker/blob/main/assets/screenshots/sensors.png)

---

## Features

### Sensors

| Sensor | Description |
|---|---|
| **State** | Printer status: `OFFLINE`, `IDLE`, `RUNNING`, or `PAUSED` |
| **IP** | Current IP address of the printer |
| **Progress** | Print progress (%) |
| **Elapsed Time** | Time elapsed since the print started (minutes) |
| **Remaining Time** | Estimated time remaining (minutes) |
| **Tool Head** | Active tool head attached to the printer |
| **Nozzle Temperature 1** | Current temperature of nozzle 1 (°C) |
| **Nozzle Temperature 2** | Current temperature of nozzle 2 (°C) |
| **Nozzle Target Temperature 1** | Target temperature of nozzle 1 (°C) |
| **Nozzle Target Temperature 2** | Target temperature of nozzle 2 (°C) |
| **Heated Bed Temperature** | Current heated bed temperature (°C) |
| **Heated Bed Target Temperature** | Target heated bed temperature (°C) |
| **File Name** | Name of the file currently being printed |

### Binary Sensors

| Binary Sensor | Description |
|---|---|
| **Filament Out** | `On` when filament runout is detected |
| **Homed** | `On` when the printer has been homed |

> The **Tool Head**, **temperature sensors**, **File Name**, and the **binary sensors** are only **available** while the printer is actively printing (`RUNNING`).

---

## Requirements

- Home Assistant 2023.1.0 or newer
- Snapmaker printer on the same local network as Home Assistant
- The Snapmaker printer must be reachable via UDP broadcast on port `20054`

---

## Installation

### Via HACS (recommended)

1. Open HACS in Home Assistant.
2. Go to **Integrations** → click the three-dot menu → **Custom repositories**.
3. Add `https://github.com/CrunkA3/ha-integration-snapmaker` as an **Integration**.
4. Search for **Snapmaker** and install it.
5. Restart Home Assistant.

### Manual

1. Copy the `custom_components/snapmaker` directory into your Home Assistant `config/custom_components/` folder.
2. Restart Home Assistant.

---

## Configuration

1. Go to **Settings** → **Devices & Services** → **Add Integration**.
2. Search for **Snapmaker**.
3. Enter the **device name** you want to use to identify your printer in Home Assistant (minimum 3 characters).
4. Click **Submit**.

The integration will begin discovering your printer automatically via UDP broadcast on the local network and poll it every 30 seconds.

---

## How It Works

1. **Discovery** – Every 30 seconds the integration sends a UDP broadcast (`discover`) to port `20054`. The printer responds with its name, IP address, model, and current status.
2. **API polling** – When the printer status is `RUNNING`, the integration connects to the Snapmaker HTTP API (`http://<printer_ip>:8080/api/v1/`) to retrieve detailed print status including temperatures, progress, elapsed/remaining time, and more.
3. **Offline detection** – If the printer does not respond to four consecutive discovery attempts, its status is set to `OFFLINE`.

---

## Issues & Contributions

Please report bugs or feature requests via [GitHub Issues](https://github.com/CrunkA3/ha-integration-snapmaker/issues).
