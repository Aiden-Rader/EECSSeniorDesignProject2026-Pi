# EECSSeniorDesignProject2026-Pi

Raspberry Pi flow-monitoring service for the EECS Senior Design project. This project reads a flow sensor and a liquid-level sensor from GPIO pins, calculates water usage in real time, and stores device state plus hydration events in MongoDB.

## What It Does

- Monitors a flow sensor on the configured GPIO pin.
- Uses a capacitive liquid-level sensor on GPIO 4 to detect whether water is present.
- Samples sensor activity every 10 seconds.
- Converts pulses to volume using a calibration factor.
- Writes the latest device state to MongoDB.
- Inserts hydration event records whenever real flow is detected.

## Project Structure

- `flow_metering.py` - Main runtime loop for sensor monitoring and database writes.
- `src/utils.py` - Timezone helpers for Eastern and UTC timestamps.
- `src/models.py` - Document builders for MongoDB records.
- `requirements.txt` - Python package dependencies.

## Requirements

- Raspberry Pi with `gpiozero`-compatible GPIO support.
- MongoDB database and connection string.
- Python 3.x.
- A `.env` file with the required runtime configuration.

## Installation

1. Clone the repository.
2. Create and activate a virtual environment.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root with at least the following values:

```env
MONGO_URI=your_mongodb_connection_string
MONGO_DB_NAME=your_database_name
GPIO_PIN=your_flow_sensor_gpio_pin
CALIBRATION_FACTOR=your_sensor_calibration_value
```

Optional values:

```env
DEVICE_ID=pi-001
DEVICE_NAME=Main Pi
MONGO_DEVICES_COLLECTION=devices
MONGO_DEVICE_STATE_COLLECTION=device_state
MONGO_HYDRATION_EVENT_COLLECTION=hydration_events
```

### Environment Variable Notes

- `GPIO_PIN` is the GPIO pin connected to the flow sensor.
- `CALIBRATION_FACTOR` is used to convert pulse counts into liters.
- `DEVICE_ID` uniquely identifies the Pi in MongoDB.
- `DEVICE_NAME` is the friendly name stored with the device record.

## Running The Monitor

Run the main script directly:

```bash
python flow_metering.py
```

The program will:

1. Connect to MongoDB.
2. Create or update the device record.
3. Start polling the sensors every 10 seconds.
4. Update device state continuously.
5. Insert hydration events whenever flow is detected.

Stop the script with `Ctrl+C`.

## MongoDB Collections

The script uses three collections by default:

- `devices`
- `device_state`
- `hydration_events`

### `devices`

Stores the registered device metadata, including:

- Device ID
- Device name
- Calibration factor
- Status
- `createdAt` / `lastSeenAt`

### `device_state`

Stores the most recent sensor snapshot:

- Current pulse count
- Current flow rate in `mL/s`
- Sensor connectivity flag
- Water presence flag

### `hydration_events`

Stores a new event when the flow sensor detects actual water movement:

- Pulse count
- Volume in milliliters
- Session start and end timestamps
- Duration in seconds

## How Flow Is Calculated

Each 10-second polling window:

```text
liters = pulse_count / calibration_factor
volume_ml = liters * 1000
flow_rate_ml_per_sec = volume_ml / duration_seconds
```

If no pulses are detected, the script still updates `device_state` but does not create a hydration event.

## Troubleshooting

- If the script exits immediately, verify `MONGO_URI`, `MONGO_DB_NAME`, `GPIO_PIN`, and `CALIBRATION_FACTOR` are set in `.env`.
- If GPIO access fails, make sure the script is being run on a Raspberry Pi with the proper hardware and permissions.
- If MongoDB writes fail, confirm the database URI and network access.

## Notes

- The script currently uses a fixed 10-second polling interval.
- Timestamps are stored in US/Eastern time through the shared helper functions.
