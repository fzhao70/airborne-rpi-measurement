#!/bin/bash
# Launcher script for Airborne RPI Measurement Monitor GUI

# Change to the script's directory
cd "$(dirname "$0")"

# Run the monitor GUI
python3 monitor_gui.py
