# Airborne RPI Measurement System

A comprehensive airborne measurement system based on the Raspberry Pi 4 that collects GPS, environmental, and system data with both GUI and command-line interfaces.

## Features

- **Real-time Data Collection**: GPS coordinates, altitude, speed, environmental sensors, and system metrics
- **GUI Monitor Panel**: Modern graphical interface with live data visualization
- **Multiple Interfaces**: Choose between GUI or headless operation with Sense HAT controls
- **Flexible File Saving**: Auto-save or manual save with file browser
- **Multi-threaded**: Parallel data collection from all sensors
- **CSV Logging**: All data saved in standard CSV format for easy analysis

## Hardware Requirements

1. **Raspberry Pi 4**
2. **Sense HAT** - Environmental sensors (temperature, humidity, pressure, orientation, acceleration)
3. **VK-162 GPS Module** - GPS positioning and speed tracking

## Software Installation

### Install Prerequisites

```bash
# Install Sense HAT library
sudo apt-get update
sudo apt-get install sense-hat

# Install GPS library
pip install gps3
```

### Enable GPS Service

Ensure the GPSD service is running:

```bash
sudo systemctl enable gpsd
sudo systemctl start gpsd
```

## Usage

### Option 1: GUI Monitor Panel (Recommended)

The GUI provides a modern interface with real-time data visualization and easy file management.

**Run the monitor:**
```bash
python3 monitor_gui.py
```

Or use the launcher script:
```bash
./run_monitor.sh
```

**GUI Features:**
- **Connection Status**: Visual indicators for GPS, Sense HAT, and system status
- **Real-time Data Display**: Separate tabs for GPS, Sense HAT, System, and combined data
- **Controls**:
  - Start Collection - Begin data logging
  - Pause/Resume - Temporarily pause without losing connection
  - Stop Collection - End session and close files
- **File Management**:
  - Auto-save: Automatically creates timestamped log files
  - Save As: Choose custom filename and location
  - Current file display shows active log file

**Data Tabs:**
1. **GPS Data**: Time, Latitude, Longitude, Altitude, Speed, Climb, Track
2. **Sense HAT Data**: Pressure, Humidity, Temperature, Pitch, Roll, Yaw, Acceleration (X,Y,Z)
3. **System Status**: Core Voltage, CPU Temperature
4. **All Data**: Scrolling log of all collected data points

### Option 2: Headless Operation (Original Mode)

For autonomous operation without a display, use the original command-line interface with Sense HAT joystick controls.

**Run the system:**
```bash
python3 main.py
```

**Controls (Sense HAT Joystick):**
- **Middle Button (Press)**: Start data logging
- **Up Button**: Pause data collection
- **Down Button**: Resume data collection
- **LED Display**: Shows system status messages

## Data Output

Both modes save data to CSV files with the following format:

**Filename**: `logger_YYYY-MM-DD_HH-MM-SS.csv`

**Columns** (18 total):
- `time`, `lat`, `lon`, `alt`, `speed`, `climb`, `track` (GPS)
- `pressure`, `humidity`, `temp`, `pitch`, `roll`, `yaw`, `acc_x`, `acc_y`, `acc_z` (Sense HAT)
- `voltage`, `cpu_temp` (System Status)

## Project Structure

```
airborne-rpi-measurement/
├── main.py              # Original headless mode entry point
├── monitor_gui.py       # GUI monitor panel application
├── run_monitor.sh       # Launcher script for GUI
├── get_gps.py          # GPS data acquisition module
├── get_sense.py        # Sense HAT sensor module
├── get_pistatus.py     # Raspberry Pi system status module
├── get_sensor.py       # Reserved for future expansion
└── README.md           # This file
```

## Troubleshooting

### GPS Not Connecting

1. Check GPS module is properly connected
2. Verify GPSD is running: `sudo systemctl status gpsd`
3. Test GPS: `cgps -s` or `gpsmon`
4. Restart GPSD: `sudo systemctl restart gpsd`

### Sense HAT Not Detected

1. Check Sense HAT is properly seated on GPIO pins
2. Test with: `python3 -c "from sense_hat import SenseHat; s = SenseHat(); s.show_message('Test')"`
3. Ensure sense-hat package is installed: `sudo apt-get install sense-hat`

### GUI Not Starting

1. Ensure X11 is running (GUI mode required)
2. For remote access, enable X11 forwarding: `ssh -X user@raspberry-pi`
3. Check tkinter is installed: `python3 -m tkinter` (should open a test window)

## Development

### Adding New Sensors

1. Create a new module in `get_*.py` format
2. Follow the pattern of existing modules (return dict with data)
3. Add thread in main.py or monitor_gui.py
4. Update CSV header and row construction

### Customizing the GUI

Edit `monitor_gui.py` to:
- Change colors: Modify hex colors in widget creation
- Add graphs: Import matplotlib and add plotting widgets
- Adjust update rate: Change `time.sleep()` values in collection loops

## License

See LICENSE file for details.

## Authors

Developed for airborne data collection and environmental monitoring applications.
