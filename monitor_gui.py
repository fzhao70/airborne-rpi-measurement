#!/usr/bin/env python3
"""
GUI Monitor Panel for Airborne RPI Measurement System
Displays real-time sensor data and provides file saving controls
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import queue
import csv
import time
from datetime import datetime
import os

try:
    from sense_hat import SenseHat
    SENSE_HAT_AVAILABLE = True
except ImportError:
    SENSE_HAT_AVAILABLE = False
    print("Warning: sense_hat module not available")

from get_gps import get_gps, gps_clean
from get_sense import get_sense
from get_pistatus import get_pistatus


class MonitorPanel:
    def __init__(self, root):
        self.root = root
        self.root.title("Airborne RPI Measurement Monitor")
        self.root.geometry("900x700")

        # Data collection state
        self.collecting = False
        self.paused = False
        self.data_queue = queue.Queue()
        self.collection_threads = []

        # File saving
        self.current_log_file = None
        self.csv_writer = None
        self.auto_save = True

        # Sensor connections
        self.gps_connected = False
        self.sense_connected = False
        self.pistatus_connected = False

        # Initialize Sense HAT if available
        self.sense = None
        if SENSE_HAT_AVAILABLE:
            try:
                self.sense = SenseHat()
                self.sense_connected = True
            except Exception as e:
                print(f"Could not initialize Sense HAT: {e}")

        # Create UI
        self.create_widgets()

        # Start UI update loop
        self.update_ui()

    def create_widgets(self):
        """Create all UI widgets"""
        # Title
        title_frame = tk.Frame(self.root, bg="#2c3e50", height=60)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)

        title_label = tk.Label(
            title_frame,
            text="🛩️ Airborne Measurement System Monitor",
            font=("Arial", 18, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title_label.pack(pady=15)

        # Main content frame
        content_frame = tk.Frame(self.root)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left panel - Controls and Status
        left_panel = tk.Frame(content_frame, width=250)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        # Connection Status
        self.create_status_section(left_panel)

        # Control Buttons
        self.create_control_section(left_panel)

        # File Controls
        self.create_file_section(left_panel)

        # Right panel - Data Display
        right_panel = tk.Frame(content_frame)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Data Display Sections
        self.create_data_display(right_panel)

    def create_status_section(self, parent):
        """Create connection status indicators"""
        status_frame = tk.LabelFrame(parent, text="Connection Status", padx=10, pady=10)
        status_frame.pack(fill=tk.X, pady=(0, 10))

        self.gps_status_label = tk.Label(status_frame, text="❌ GPS: Disconnected", anchor="w")
        self.gps_status_label.pack(fill=tk.X, pady=2)

        self.sense_status_label = tk.Label(status_frame, text="❌ Sense HAT: Disconnected", anchor="w")
        self.sense_status_label.pack(fill=tk.X, pady=2)

        self.pistatus_status_label = tk.Label(status_frame, text="❌ System: Disconnected", anchor="w")
        self.pistatus_status_label.pack(fill=tk.X, pady=2)

    def create_control_section(self, parent):
        """Create control buttons"""
        control_frame = tk.LabelFrame(parent, text="Controls", padx=10, pady=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))

        self.start_btn = tk.Button(
            control_frame,
            text="▶️ Start Collection",
            command=self.start_collection,
            bg="#27ae60",
            fg="white",
            font=("Arial", 11, "bold"),
            height=2
        )
        self.start_btn.pack(fill=tk.X, pady=2)

        self.pause_btn = tk.Button(
            control_frame,
            text="⏸️ Pause",
            command=self.toggle_pause,
            bg="#f39c12",
            fg="white",
            font=("Arial", 11, "bold"),
            height=2,
            state=tk.DISABLED
        )
        self.pause_btn.pack(fill=tk.X, pady=2)

        self.stop_btn = tk.Button(
            control_frame,
            text="⏹️ Stop Collection",
            command=self.stop_collection,
            bg="#e74c3c",
            fg="white",
            font=("Arial", 11, "bold"),
            height=2,
            state=tk.DISABLED
        )
        self.stop_btn.pack(fill=tk.X, pady=2)

    def create_file_section(self, parent):
        """Create file saving controls"""
        file_frame = tk.LabelFrame(parent, text="File Management", padx=10, pady=10)
        file_frame.pack(fill=tk.X, pady=(0, 10))

        self.auto_save_var = tk.BooleanVar(value=True)
        auto_save_check = tk.Checkbutton(
            file_frame,
            text="Auto-save on start",
            variable=self.auto_save_var,
            command=self.toggle_auto_save
        )
        auto_save_check.pack(fill=tk.X, pady=2)

        self.save_as_btn = tk.Button(
            file_frame,
            text="💾 Save As...",
            command=self.save_as_dialog,
            height=2
        )
        self.save_as_btn.pack(fill=tk.X, pady=2)

        self.current_file_label = tk.Label(
            file_frame,
            text="No file open",
            wraplength=220,
            justify=tk.LEFT,
            fg="gray"
        )
        self.current_file_label.pack(fill=tk.X, pady=2)

    def create_data_display(self, parent):
        """Create data display sections"""
        # Create notebook for tabs
        notebook = ttk.Notebook(parent)
        notebook.pack(fill=tk.BOTH, expand=True)

        # GPS Tab
        gps_frame = tk.Frame(notebook)
        notebook.add(gps_frame, text="GPS Data")
        self.gps_labels = self.create_data_grid(gps_frame, [
            "Time", "Latitude", "Longitude", "Altitude",
            "Speed", "Climb", "Track"
        ])

        # Sense HAT Tab
        sense_frame = tk.Frame(notebook)
        notebook.add(sense_frame, text="Sense HAT Data")
        self.sense_labels = self.create_data_grid(sense_frame, [
            "Pressure", "Humidity", "Temperature",
            "Pitch", "Roll", "Yaw",
            "Accel X", "Accel Y", "Accel Z"
        ])

        # System Status Tab
        system_frame = tk.Frame(notebook)
        notebook.add(system_frame, text="System Status")
        self.system_labels = self.create_data_grid(system_frame, [
            "Core Voltage", "CPU Temperature"
        ])

        # All Data Tab (Combined)
        all_frame = tk.Frame(notebook)
        notebook.add(all_frame, text="All Data")

        # Create scrollable text widget for all data
        scroll = tk.Scrollbar(all_frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.all_data_text = tk.Text(all_frame, yscrollcommand=scroll.set, height=30)
        self.all_data_text.pack(fill=tk.BOTH, expand=True)
        scroll.config(command=self.all_data_text.yview)

    def create_data_grid(self, parent, labels):
        """Create a grid of labels for data display"""
        data_labels = {}

        for i, label in enumerate(labels):
            # Label name
            tk.Label(
                parent,
                text=f"{label}:",
                font=("Arial", 10, "bold"),
                anchor="w"
            ).grid(row=i, column=0, sticky="w", padx=10, pady=5)

            # Value label
            value_label = tk.Label(
                parent,
                text="--",
                font=("Arial", 10),
                anchor="w",
                fg="#2c3e50"
            )
            value_label.grid(row=i, column=1, sticky="w", padx=10, pady=5)
            data_labels[label] = value_label

        return data_labels

    def toggle_auto_save(self):
        """Toggle auto-save setting"""
        self.auto_save = self.auto_save_var.get()

    def save_as_dialog(self):
        """Open save as dialog"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"logger_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"
        )

        if filename:
            self.open_log_file(filename)

    def open_log_file(self, filename):
        """Open a log file for writing"""
        try:
            # Close existing file if open
            if self.current_log_file:
                self.current_log_file.close()

            # Open new file
            self.current_log_file = open(filename, 'w', newline='')
            self.csv_writer = csv.writer(self.current_log_file)

            # Write header
            header = ['time', 'lat', 'lon', 'alt', 'speed', 'climb', 'track',
                     'pressure', 'humidity', 'temp', 'pitch', 'roll', 'yaw',
                     'acc_x', 'acc_y', 'acc_z', 'voltage', 'cpu_temp']
            self.csv_writer.writerow(header)
            self.current_log_file.flush()

            # Update UI
            self.current_file_label.config(text=f"File: {os.path.basename(filename)}", fg="green")
            print(f"Logging to: {filename}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to open log file: {e}")
            self.current_log_file = None
            self.csv_writer = None

    def start_collection(self):
        """Start data collection"""
        if self.collecting:
            return

        # Auto-save: create log file if enabled
        if self.auto_save and not self.current_log_file:
            filename = f"logger_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"
            self.open_log_file(filename)

        # Check if log file is open
        if not self.current_log_file:
            response = messagebox.askyesno(
                "No File Open",
                "No log file is open. Data will be displayed but not saved. Continue?"
            )
            if not response:
                return

        self.collecting = True
        self.paused = False

        # Update UI
        self.start_btn.config(state=tk.DISABLED)
        self.pause_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.NORMAL)

        # Test connections and start threads
        self.start_collection_threads()

        if self.sense:
            self.sense.show_message("Started", scroll_speed=0.05)

    def stop_collection(self):
        """Stop data collection"""
        if not self.collecting:
            return

        self.collecting = False
        self.paused = False

        # Wait for threads to finish
        for thread in self.collection_threads:
            if thread.is_alive():
                thread.join(timeout=2)

        self.collection_threads.clear()

        # Close log file
        if self.current_log_file:
            self.current_log_file.close()
            self.current_log_file = None
            self.csv_writer = None
            self.current_file_label.config(text="File closed", fg="gray")

        # Update UI
        self.start_btn.config(state=tk.NORMAL)
        self.pause_btn.config(state=tk.DISABLED, text="⏸️ Pause")
        self.stop_btn.config(state=tk.DISABLED)

        # Reset connection status
        self.gps_connected = False
        self.pistatus_connected = False
        self.update_connection_status()

        if self.sense:
            self.sense.show_message("Stopped", scroll_speed=0.05)

    def toggle_pause(self):
        """Toggle pause state"""
        self.paused = not self.paused

        if self.paused:
            self.pause_btn.config(text="▶️ Resume")
            if self.sense:
                self.sense.show_message("Paused", scroll_speed=0.05)
        else:
            self.pause_btn.config(text="⏸️ Pause")
            if self.sense:
                self.sense.show_message("Resumed", scroll_speed=0.05)

    def start_collection_threads(self):
        """Start data collection threads"""
        # GPS thread
        gps_thread = threading.Thread(target=self.gps_collection_loop, daemon=True)
        gps_thread.start()
        self.collection_threads.append(gps_thread)

        # Sense HAT thread
        sense_thread = threading.Thread(target=self.sense_collection_loop, daemon=True)
        sense_thread.start()
        self.collection_threads.append(sense_thread)

        # System status thread
        status_thread = threading.Thread(target=self.status_collection_loop, daemon=True)
        status_thread.start()
        self.collection_threads.append(status_thread)

    def gps_collection_loop(self):
        """GPS data collection thread"""
        try:
            while self.collecting:
                if not self.paused:
                    data = get_gps()
                    if data:
                        self.gps_connected = True
                        self.data_queue.put(('gps', data))
                    else:
                        self.gps_connected = False
                time.sleep(0.5)
        except Exception as e:
            print(f"GPS thread error: {e}")
            self.gps_connected = False
        finally:
            gps_clean()

    def sense_collection_loop(self):
        """Sense HAT data collection thread"""
        try:
            while self.collecting:
                if not self.paused:
                    data = get_sense()
                    if data:
                        self.data_queue.put(('sense', data))
                time.sleep(0.5)
        except Exception as e:
            print(f"Sense HAT thread error: {e}")

    def status_collection_loop(self):
        """System status data collection thread"""
        try:
            while self.collecting:
                if not self.paused:
                    data = get_pistatus()
                    if data:
                        self.pistatus_connected = True
                        self.data_queue.put(('status', data))
                    else:
                        self.pistatus_connected = False
                time.sleep(0.5)
        except Exception as e:
            print(f"Status thread error: {e}")
            self.pistatus_connected = False

    def update_connection_status(self):
        """Update connection status indicators"""
        if self.gps_connected:
            self.gps_status_label.config(text="✅ GPS: Connected", fg="green")
        else:
            self.gps_status_label.config(text="❌ GPS: Disconnected", fg="red")

        if self.sense_connected:
            self.sense_status_label.config(text="✅ Sense HAT: Connected", fg="green")
        else:
            self.sense_status_label.config(text="❌ Sense HAT: Disconnected", fg="red")

        if self.pistatus_connected:
            self.pistatus_status_label.config(text="✅ System: Connected", fg="green")
        else:
            self.pistatus_status_label.config(text="❌ System: Disconnected", fg="red")

    def update_ui(self):
        """Update UI with latest data"""
        # Process all items in queue
        try:
            while True:
                sensor_type, data = self.data_queue.get_nowait()

                if sensor_type == 'gps':
                    self.update_gps_display(data)
                elif sensor_type == 'sense':
                    self.update_sense_display(data)
                elif sensor_type == 'status':
                    self.update_status_display(data)

                # Write to CSV if file is open
                if self.csv_writer and not self.paused:
                    self.write_data_to_csv(sensor_type, data)

        except queue.Empty:
            pass

        # Update connection status
        if self.collecting:
            self.update_connection_status()

        # Schedule next update
        self.root.after(100, self.update_ui)

    def update_gps_display(self, data):
        """Update GPS data display"""
        if not data:
            return

        labels_map = {
            'Time': 'time',
            'Latitude': 'lat',
            'Longitude': 'lon',
            'Altitude': 'alt',
            'Speed': 'speed',
            'Climb': 'climb',
            'Track': 'track'
        }

        for label, key in labels_map.items():
            value = data.get(key, '--')
            if value and value != 'n/a':
                self.gps_labels[label].config(text=str(value))

    def update_sense_display(self, data):
        """Update Sense HAT data display"""
        if not data:
            return

        labels_map = {
            'Pressure': 'pressure',
            'Humidity': 'humidity',
            'Temperature': 'temp',
            'Pitch': 'pitch',
            'Roll': 'roll',
            'Yaw': 'yaw',
            'Accel X': 'acc_x',
            'Accel Y': 'acc_y',
            'Accel Z': 'acc_z'
        }

        for label, key in labels_map.items():
            value = data.get(key, '--')
            if value is not None:
                if isinstance(value, float):
                    self.sense_labels[label].config(text=f"{value:.2f}")
                else:
                    self.sense_labels[label].config(text=str(value))

    def update_status_display(self, data):
        """Update system status display"""
        if not data:
            return

        labels_map = {
            'Core Voltage': 'voltage',
            'CPU Temperature': 'cpu_temp'
        }

        for label, key in labels_map.items():
            value = data.get(key, '--')
            if value is not None:
                self.system_labels[label].config(text=str(value))

    # Store latest data for CSV writing
    latest_gps = {}
    latest_sense = {}
    latest_status = {}

    def write_data_to_csv(self, sensor_type, data):
        """Write collected data to CSV file"""
        # Update latest data
        if sensor_type == 'gps':
            self.latest_gps = data
        elif sensor_type == 'sense':
            self.latest_sense = data
        elif sensor_type == 'status':
            self.latest_status = data

        # Only write when we have all data
        if not (self.latest_gps and self.latest_sense and self.latest_status):
            return

        try:
            # Prepare row data
            row = [
                self.latest_gps.get('time', ''),
                self.latest_gps.get('lat', ''),
                self.latest_gps.get('lon', ''),
                self.latest_gps.get('alt', ''),
                self.latest_gps.get('speed', ''),
                self.latest_gps.get('climb', ''),
                self.latest_gps.get('track', ''),
                self.latest_sense.get('pressure', ''),
                self.latest_sense.get('humidity', ''),
                self.latest_sense.get('temp', ''),
                self.latest_sense.get('pitch', ''),
                self.latest_sense.get('roll', ''),
                self.latest_sense.get('yaw', ''),
                self.latest_sense.get('acc_x', ''),
                self.latest_sense.get('acc_y', ''),
                self.latest_sense.get('acc_z', ''),
                self.latest_status.get('voltage', ''),
                self.latest_status.get('cpu_temp', '')
            ]

            # Write to CSV
            self.csv_writer.writerow(row)
            self.current_log_file.flush()

            # Update all data text display
            data_str = f"[{datetime.now().strftime('%H:%M:%S')}] "
            data_str += f"GPS: {self.latest_gps.get('lat', 'N/A')}, {self.latest_gps.get('lon', 'N/A')} | "
            data_str += f"Temp: {self.latest_sense.get('temp', 'N/A')}°C | "
            data_str += f"Alt: {self.latest_gps.get('alt', 'N/A')}m\n"

            self.all_data_text.insert(tk.END, data_str)
            self.all_data_text.see(tk.END)

            # Limit text widget size
            if int(self.all_data_text.index('end-1c').split('.')[0]) > 1000:
                self.all_data_text.delete('1.0', '100.0')

        except Exception as e:
            print(f"Error writing to CSV: {e}")


def main():
    """Main entry point"""
    root = tk.Tk()
    app = MonitorPanel(root)

    # Handle window close
    def on_closing():
        if app.collecting:
            if messagebox.askokcancel("Quit", "Data collection is active. Stop and quit?"):
                app.stop_collection()
                root.destroy()
        else:
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()