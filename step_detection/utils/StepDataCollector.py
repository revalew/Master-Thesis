import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import pandas as pd
import requests
import json
import time
import threading
import os
from datetime import datetime

from .step_detection_algorithms import (
    peak_detection_algorithm,
    zero_crossing_algorithm,
    spectral_analysis_algorithm,
    adaptive_threshold_algorithm,
    shoe_algorithm,
    evaluate_algorithm,
    # plot_algorithm_results,
    # compare_algorithms,
    # compare_sensors
)


class StepDataCollector:
    def __init__(self, master, api_url: str = "http://192.168.4.1/api") -> None:
        """
        Constructor for the StepDataCollector class.

        Args:
            master: The root object of the Tkinter application.
            api_url (str): The URL of the API to query for data. Defaults to "http://192.168.4.1/api".
        """
        self.master = master
        self.master.title("Step Data Collector")
        self.master.geometry("1200x800")
        self.master.minsize(1000, 700)

        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.recording = False
        self.api_url = api_url
        self.data = {
            "time": [],
            "sensor1": {
                "accel_x": [],
                "accel_y": [],
                "accel_z": [],
                "gyro_x": [],
                "gyro_y": [],
                "gyro_z": [],
                "mag_x": [],
                "mag_y": [],
                "mag_z": [],
            },
            "sensor2": {
                "accel_x": [],
                "accel_y": [],
                "accel_z": [],
                "gyro_x": [],
                "gyro_y": [],
                "gyro_z": [],
                "mag_x": [],
                "mag_y": [],
                "mag_z": [],
            },
            "battery": {"voltage": [], "current": [], "percentage": []},
        }
        self.ground_truth_steps = []
        self.ground_truth_counting = False

        self.create_widgets()

        self.create_plots()

        self.update_status("Ready. Connect to your Pico device to begin.")


    def on_closing(self):
        """Handle application closing properly"""
        print("Closing application...")

        if self.recording:
            self.recording = False
            print("Stopping recording...")
            # Give the thread time to finish
            if hasattr(self, "recording_thread") and self.recording_thread.is_alive():
                self.recording_thread.join(timeout=2.0)

        plt.close("all")

        self.master.quit()
        self.master.destroy()

        print("Application closed successfully")


    def create_widgets(self):
        # Create main frame with padding
        main_frame = ttk.Frame(self.master, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Top control panel
        control_frame = ttk.LabelFrame(main_frame, text="Control Panel", padding="10")
        control_frame.pack(fill=tk.X, padx=5, pady=5)

        # Connection settings
        connection_frame = ttk.Frame(control_frame)
        connection_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(connection_frame, text="Pico API URL:").grid(
            row=0, column=0, padx=5, pady=5, sticky="w"
        )
        self.url_entry = ttk.Entry(connection_frame, width=30)
        self.url_entry.insert(0, self.api_url)
        self.url_entry.grid(row=0, column=1, padx=5, pady=5)

        self.connect_btn = ttk.Button(
            connection_frame, text="Connect", command=self.check_connection
        )
        self.connect_btn.grid(row=0, column=2, padx=5, pady=5)

        # Recording controls
        record_frame = ttk.Frame(control_frame)
        record_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(record_frame, text="Recording Name:").grid(
            row=0, column=0, padx=5, pady=5, sticky="w"
        )
        self.recording_name = ttk.Entry(record_frame, width=30)
        self.recording_name.insert(
            0, f"recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        self.recording_name.grid(row=0, column=1, padx=5, pady=5)

        buttons_frame = ttk.Frame(record_frame)
        buttons_frame.grid(row=0, column=2, padx=5, pady=5)

        self.record_btn = ttk.Button(
            buttons_frame, text="Start Recording", command=self.toggle_recording
        )
        self.record_btn.pack(side=tk.LEFT, padx=5)

        self.mark_step_btn = ttk.Button(
            buttons_frame, text="Mark Step (Space)", command=self.mark_step
        )
        self.mark_step_btn.pack(side=tk.LEFT, padx=5)
        self.mark_step_btn.config(state=tk.DISABLED)

        self.toggle_count_btn = ttk.Button(
            buttons_frame, text="Start Auto Counting", command=self.toggle_auto_counting
        )
        self.toggle_count_btn.pack(side=tk.LEFT, padx=5)
        self.toggle_count_btn.config(state=tk.DISABLED)

        # File operations
        file_frame = ttk.Frame(control_frame)
        file_frame.pack(fill=tk.X, padx=5, pady=5)

        self.save_btn = ttk.Button(file_frame, text="Save Data", command=self.save_data)
        self.save_btn.pack(side=tk.LEFT, padx=5)

        self.load_btn = ttk.Button(file_frame, text="Load Data", command=self.load_data)
        self.load_btn.pack(side=tk.LEFT, padx=5)

        self.analyze_btn = ttk.Button(
            file_frame, text="Analyze Data", command=self.analyze_data
        )
        self.analyze_btn.pack(side=tk.LEFT, padx=5)
        self.analyze_btn.config(state=tk.DISABLED)

        # Status bar
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=5)

        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_label = ttk.Label(
            status_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W
        )
        status_label.pack(fill=tk.X)

        # Sensor readings
        readings_frame = ttk.LabelFrame(
            main_frame, text="Sensor Readings", padding="10"
        )
        readings_frame.pack(fill=tk.X, padx=5, pady=5)

        # Sensor 1 (Waveshare)
        sensor1_frame = ttk.LabelFrame(
            readings_frame, text="Sensor 1 (Waveshare)", padding="5"
        )
        sensor1_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        ttk.Label(sensor1_frame, text="Accelerometer (m/s²):").grid(
            row=0, column=0, padx=5, pady=2, sticky="w"
        )
        self.accel1_var = tk.StringVar()
        ttk.Label(sensor1_frame, textvariable=self.accel1_var).grid(
            row=0, column=1, padx=5, pady=2, sticky="w"
        )

        ttk.Label(sensor1_frame, text="Gyroscope (rad/s):").grid(
            row=1, column=0, padx=5, pady=2, sticky="w"
        )
        self.gyro1_var = tk.StringVar()
        ttk.Label(sensor1_frame, textvariable=self.gyro1_var).grid(
            row=1, column=1, padx=5, pady=2, sticky="w"
        )

        ttk.Label(sensor1_frame, text="Magnetometer (µT):").grid(
            row=2, column=0, padx=5, pady=2, sticky="w"
        )
        self.mag1_var = tk.StringVar()
        ttk.Label(sensor1_frame, textvariable=self.mag1_var).grid(
            row=2, column=1, padx=5, pady=2, sticky="w"
        )

        # Sensor 2 (Adafruit)
        sensor2_frame = ttk.LabelFrame(
            readings_frame, text="Sensor 2 (Adafruit)", padding="5"
        )
        sensor2_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        ttk.Label(sensor2_frame, text="Accelerometer (m/s²):").grid(
            row=0, column=0, padx=5, pady=2, sticky="w"
        )
        self.accel2_var = tk.StringVar()
        ttk.Label(sensor2_frame, textvariable=self.accel2_var).grid(
            row=0, column=1, padx=5, pady=2, sticky="w"
        )

        ttk.Label(sensor2_frame, text="Gyroscope (rad/s):").grid(
            row=1, column=0, padx=5, pady=2, sticky="w"
        )
        self.gyro2_var = tk.StringVar()
        ttk.Label(sensor2_frame, textvariable=self.gyro2_var).grid(
            row=1, column=1, padx=5, pady=2, sticky="w"
        )

        ttk.Label(sensor2_frame, text="Magnetometer (µT):").grid(
            row=2, column=0, padx=5, pady=2, sticky="w"
        )
        self.mag2_var = tk.StringVar()
        ttk.Label(sensor2_frame, textvariable=self.mag2_var).grid(
            row=2, column=1, padx=5, pady=2, sticky="w"
        )

        # Battery info
        battery_frame = ttk.LabelFrame(readings_frame, text="Battery", padding="5")
        battery_frame.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")

        ttk.Label(battery_frame, text="Voltage (V):").grid(
            row=0, column=0, padx=5, pady=2, sticky="w"
        )
        self.voltage_var = tk.StringVar()
        ttk.Label(battery_frame, textvariable=self.voltage_var).grid(
            row=0, column=1, padx=5, pady=2, sticky="w"
        )

        ttk.Label(battery_frame, text="Current (A):").grid(
            row=1, column=0, padx=5, pady=2, sticky="w"
        )
        self.current_var = tk.StringVar()
        ttk.Label(battery_frame, textvariable=self.current_var).grid(
            row=1, column=1, padx=5, pady=2, sticky="w"
        )

        ttk.Label(battery_frame, text="Battery (%):").grid(
            row=2, column=0, padx=5, pady=2, sticky="w"
        )
        self.battery_var = tk.StringVar()
        ttk.Label(battery_frame, textvariable=self.battery_var).grid(
            row=2, column=1, padx=5, pady=2, sticky="w"
        )

        # Step counter
        counter_frame = ttk.LabelFrame(readings_frame, text="Step Counter", padding="5")
        counter_frame.grid(row=0, column=3, padx=5, pady=5, sticky="nsew")

        ttk.Label(counter_frame, text="Marked Steps:").grid(
            row=0, column=0, padx=5, pady=2, sticky="w"
        )
        self.step_count_var = tk.StringVar()
        self.step_count_var.set("0")
        ttk.Label(
            counter_frame,
            textvariable=self.step_count_var,
            font=("TkDefaultFont", 12, "bold"),
        ).grid(row=0, column=1, padx=5, pady=2, sticky="w")

        ttk.Label(counter_frame, text="Recording Time:").grid(
            row=1, column=0, padx=5, pady=2, sticky="w"
        )
        self.recording_time_var = tk.StringVar()
        self.recording_time_var.set("00:00")
        ttk.Label(counter_frame, textvariable=self.recording_time_var).grid(
            row=1, column=1, padx=5, pady=2, sticky="w"
        )

        # Configure grid weights
        readings_frame.columnconfigure(0, weight=1)
        readings_frame.columnconfigure(1, weight=1)
        readings_frame.columnconfigure(2, weight=1)
        readings_frame.columnconfigure(3, weight=1)
        
        # Bind space key to mark_step
        # self.master.bind("<space>", lambda event: self.mark_step())
        
        # Mouse bindings for convenient step marking and recording control
        # (walking with just the wireless mouse and not the whole PC, so I need a quick access for some actions)
        self.master.bind("<Button-3>", lambda event: self.mark_step())  # Right click -> mark step
        self.master.bind("<Button-2>", lambda event: self.toggle_recording())  # Middle click -> toggle recording
        
        # Mouse wheel bindings - not used as of now, because I'm afraid of the sensitivity
        # self.master.bind("<Button-4>", lambda event: self.mark_step())  # Scroll up -> mark step (Linux)
        # self.master.bind("<Button-5>", lambda event: self.mark_step())  # Scroll down -> mark step (Linux)
        # self.master.bind("<MouseWheel>", lambda event: self.mark_step())  # Scroll wheel (Windows)


    def create_plots(self):
        self.fig, self.axes = plt.subplots(3, 1, figsize=(12, 10), dpi=100)
        self.fig.tight_layout(pad=4.0)

        # Acceleration plot
        self.ax1 = self.axes[0]
        self.ax1.set_title("Accelerometer Data", fontsize=12)
        self.ax1.set_ylabel("Acceleration (m/s²)", fontsize=10)
        self.ax1.grid(True, alpha=0.3)

        # Create empty lines for accelerometer data
        (self.line_ax1,) = self.ax1.plot([], [], "r-", label="X-S1", linewidth=1)
        (self.line_ay1,) = self.ax1.plot([], [], "g-", label="Y-S1", linewidth=1)
        (self.line_az1,) = self.ax1.plot([], [], "b-", label="Z-S1", linewidth=1)

        (self.line_ax2,) = self.ax1.plot([], [], "r--", label="X-S2", linewidth=1)
        (self.line_ay2,) = self.ax1.plot([], [], "g--", label="Y-S2", linewidth=1)
        (self.line_az2,) = self.ax1.plot([], [], "b--", label="Z-S2", linewidth=1)

        self.ax1.legend(loc="upper right", fontsize=8)

        # Gyroscope plot
        self.ax2 = self.axes[1]
        self.ax2.set_title("Gyroscope Data", fontsize=12)
        self.ax2.set_ylabel("Angular Velocity (rad/s)", fontsize=10)
        self.ax2.grid(True, alpha=0.3)

        # Create empty lines for gyroscope data
        (self.line_gx1,) = self.ax2.plot([], [], "r-", label="X-S1", linewidth=1)
        (self.line_gy1,) = self.ax2.plot([], [], "g-", label="Y-S1", linewidth=1)
        (self.line_gz1,) = self.ax2.plot([], [], "b-", label="Z-S1", linewidth=1)

        (self.line_gx2,) = self.ax2.plot([], [], "r--", label="X-S2", linewidth=1)
        (self.line_gy2,) = self.ax2.plot([], [], "g--", label="Y-S2", linewidth=1)
        (self.line_gz2,) = self.ax2.plot([], [], "b--", label="Z-S2", linewidth=1)

        self.ax2.legend(loc="upper right", fontsize=8)

        # Step markers plot
        self.ax3 = self.axes[2]
        self.ax3.set_title("Step Markers", fontsize=12)
        self.ax3.set_xlabel("Time (s)", fontsize=10)
        self.ax3.set_yticks([])
        self.ax3.grid(True, alpha=0.3)

        # Create empty scatter for step markers
        self.step_markers = self.ax3.scatter(
            [], [], marker="o", color="r", s=50, label="Steps"
        )
        self.ax3.legend(loc="upper right", fontsize=8)

        # Create canvas with better frame
        self.canvas_frame = ttk.Frame(self.master)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.canvas_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)


    def check_connection(self):
        """Test connection to the Pico API"""
        self.api_url = self.url_entry.get()
        self.update_status(f"Connecting to {self.api_url}...")

        try:
            response = requests.get(f"{self.api_url}?action=getBatteryInfo", timeout=3)
            if response.status_code == 200:
                data = response.json()
                if "status" in data and data["status"] == "OK":
                    self.update_status(
                        f"Connected successfully! Battery: {data['battery_percentage']:.1f}%"
                    )
                    messagebox.showinfo(
                        "Connection", "Successfully connected to the Pico device!"
                    )
                    # Enable UI elements
                    self.record_btn.config(state=tk.NORMAL)
                    return True

            self.update_status("Connection failed. Invalid response from API.")
            messagebox.showerror(
                "Connection Error",
                "Failed to connect to the Pico device. Invalid response from API.",
            )
            return False

        except requests.exceptions.RequestException as e: # type: ignore
            self.update_status(f"Connection failed: {str(e)}")
            messagebox.showerror(
                "Connection Error", f"Failed to connect to the Pico device:\n{str(e)}"
            )
            return False


    def toggle_recording(self):
        if not self.recording:
            self.recording = True
            self.record_btn.config(text="Stop Recording")
            self.mark_step_btn.config(state=tk.NORMAL)
            self.toggle_count_btn.config(state=tk.NORMAL)

            self.data = {
                "time": [],
                "sensor1": {
                    "accel_x": [],
                    "accel_y": [],
                    "accel_z": [],
                    "gyro_x": [],
                    "gyro_y": [],
                    "gyro_z": [],
                    "mag_x": [],
                    "mag_y": [],
                    "mag_z": [],
                },
                "sensor2": {
                    "accel_x": [],
                    "accel_y": [],
                    "accel_z": [],
                    "gyro_x": [],
                    "gyro_y": [],
                    "gyro_z": [],
                    "mag_x": [],
                    "mag_y": [],
                    "mag_z": [],
                },
                "battery": {"voltage": [], "current": [], "percentage": []},
            }
            self.ground_truth_steps = []
            self.step_count_var.set("0")

            # Reset plots
            self.line_ax1.set_data([], [])
            self.line_ay1.set_data([], [])
            self.line_az1.set_data([], [])
            self.line_ax2.set_data([], [])
            self.line_ay2.set_data([], [])
            self.line_az2.set_data([], [])

            self.line_gx1.set_data([], [])
            self.line_gy1.set_data([], [])
            self.line_gz1.set_data([], [])
            self.line_gx2.set_data([], [])
            self.line_gy2.set_data([], [])
            self.line_gz2.set_data([], [])

            self.step_markers.set_offsets(np.empty((0, 2)))

            self.ax1.relim()
            self.ax1.autoscale_view()
            self.ax2.relim()
            self.ax2.autoscale_view()
            self.ax3.relim()
            self.ax3.autoscale_view()

            self.canvas.draw()

            # Start recording thread
            self.recording_start_time = time.time()
            self.recording_thread = threading.Thread(
                target=self.record_data, daemon=True
            )
            self.recording_thread.start()

            self.update_status("Recording started.")

        else:
            self.recording = False
            self.record_btn.config(text="Start Recording")
            self.mark_step_btn.config(state=tk.DISABLED)
            self.toggle_count_btn.config(state=tk.DISABLED)
            self.ground_truth_counting = False
            self.toggle_count_btn.config(text="Start Auto Counting")

            # Enable analyze button if we have data
            if len(self.data["time"]) > 0:
                self.analyze_btn.config(state=tk.NORMAL)

            self.update_status("Recording stopped.")


    def record_data(self, update_interval: float = 0.1):
        """Background thread to record data from the Pico - FIXED for data synchronization"""
        last_update_time = time.time()

        while self.recording:
            current_time = time.time()
            elapsed_time = current_time - self.recording_start_time

            # Update recording time display
            mins, secs = divmod(int(elapsed_time), 60)
            self.recording_time_var.set(f"{mins:02d}:{secs:02d}")

            # Auto-mark steps if enabled
            if (
                self.ground_truth_counting and current_time - last_update_time >= 1.0
            ):  # Check once per second
                # This simulates a real-time step detection - in reality, you'd integrate with a
                # hardware button or auto-detection system
                if np.random.random() < 0.2:  # 20% chance of a step each second
                    self.mark_step()
                last_update_time = current_time

            try:
                # Initialize data containers for this iteration to ensure synchronization
                data_collected = {
                    "time": elapsed_time,
                    "sensor1": None,
                    "sensor2": None,
                    "battery": None,
                }

                # Get IMU data from sensor 1 (Waveshare)
                try:
                    response1 = requests.get(
                        f"{self.api_url}?action=WavReadIMU", timeout=1
                    )
                    if response1.status_code == 200:
                        data1 = response1.json()
                        if "status" in data1 and data1["status"] == "OK":
                            data_collected["sensor1"] = data1
                            self.accel1_var.set(
                                f"X: {data1['acceleration']['X']:.2f}, Y: {data1['acceleration']['Y']:.2f}, Z: {data1['acceleration']['Z']:.2f}"
                            )
                            self.gyro1_var.set(
                                f"X: {data1['gyro']['X']:.2f}, Y: {data1['gyro']['Y']:.2f}, Z: {data1['gyro']['Z']:.2f}"
                            )
                            self.mag1_var.set(
                                f"X: {data1['magnetic']['X']:.2f}, Y: {data1['magnetic']['Y']:.2f}, Z: {data1['magnetic']['Z']:.2f}"
                            )
                except requests.exceptions.RequestException: # type: ignore
                    pass  # Continue without sensor1 data

                # Get IMU data from sensor 2 (Adafruit)
                try:
                    response2 = requests.get(
                        f"{self.api_url}?action=AdaReadIMU", timeout=1
                    )
                    if response2.status_code == 200:
                        data2 = response2.json()
                        if "status" in data2 and data2["status"] == "OK":
                            data_collected["sensor2"] = data2
                            self.accel2_var.set(
                                f"X: {data2['acceleration']['X']:.2f}, Y: {data2['acceleration']['Y']:.2f}, Z: {data2['acceleration']['Z']:.2f}"
                            )
                            self.gyro2_var.set(
                                f"X: {data2['gyro']['X']:.2f}, Y: {data2['gyro']['Y']:.2f}, Z: {data2['gyro']['Z']:.2f}"
                            )
                            self.mag2_var.set(
                                f"X: {data2['magnetic']['X']:.2f}, Y: {data2['magnetic']['Y']:.2f}, Z: {data2['magnetic']['Z']:.2f}"
                            )
                except requests.exceptions.RequestException: # type: ignore
                    pass  # Continue without sensor2 data

                # Get battery info
                try:
                    response_batt = requests.get(
                        f"{self.api_url}?action=getBatteryInfo", timeout=1
                    )
                    if response_batt.status_code == 200:
                        data_batt = response_batt.json()
                        if "status" in data_batt and data_batt["status"] == "OK":
                            data_collected["battery"] = data_batt
                            self.voltage_var.set(
                                f"{data_batt['battery_voltage']:.2f} V"
                            )
                            self.current_var.set(
                                f"{data_batt['battery_current']:.3f} A"
                            )
                            self.battery_var.set(
                                f"{data_batt['battery_percentage']:.1f}%"
                            )
                except requests.exceptions.RequestException: # type: ignore
                    pass  # Continue without battery data

                # Only add data if we have at least one sensor reading
                if (
                    data_collected["sensor1"] is not None
                    or data_collected["sensor2"] is not None
                ):
                    self.data["time"].append(elapsed_time)

                    if data_collected["sensor1"] is not None:
                        data1 = data_collected["sensor1"]
                        self.data["sensor1"]["accel_x"].append(
                            data1["acceleration"]["X"]
                        )
                        self.data["sensor1"]["accel_y"].append(
                            data1["acceleration"]["Y"]
                        )
                        self.data["sensor1"]["accel_z"].append(
                            data1["acceleration"]["Z"]
                        )
                        self.data["sensor1"]["gyro_x"].append(data1["gyro"]["X"])
                        self.data["sensor1"]["gyro_y"].append(data1["gyro"]["Y"])
                        self.data["sensor1"]["gyro_z"].append(data1["gyro"]["Z"])
                        self.data["sensor1"]["mag_x"].append(data1["magnetic"]["X"])
                        self.data["sensor1"]["mag_y"].append(data1["magnetic"]["Y"])
                        self.data["sensor1"]["mag_z"].append(data1["magnetic"]["Z"])
                    else:
                        self.data["sensor1"]["accel_x"].append(0.0)
                        self.data["sensor1"]["accel_y"].append(0.0)
                        self.data["sensor1"]["accel_z"].append(0.0)
                        self.data["sensor1"]["gyro_x"].append(0.0)
                        self.data["sensor1"]["gyro_y"].append(0.0)
                        self.data["sensor1"]["gyro_z"].append(0.0)
                        self.data["sensor1"]["mag_x"].append(0.0)
                        self.data["sensor1"]["mag_y"].append(0.0)
                        self.data["sensor1"]["mag_z"].append(0.0)

                    if data_collected["sensor2"] is not None:
                        data2 = data_collected["sensor2"]
                        self.data["sensor2"]["accel_x"].append(
                            data2["acceleration"]["X"]
                        )
                        self.data["sensor2"]["accel_y"].append(
                            data2["acceleration"]["Y"]
                        )
                        self.data["sensor2"]["accel_z"].append(
                            data2["acceleration"]["Z"]
                        )
                        self.data["sensor2"]["gyro_x"].append(data2["gyro"]["X"])
                        self.data["sensor2"]["gyro_y"].append(data2["gyro"]["Y"])
                        self.data["sensor2"]["gyro_z"].append(data2["gyro"]["Z"])
                        self.data["sensor2"]["mag_x"].append(data2["magnetic"]["X"])
                        self.data["sensor2"]["mag_y"].append(data2["magnetic"]["Y"])
                        self.data["sensor2"]["mag_z"].append(data2["magnetic"]["Z"])
                    else:
                        self.data["sensor2"]["accel_x"].append(0.0)
                        self.data["sensor2"]["accel_y"].append(0.0)
                        self.data["sensor2"]["accel_z"].append(0.0)
                        self.data["sensor2"]["gyro_x"].append(0.0)
                        self.data["sensor2"]["gyro_y"].append(0.0)
                        self.data["sensor2"]["gyro_z"].append(0.0)
                        self.data["sensor2"]["mag_x"].append(0.0)
                        self.data["sensor2"]["mag_y"].append(0.0)
                        self.data["sensor2"]["mag_z"].append(0.0)

                    if data_collected["battery"] is not None:
                        data_batt = data_collected["battery"]
                        self.data["battery"]["voltage"].append(
                            data_batt["battery_voltage"]
                        )
                        self.data["battery"]["current"].append(
                            data_batt["battery_current"]
                        )
                        self.data["battery"]["percentage"].append(
                            data_batt["battery_percentage"]
                        )
                    else:
                        self.data["battery"]["voltage"].append(0.0)
                        self.data["battery"]["current"].append(0.0)
                        self.data["battery"]["percentage"].append(0.0)

                    # Update plots (not too frequently to avoid GUI lag)
                    if len(self.data["time"]) % 5 == 0:
                        self.update_plots()

            except requests.exceptions.RequestException as e: # type: ignore
                self.update_status(f"Error reading data: {str(e)}")

            # Sleep to maintain update rate
            time.sleep(update_interval)


    def update_plots(self):
        """Update the data plots - FIXED for array length validation"""
        if len(self.data["time"]) == 0:
            return

        try:
            # Validate data lengths before plotting to prevent broadcast errors
            time_len = len(self.data["time"])
            for sensor in ["sensor1", "sensor2"]:
                for key in self.data[sensor]:
                    if len(self.data[sensor][key]) != time_len:
                        print(
                            f"Warning: {sensor}.{key} length {len(self.data[sensor][key])} != time length {time_len}"
                        )
                        return  # Skip update if data is inconsistent

            times = np.array(self.data["time"])

            min_len = min(
                len(times),
                len(self.data["sensor1"]["accel_x"]),
                len(self.data["sensor2"]["accel_x"]),
            )

            if min_len == 0:
                return

            # Truncate all arrays to the minimum length to ensure consistency
            times = times[:min_len]

            # 
            self.line_ax1.set_data(
                times, np.array(self.data["sensor1"]["accel_x"])[:min_len]
            )
            self.line_ay1.set_data(
                times, np.array(self.data["sensor1"]["accel_y"])[:min_len]
            )
            self.line_az1.set_data(
                times, np.array(self.data["sensor1"]["accel_z"])[:min_len]
            )

            self.line_ax2.set_data(
                times, np.array(self.data["sensor2"]["accel_x"])[:min_len]
            )
            self.line_ay2.set_data(
                times, np.array(self.data["sensor2"]["accel_y"])[:min_len]
            )
            self.line_az2.set_data(
                times, np.array(self.data["sensor2"]["accel_z"])[:min_len]
            )

            # 
            self.line_gx1.set_data(
                times, np.array(self.data["sensor1"]["gyro_x"])[:min_len]
            )
            self.line_gy1.set_data(
                times, np.array(self.data["sensor1"]["gyro_y"])[:min_len]
            )
            self.line_gz1.set_data(
                times, np.array(self.data["sensor1"]["gyro_z"])[:min_len]
            )

            self.line_gx2.set_data(
                times, np.array(self.data["sensor2"]["gyro_x"])[:min_len]
            )
            self.line_gy2.set_data(
                times, np.array(self.data["sensor2"]["gyro_y"])[:min_len]
            )
            self.line_gz2.set_data(
                times, np.array(self.data["sensor2"]["gyro_z"])[:min_len]
            )

            if len(self.ground_truth_steps) > 0:
                # Only include steps that are within the current time range
                step_times = [t for t in self.ground_truth_steps if t <= times[-1]]
                if len(step_times) > 0:
                    step_points = np.column_stack(
                        (step_times, np.ones(len(step_times)) * 0.5)
                    )
                    self.step_markers.set_offsets(step_points)
                else:
                    self.step_markers.set_offsets(np.empty((0, 2)))
            else:
                self.step_markers.set_offsets(np.empty((0, 2)))

            # Update axis limits
            if len(times) > 0:
                self.ax1.relim()
                self.ax1.autoscale_view()
                self.ax2.relim()
                self.ax2.autoscale_view()

                self.ax3.set_xlim(times[0], times[-1])
                self.ax3.set_ylim(0, 1)

            self.canvas.draw_idle()

        # Don't crash the application, just skip this update
        except Exception as e:
            print(f"Error updating plots: {e}")


    def mark_step(self):
        """Mark a step in the data"""
        if self.recording:
            current_time = time.time()
            elapsed_time = current_time - self.recording_start_time

            self.ground_truth_steps.append(elapsed_time)
            self.step_count_var.set(str(len(self.ground_truth_steps)))

            self.update_status(f"Step marked at {elapsed_time:.2f} seconds.")

            try:
                self.update_plots()
            except Exception as e:
                print(f"Error updating plots after step mark: {e}")


    def toggle_auto_counting(self):
        """Toggle automatic step counting"""
        if not self.ground_truth_counting:
            self.ground_truth_counting = True
            self.toggle_count_btn.config(text="Stop Auto Counting")
            self.update_status("Automatic step counting enabled.")
        else:
            self.ground_truth_counting = False
            self.toggle_count_btn.config(text="Start Auto Counting")
            self.update_status("Automatic step counting disabled.")


    def save_data(self):
        """Save the recorded data to CSV files"""
        if len(self.data["time"]) == 0:
            messagebox.showwarning(
                "No Data", "No data to save. Record some data first."
            )
            return

        save_dir = filedialog.askdirectory(title="Select Directory to Save Data")
        if not save_dir:
            return

        recording_name = self.recording_name.get()
        if not recording_name:
            recording_name = f"recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        recording_dir = os.path.join(save_dir, recording_name) # type: ignore
        if not os.path.exists(recording_dir): # type: ignore
            os.makedirs(recording_dir)

        sensor1_df = pd.DataFrame(
            {
                "time": self.data["time"],
                "accel_x": self.data["sensor1"]["accel_x"],
                "accel_y": self.data["sensor1"]["accel_y"],
                "accel_z": self.data["sensor1"]["accel_z"],
                "gyro_x": self.data["sensor1"]["gyro_x"],
                "gyro_y": self.data["sensor1"]["gyro_y"],
                "gyro_z": self.data["sensor1"]["gyro_z"],
                "mag_x": self.data["sensor1"]["mag_x"],
                "mag_y": self.data["sensor1"]["mag_y"],
                "mag_z": self.data["sensor1"]["mag_z"],
            }
        )
        sensor1_df.to_csv(
            os.path.join(recording_dir, "sensor1_waveshare.csv"), index=False # type: ignore
        )

        sensor2_df = pd.DataFrame(
            {
                "time": self.data["time"],
                "accel_x": self.data["sensor2"]["accel_x"],
                "accel_y": self.data["sensor2"]["accel_y"],
                "accel_z": self.data["sensor2"]["accel_z"],
                "gyro_x": self.data["sensor2"]["gyro_x"],
                "gyro_y": self.data["sensor2"]["gyro_y"],
                "gyro_z": self.data["sensor2"]["gyro_z"],
                "mag_x": self.data["sensor2"]["mag_x"],
                "mag_y": self.data["sensor2"]["mag_y"],
                "mag_z": self.data["sensor2"]["mag_z"],
            }
        )
        sensor2_df.to_csv(
            os.path.join(recording_dir, "sensor2_adafruit.csv"), index=False # type: ignore
        )

        battery_df = pd.DataFrame(
            {
                "time": self.data["time"],
                "voltage": self.data["battery"]["voltage"],
                "current": self.data["battery"]["current"],
                "percentage": self.data["battery"]["percentage"],
            }
        )
        battery_df.to_csv(os.path.join(recording_dir, "battery.csv"), index=False) # type: ignore

        ground_truth_df = pd.DataFrame({"step_times": self.ground_truth_steps})
        ground_truth_df.to_csv(
            os.path.join(recording_dir, "ground_truth.csv"), index=False # type: ignore
        )

        metadata = {
            "recording_name": recording_name,
            "recording_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_duration": (
                self.data["time"][-1] if len(self.data["time"]) > 0 else 0
            ),
            "step_count": len(self.ground_truth_steps),
            "sampling_frequency": (
                len(self.data["time"]) / self.data["time"][-1]
                if len(self.data["time"]) > 0
                else 0
            ),
        }

        with open(os.path.join(recording_dir, "metadata.json"), "w") as f: # type: ignore
            json.dump(metadata, f, indent=4) # type: ignore

        self.update_status(f"Data saved to {recording_dir}")
        messagebox.showinfo("Data Saved", f"Recording data saved to {recording_dir}")


    def load_data(self):
        """Load previously recorded data"""
        load_dir = filedialog.askdirectory(title="Select Recording Directory to Load")
        if not load_dir:
            return

        try:
            required_files = [
                "sensor1_waveshare.csv",
                "sensor2_adafruit.csv",
                "ground_truth.csv",
            ]
            for file in required_files:
                if not os.path.exists(os.path.join(load_dir, file)): # type: ignore
                    messagebox.showerror(
                        "Missing File",
                        f"Required file {file} not found in the selected directory.",
                    )
                    return

            sensor1_df = pd.read_csv(os.path.join(load_dir, "sensor1_waveshare.csv")) # type: ignore

            sensor2_df = pd.read_csv(os.path.join(load_dir, "sensor2_adafruit.csv")) # type: ignore

            ground_truth_df = pd.read_csv(os.path.join(load_dir, "ground_truth.csv")) # type: ignore

            battery_df = None
            if os.path.exists(os.path.join(load_dir, "battery.csv")): # type: ignore
                battery_df = pd.read_csv(os.path.join(load_dir, "battery.csv")) # type: ignore

            # Reset data structures
            self.data = {
                "time": sensor1_df["time"].tolist(),
                "sensor1": {
                    "accel_x": sensor1_df["accel_x"].tolist(),
                    "accel_y": sensor1_df["accel_y"].tolist(),
                    "accel_z": sensor1_df["accel_z"].tolist(),
                    "gyro_x": sensor1_df["gyro_x"].tolist(),
                    "gyro_y": sensor1_df["gyro_y"].tolist(),
                    "gyro_z": sensor1_df["gyro_z"].tolist(),
                    "mag_x": sensor1_df["mag_x"].tolist(),
                    "mag_y": sensor1_df["mag_y"].tolist(),
                    "mag_z": sensor1_df["mag_z"].tolist(),
                },
                "sensor2": {
                    "accel_x": sensor2_df["accel_x"].tolist(),
                    "accel_y": sensor2_df["accel_y"].tolist(),
                    "accel_z": sensor2_df["accel_z"].tolist(),
                    "gyro_x": sensor2_df["gyro_x"].tolist(),
                    "gyro_y": sensor2_df["gyro_y"].tolist(),
                    "gyro_z": sensor2_df["gyro_z"].tolist(),
                    "mag_x": sensor2_df["mag_x"].tolist(),
                    "mag_y": sensor2_df["mag_y"].tolist(),
                    "mag_z": sensor2_df["mag_z"].tolist(),
                },
                "battery": {
                    "voltage": (
                        battery_df["voltage"].tolist() if battery_df is not None else []
                    ),
                    "current": (
                        battery_df["current"].tolist() if battery_df is not None else []
                    ),
                    "percentage": (
                        battery_df["percentage"].tolist()
                        if battery_df is not None
                        else []
                    ),
                },
            }
            self.ground_truth_steps = ground_truth_df["step_times"].tolist()

            self.step_count_var.set(str(len(self.ground_truth_steps)))

            if len(self.data["time"]) > 0:
                duration = self.data["time"][-1]
                mins, secs = divmod(int(duration), 60)
                self.recording_time_var.set(f"{mins:02d}:{secs:02d}")

                self.analyze_btn.config(state=tk.NORMAL)

                self.update_plots()

            recording_name = os.path.basename(load_dir) # type: ignore
            self.recording_name.delete(0, tk.END)
            self.recording_name.insert(0, recording_name)

            self.update_status(f"Data loaded from {load_dir}")
            messagebox.showinfo("Data Loaded", f"Recording data loaded from {load_dir}")

        except Exception as e:
            self.update_status(f"Error loading data: {str(e)}")
            messagebox.showerror("Load Error", f"Failed to load data:\n{str(e)}")


    def analyze_data(self):
        """Analyze the recorded data with step detection algorithms"""
        if len(self.data["time"]) == 0 or len(self.ground_truth_steps) == 0:
            messagebox.showwarning(
                "No Data", "Not enough data to analyze. Record data with steps first."
            )
            return
        
        # Define parameter sets
        param_sets = {
            "peak_detection": {
                "window_size": 1.0,
                "threshold": 1.0,
                "min_time_between_steps": 0.3,
            },
            "zero_crossing": {"window_size": 1.0, "min_time_between_steps": 0.3},
            "spectral_analysis": {
                "window_size": 5.0,
                "overlap": 0.5,
                "step_freq_range": (1.0, 2.5),
            },
            "adaptive_threshold": {
                "window_size": 1.0,
                "sensitivity": 0.6,
                "min_time_between_steps": 0.3,
            },
            "shoe": {
                "window_size": 1.0,
                "threshold": 0.8,
                "min_time_between_steps": 0.3,
            },
        }

        # Create dataset in the format expected by the algorithms
        dataset = {
            "time": np.array(self.data["time"]),
            "sensor1": {
                "accel_x": np.array(self.data["sensor1"]["accel_x"]),
                "accel_y": np.array(self.data["sensor1"]["accel_y"]),
                "accel_z": np.array(self.data["sensor1"]["accel_z"]),
                "gyro_x": np.array(self.data["sensor1"]["gyro_x"]),
                "gyro_y": np.array(self.data["sensor1"]["gyro_y"]),
                "gyro_z": np.array(self.data["sensor1"]["gyro_z"]),
                "mag_x": np.array(self.data["sensor1"]["mag_x"]),
                "mag_y": np.array(self.data["sensor1"]["mag_y"]),
                "mag_z": np.array(self.data["sensor1"]["mag_z"]),
            },
            "sensor2": {
                "accel_x": np.array(self.data["sensor2"]["accel_x"]),
                "accel_y": np.array(self.data["sensor2"]["accel_y"]),
                "accel_z": np.array(self.data["sensor2"]["accel_z"]),
                "gyro_x": np.array(self.data["sensor2"]["gyro_x"]),
                "gyro_y": np.array(self.data["sensor2"]["gyro_y"]),
                "gyro_z": np.array(self.data["sensor2"]["gyro_z"]),
                "mag_x": np.array(self.data["sensor2"]["mag_x"]),
                "mag_y": np.array(self.data["sensor2"]["mag_y"]),
                "mag_z": np.array(self.data["sensor2"]["mag_z"]),
            },
            "ground_truth": {
                "step_times": np.array(self.ground_truth_steps),
                "step_count": len(self.ground_truth_steps),
            },
            "params": {
                "fs": (
                    len(self.data["time"]) / self.data["time"][-1]
                    if len(self.data["time"]) > 0
                    else 0
                )
            },
        }

        self.update_status("Running step detection algorithms...")

        analysis_window = tk.Toplevel(self.master)
        analysis_window.title("Step Detection Analysis")
        analysis_window.geometry("1000x800")

        # Create notebook for tabbed interface
        notebook = ttk.Notebook(analysis_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        results = {"sensor1": {}, "sensor2": {}}

        # Process sensor 1
        accel_data1 = [
            dataset["sensor1"]["accel_x"],
            dataset["sensor1"]["accel_y"],
            dataset["sensor1"]["accel_z"],
        ]
        gyro_data1 = [
            dataset["sensor1"]["gyro_x"],
            dataset["sensor1"]["gyro_y"],
            dataset["sensor1"]["gyro_z"],
        ]

        # Process sensor 2
        accel_data2 = [
            dataset["sensor2"]["accel_x"],
            dataset["sensor2"]["accel_y"],
            dataset["sensor2"]["accel_z"],
        ]
        gyro_data2 = [
            dataset["sensor2"]["gyro_x"],
            dataset["sensor2"]["gyro_y"],
            dataset["sensor2"]["gyro_z"],
        ]

        fs = dataset["params"]["fs"]
        ground_truth_steps = dataset["ground_truth"]["step_times"]

        for algorithm_name, params in param_sets.items():
            self.update_status(f"Running {algorithm_name}...")

            try:
                # Sensor 1
                if algorithm_name == "peak_detection":
                    start_time = time.time()
                    detected_steps1, filtered_signal1 = peak_detection_algorithm(
                        accel_data1,
                        fs,
                        params["window_size"],
                        params["threshold"],
                        params["min_time_between_steps"],
                    )
                    execution_time1 = time.time() - start_time
                    results["sensor1"][algorithm_name] = {
                        "detected_steps": detected_steps1,
                        "filtered_signal": filtered_signal1,
                        "metrics": evaluate_algorithm(
                            detected_steps1, ground_truth_steps
                        ),
                        "execution_time": execution_time1,
                    }

                elif algorithm_name == "zero_crossing":
                    start_time = time.time()
                    detected_steps1, filtered_signal1 = zero_crossing_algorithm(
                        accel_data1,
                        fs,
                        params["window_size"],
                        params["min_time_between_steps"],
                    )
                    execution_time1 = time.time() - start_time
                    results["sensor1"][algorithm_name] = {
                        "detected_steps": detected_steps1,
                        "filtered_signal": filtered_signal1,
                        "metrics": evaluate_algorithm(
                            detected_steps1, ground_truth_steps
                        ),
                        "execution_time": execution_time1,
                    }

                elif algorithm_name == "spectral_analysis":
                    start_time = time.time()
                    detected_steps1, step_freqs1 = spectral_analysis_algorithm(
                        accel_data1,
                        fs,
                        params["window_size"],
                        params["overlap"],
                        params["step_freq_range"],
                    )
                    execution_time1 = time.time() - start_time
                    results["sensor1"][algorithm_name] = {
                        "detected_steps": detected_steps1,
                        "step_frequencies": step_freqs1,
                        "metrics": evaluate_algorithm(
                            detected_steps1, ground_truth_steps
                        ),
                        "execution_time": execution_time1,
                    }

                elif algorithm_name == "adaptive_threshold":
                    start_time = time.time()
                    detected_steps1, filtered_signal1, threshold1 = (
                        adaptive_threshold_algorithm(
                            accel_data1,
                            fs,
                            params["window_size"],
                            params["sensitivity"],
                            params["min_time_between_steps"],
                        )
                    )
                    execution_time1 = time.time() - start_time
                    results["sensor1"][algorithm_name] = {
                        "detected_steps": detected_steps1,
                        "filtered_signal": filtered_signal1,
                        "threshold": threshold1,
                        "metrics": evaluate_algorithm(
                            detected_steps1, ground_truth_steps
                        ),
                        "execution_time": execution_time1,
                    }

                elif algorithm_name == "shoe":
                    start_time = time.time()
                    detected_steps1, combined_signal1 = shoe_algorithm(
                        accel_data1,
                        gyro_data1,
                        fs,
                        params["window_size"],
                        params["threshold"],
                        params["min_time_between_steps"],
                    )
                    execution_time1 = time.time() - start_time
                    results["sensor1"][algorithm_name] = {
                        "detected_steps": detected_steps1,
                        "combined_signal": combined_signal1,
                        "metrics": evaluate_algorithm(
                            detected_steps1, ground_truth_steps
                        ),
                        "execution_time": execution_time1,
                    }

                # Sensor 2
                if algorithm_name == "peak_detection":
                    start_time = time.time()
                    detected_steps2, filtered_signal2 = peak_detection_algorithm(
                        accel_data2,
                        fs,
                        params["window_size"],
                        params["threshold"],
                        params["min_time_between_steps"],
                    )
                    execution_time2 = time.time() - start_time
                    results["sensor2"][algorithm_name] = {
                        "detected_steps": detected_steps2,
                        "filtered_signal": filtered_signal2,
                        "metrics": evaluate_algorithm(
                            detected_steps2, ground_truth_steps
                        ),
                        "execution_time": execution_time2,
                    }

                elif algorithm_name == "zero_crossing":
                    start_time = time.time()
                    detected_steps2, filtered_signal2 = zero_crossing_algorithm(
                        accel_data2,
                        fs,
                        params["window_size"],
                        params["min_time_between_steps"],
                    )
                    execution_time2 = time.time() - start_time
                    results["sensor2"][algorithm_name] = {
                        "detected_steps": detected_steps2,
                        "filtered_signal": filtered_signal2,
                        "metrics": evaluate_algorithm(
                            detected_steps2, ground_truth_steps
                        ),
                        "execution_time": execution_time2,
                    }

                elif algorithm_name == "spectral_analysis":
                    start_time = time.time()
                    detected_steps2, step_freqs2 = spectral_analysis_algorithm(
                        accel_data2,
                        fs,
                        params["window_size"],
                        params["overlap"],
                        params["step_freq_range"],
                    )
                    execution_time2 = time.time() - start_time
                    results["sensor2"][algorithm_name] = {
                        "detected_steps": detected_steps2,
                        "step_frequencies": step_freqs2,
                        "metrics": evaluate_algorithm(
                            detected_steps2, ground_truth_steps
                        ),
                        "execution_time": execution_time2,
                    }

                elif algorithm_name == "adaptive_threshold":
                    start_time = time.time()
                    detected_steps2, filtered_signal2, threshold2 = (
                        adaptive_threshold_algorithm(
                            accel_data2,
                            fs,
                            params["window_size"],
                            params["sensitivity"],
                            params["min_time_between_steps"],
                        )
                    )
                    execution_time2 = time.time() - start_time
                    results["sensor2"][algorithm_name] = {
                        "detected_steps": detected_steps2,
                        "filtered_signal": filtered_signal2,
                        "threshold": threshold2,
                        "metrics": evaluate_algorithm(
                            detected_steps2, ground_truth_steps
                        ),
                        "execution_time": execution_time2,
                    }

                elif algorithm_name == "shoe":
                    start_time = time.time()
                    detected_steps2, combined_signal2 = shoe_algorithm(
                        accel_data2,
                        gyro_data2,
                        fs,
                        params["window_size"],
                        params["threshold"],
                        params["min_time_between_steps"],
                    )
                    execution_time2 = time.time() - start_time
                    results["sensor2"][algorithm_name] = {
                        "detected_steps": detected_steps2,
                        "combined_signal": combined_signal2,
                        "metrics": evaluate_algorithm(
                            detected_steps2, ground_truth_steps
                        ),
                        "execution_time": execution_time2,
                    }

            except Exception as e:
                print(f"Error running {algorithm_name}: {e}")
                # Create dummy results if algorithm fails
                results["sensor1"][algorithm_name] = {
                    "detected_steps": np.array([]),
                    "metrics": {
                        "precision": 0,
                        "recall": 0,
                        "f1_score": 0,
                        "step_count": 0,
                        "ground_truth_count": len(ground_truth_steps),
                        "step_count_error": len(ground_truth_steps),
                        "step_count_error_percent": 100.0,
                        "mse": float("inf"),
                    },
                    "execution_time": 0.0,
                }
                results["sensor2"][algorithm_name] = {
                    "detected_steps": np.array([]),
                    "metrics": {
                        "precision": 0,
                        "recall": 0,
                        "f1_score": 0,
                        "step_count": 0,
                        "ground_truth_count": len(ground_truth_steps),
                        "step_count_error": len(ground_truth_steps),
                        "step_count_error_percent": 100.0,
                        "mse": float("inf"),
                    },
                    "execution_time": 0.0,
                }

        # Create tabs for each algorithm
        for algorithm_name in param_sets.keys():
            tab = ttk.Frame(notebook)
            notebook.add(tab, text=algorithm_name.replace("_", " ").title())

            # Create figure for this algorithm
            fig = plt.figure(figsize=(10, 8))

            # Plot sensor 1 results
            ax1 = fig.add_subplot(2, 1, 1)
            metrics1 = results["sensor1"][algorithm_name]["metrics"]
            ax1.set_title(
                f"Sensor 1 (Waveshare) - {algorithm_name} - F1: {metrics1['f1_score']:.2f}, Error: {metrics1['step_count_error']}"
            )

            # Plot ground truth and detected steps
            ax1.vlines(ground_truth_steps, 0, 0.8, color="g", label="Ground Truth")
            ax1.vlines(
                results["sensor1"][algorithm_name]["detected_steps"],
                0.2,
                1.0,
                color="r",
                label="Detected",
            )
            ax1.set_yticks([])
            ax1.set_xlim(0, dataset["time"][-1])
            ax1.set_ylim(0, 1)
            ax1.legend()
            ax1.grid(True, alpha=0.3)

            # Plot sensor 2 results
            ax2 = fig.add_subplot(2, 1, 2)
            metrics2 = results["sensor2"][algorithm_name]["metrics"]
            ax2.set_title(
                f"Sensor 2 (Adafruit) - {algorithm_name} - F1: {metrics2['f1_score']:.2f}, Error: {metrics2['step_count_error']}"
            )

            # Plot ground truth and detected steps
            ax2.vlines(ground_truth_steps, 0, 0.8, color="g", label="Ground Truth")
            ax2.vlines(
                results["sensor2"][algorithm_name]["detected_steps"],
                0.2,
                1.0,
                color="r",
                label="Detected",
            )
            ax2.set_yticks([])
            ax2.set_xlim(0, dataset["time"][-1])
            ax2.set_ylim(0, 1)
            ax2.set_xlabel("Time (s)")
            ax2.legend()
            ax2.grid(True, alpha=0.3)

            fig.tight_layout()

            # Create metrics panel
            metrics_frame = ttk.LabelFrame(tab, text="Metrics", padding="2")
            metrics_frame.pack(fill=tk.X, padx=5, pady=2)

            # Sensor 1 metrics
            s1_frame = ttk.LabelFrame(
                metrics_frame, text="Sensor 1 (Waveshare)", padding="2"
            )
            s1_frame.grid(row=0, column=0, padx=5, pady=2, sticky="nsew")

            ttk.Label(s1_frame, text="Precision:").grid(
                row=0, column=0, padx=5, pady=2, sticky="w"
            )
            ttk.Label(s1_frame, text=f"{metrics1['precision']:.4f}").grid(
                row=0, column=1, padx=5, pady=2, sticky="w"
            )

            ttk.Label(s1_frame, text="Recall:").grid(
                row=1, column=0, padx=5, pady=2, sticky="w"
            )
            ttk.Label(s1_frame, text=f"{metrics1['recall']:.4f}").grid(
                row=1, column=1, padx=5, pady=2, sticky="w"
            )

            ttk.Label(s1_frame, text="F1 Score:").grid(
                row=2, column=0, padx=5, pady=2, sticky="w"
            )
            ttk.Label(s1_frame, text=f"{metrics1['f1_score']:.4f}").grid(
                row=2, column=1, padx=5, pady=2, sticky="w"
            )

            ttk.Label(s1_frame, text="Step Count:").grid(
                row=3, column=0, padx=5, pady=2, sticky="w"
            )
            ttk.Label(
                s1_frame,
                text=f"{metrics1['step_count']} (GT: {metrics1['ground_truth_count']})",
            ).grid(row=3, column=1, padx=5, pady=2, sticky="w")

            placeholder_text = "                         "
            ttk.Label(s1_frame, text=placeholder_text).grid(row=0, column=3)
            ttk.Label(s1_frame, text=placeholder_text).grid(row=1, column=3)
            ttk.Label(s1_frame, text=placeholder_text).grid(row=2, column=3)
            ttk.Label(s1_frame, text="Count Error:").grid(
                row=0,
                column=4,
                padx=5,
                pady=2,
                sticky="w",
                # row=4, column=0, padx=5, pady=2, sticky="w"
            )
            ttk.Label(
                s1_frame,
                text=f"{metrics1['step_count_error']} ({metrics1['step_count_error_percent']:.1f}%)",
            ).grid(row=0, column=5, padx=5, pady=2, sticky="w")
            # ).grid(row=4, column=1, padx=5, pady=2, sticky="w")

            ttk.Label(s1_frame, text="MSE:").grid(
                # row=5, column=0, padx=5, pady=2, sticky="w"
                row=1,
                column=4,
                padx=5,
                pady=2,
                sticky="w",
            )
            ttk.Label(s1_frame, text=f"{metrics1['mse']:.4f}").grid(
                # row=5, column=1, padx=5, pady=2, sticky="w"
                row=1,
                column=5,
                padx=5,
                pady=2,
                sticky="w",
            )

            ttk.Label(s1_frame, text="Exec. Time:").grid(
                # row=6, column=0, padx=5, pady=2, sticky="w"
                row=2,
                column=4,
                padx=5,
                pady=2,
                sticky="w",
            )
            ttk.Label(
                s1_frame,
                text=f"{results['sensor1'][algorithm_name]['execution_time']:.4f} s",
            ).grid(row=2, column=5, padx=5, pady=2, sticky="w")
            # ).grid(row=6, column=1, padx=5, pady=2, sticky="w")

            # Sensor 2 metrics
            s2_frame = ttk.LabelFrame(
                metrics_frame, text="Sensor 2 (Adafruit)", padding="2"
            )
            s2_frame.grid(row=0, column=1, padx=5, pady=2, sticky="nsew")

            ttk.Label(s2_frame, text="Precision:").grid(
                row=0, column=0, padx=5, pady=2, sticky="w"
            )
            ttk.Label(s2_frame, text=f"{metrics2['precision']:.4f}").grid(
                row=0, column=1, padx=5, pady=2, sticky="w"
            )

            ttk.Label(s2_frame, text="Recall:").grid(
                row=1, column=0, padx=5, pady=2, sticky="w"
            )
            ttk.Label(s2_frame, text=f"{metrics2['recall']:.4f}").grid(
                row=1, column=1, padx=5, pady=2, sticky="w"
            )

            ttk.Label(s2_frame, text="F1 Score:").grid(
                row=2, column=0, padx=5, pady=2, sticky="w"
            )
            ttk.Label(s2_frame, text=f"{metrics2['f1_score']:.4f}").grid(
                row=2, column=1, padx=5, pady=2, sticky="w"
            )

            ttk.Label(s2_frame, text="Step Count:").grid(
                row=3, column=0, padx=5, pady=2, sticky="w"
            )
            ttk.Label(
                s2_frame,
                text=f"{metrics2['step_count']} (GT: {metrics2['ground_truth_count']})",
            ).grid(row=3, column=1, padx=5, pady=2, sticky="w")

            ttk.Label(s2_frame, text=placeholder_text).grid(row=0, column=3)
            ttk.Label(s2_frame, text=placeholder_text).grid(row=1, column=3)
            ttk.Label(s2_frame, text=placeholder_text).grid(row=2, column=3)
            ttk.Label(s2_frame, text="Count Error:").grid(
                row=0,
                column=4,
                padx=5,
                pady=2,
                sticky="w",
                # row=4, column=0, padx=5, pady=2, sticky="w"
            )
            ttk.Label(
                s2_frame,
                text=f"{metrics2['step_count_error']} ({metrics2['step_count_error_percent']:.1f}%)",
            ).grid(row=0, column=5, padx=5, pady=2, sticky="w")
            # ).grid(row=4, column=1, padx=5, pady=2, sticky="w")

            ttk.Label(s2_frame, text="MSE:").grid(
                # row=5, column=0, padx=5, pady=2, sticky="w"
                row=1,
                column=4,
                padx=5,
                pady=2,
                sticky="w",
            )
            ttk.Label(s2_frame, text=f"{metrics2['mse']:.4f}").grid(
                # row=5, column=1, padx=5, pady=2, sticky="w"
                row=1,
                column=5,
                padx=5,
                pady=2,
                sticky="w",
            )

            ttk.Label(s2_frame, text="Exec. Time:").grid(
                # row=6, column=0, padx=5, pady=2, sticky="w"
                row=2,
                column=4,
                padx=5,
                pady=2,
                sticky="w",
            )
            ttk.Label(
                s2_frame,
                text=f"{results['sensor2'][algorithm_name]['execution_time']:.4f} s",
            ).grid(row=2, column=5, padx=5, pady=2, sticky="w")
            # ).grid(row=6, column=1, padx=5, pady=2, sticky="w")

            # Configure grid weights
            metrics_frame.columnconfigure(0, weight=1)
            metrics_frame.columnconfigure(1, weight=1)

            # Add the figure to the tab
            canvas = FigureCanvasTkAgg(fig, master=tab)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create summary tab
        summary_tab = ttk.Frame(notebook)
        notebook.add(summary_tab, text="Summary")

        # Create summary metrics table
        summary_frame = ttk.LabelFrame(
            summary_tab, text="Algorithm Performance Summary", padding="10"
        )
        summary_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        style = ttk.Style()
        style.configure("Treeview.Heading", font=("TkDefaultFont", 9, "bold"))
        style.configure("Treeview", font=("TkDefaultFont", 8))
        style.configure("Treeview", rowheight=25)

        # Configure alternating row colors for better readability
        style.map(
            "Treeview",
            background=[("selected", "#347083")],
            foreground=[("selected", "white")],
        )

        # Create table
        columns = (
            "Algorithm",
            "S1 Precision",
            "S1 Recall",
            "S1 F1",
            "S1 Error%",
            "S1 MSE",
            "S2 Precision",
            "S2 Recall",
            "S2 F1",
            "S2 Error%",
            "S2 MSE",
        )
        tree = ttk.Treeview(
            summary_frame,
            columns=columns,
            show="headings",
            height=len(param_sets.keys()) + 1,
        )

        for col in columns:
            tree.heading(col, text=col, anchor="center")

            if "Algorithm" in col:
                tree.column(col, width=100, anchor="w")

            elif "Precision" in col:
                tree.column(col, width=50, anchor="center")

            else:
                tree.column(col, width=35, anchor="center")

        for i, algorithm_name in enumerate(param_sets.keys()):
            metrics1 = results["sensor1"][algorithm_name]["metrics"]
            metrics2 = results["sensor2"][algorithm_name]["metrics"]

            tag = "evenrow" if i % 2 == 0 else "oddrow"

            tree.insert(
                "",
                tk.END,
                values=(
                    algorithm_name.replace("_", " ").title(),
                    f"{metrics1['precision']:.4f}",
                    f"{metrics1['recall']:.4f}",
                    f"{metrics1['f1_score']:.4f}",
                    f"{metrics1['step_count_error_percent']:.1f}%",
                    f"{metrics1['mse']:.4f}",
                    f"{metrics2['precision']:.4f}",
                    f"{metrics2['recall']:.4f}",
                    f"{metrics2['f1_score']:.4f}",
                    f"{metrics2['step_count_error_percent']:.1f}%",
                    f"{metrics2['mse']:.4f}",
                ),
                tags=(tag,),
            )

        # Configure row colors
        tree.tag_configure("evenrow", background="#f0f0f0")
        tree.tag_configure("oddrow", background="white")

        # Add scrollbar
        scrollbar = ttk.Scrollbar(summary_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(fill=tk.BOTH, expand=True)

        # Create visualization of algorithm rankings
        fig_summary = plt.figure(figsize=(10, 6))
        ax_summary = fig_summary.add_subplot(1, 1, 1)

        # Extract F1 scores for all algorithms
        algorithms = list(param_sets.keys())
        f1_scores_s1 = [
            results["sensor1"][alg]["metrics"]["f1_score"] for alg in algorithms
        ]
        f1_scores_s2 = [
            results["sensor2"][alg]["metrics"]["f1_score"] for alg in algorithms
        ]

        # Sort algorithms by average F1 score
        avg_scores = [
            (algorithms[i], (f1_scores_s1[i] + f1_scores_s2[i]) / 2)
            for i in range(len(algorithms))
        ]
        avg_scores.sort(key=lambda x: x[1], reverse=True)

        sorted_algorithms = [item[0] for item in avg_scores]
        sorted_f1_s1 = [
            results["sensor1"][alg]["metrics"]["f1_score"] for alg in sorted_algorithms
        ]
        sorted_f1_s2 = [
            results["sensor2"][alg]["metrics"]["f1_score"] for alg in sorted_algorithms
        ]

        # Create bar chart
        x = np.arange(len(sorted_algorithms))
        width = 0.35

        ax_summary.bar(x - width / 2, sorted_f1_s1, width, label="Sensor 1 (Waveshare)")
        ax_summary.bar(x + width / 2, sorted_f1_s2, width, label="Sensor 2 (Adafruit)")

        ax_summary.set_title("Algorithm Performance Comparison (F1 Score)")
        ax_summary.set_ylabel("F1 Score")
        ax_summary.set_ylim(0, 1.0)
        ax_summary.set_xticks(x)
        ax_summary.set_xticklabels(
            [alg.replace("_", " ").title() for alg in sorted_algorithms]
        )
        ax_summary.legend()
        ax_summary.grid(True, alpha=0.3, axis="y")

        fig_summary.tight_layout()

        # Add the figure to the summary tab
        canvas_summary = FigureCanvasTkAgg(fig_summary, master=summary_tab)
        canvas_summary.draw()
        canvas_summary.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        def on_analysis_window_close():
            plt.close("all")
            analysis_window.destroy()

        analysis_window.protocol("WM_DELETE_WINDOW", on_analysis_window_close)

        self.update_status("Analysis complete!")


    def update_status(self, message):
        """Update the status bar with a message"""
        self.status_var.set(message)
        self.master.update_idletasks()
