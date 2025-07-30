#!/usr/bin/env python3

# CONFIGURATION
API_URL = "http://192.168.4.1/api"  # AP mode
# API_URL = "http://10.9.8.119/api" # STA mode
RECORDING_NAME = "performance_test_001"
SAVE_PATH = "../analysis/test_recordings"
TARGET_RATE_HZ = 25  # Target sampling rate
REQUEST_TIMEOUT = 0.5  # Seconds
MAX_RECORDING_TIME = 17  # Seconds

import requests
import time
import json
import os
import pandas as pd
from datetime import datetime
from pynput import keyboard
import threading

# UDP
import socket
import struct

# import sys


class PerformanceTester:
    def __init__(self):
        self.session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=1, pool_maxsize=1, max_retries=0
        )
        self.session.mount("http://", adapter)

        # UDP socket
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_sock.settimeout(0.1)
        self.server_addr = (
            API_URL.split("//")[1].split("/")[0],
            12345,
        )  # Extract IP from URL

        self.recording = False
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
        self.step_times = []
        self.start_time = 0
        self.sample_count = 0
        self.last_print = 0

    def test_connection(self):
        try:
            self.udp_sock.sendto(b"GET", self.server_addr)
            data, _ = self.udp_sock.recvfrom(1024)

            values = struct.unpack("<f18f3f", data)

            print(f"✓ Connected to Pico. Battery: {values[21]:.1f}%")

            return True
        
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            return False
        # try:
        #     response = self.session.get(
        #         f"{API_URL}?action=getBatteryInfo", timeout=REQUEST_TIMEOUT
        #     )
        #     if response.status_code == 200:
        #         data = response.json()
        #         if "status" in data and data["status"] == "OK":
        #             print(
        #                 f"✓ Connected to Pico. Battery: {data['battery_percentage']:.1f}%"
        #             )
        #             return True
        #     print("✗ Invalid response from Pico")
        #     return False
        # except Exception as e:
        #     print(f"✗ Connection failed: {e}")
        #     return False

    # def read_sensors(self):
    #     try:
    #         response = self.session.get(
    #             f"{API_URL}?action=getAllData", timeout=REQUEST_TIMEOUT
    #         )
    #         if response.status_code == 200:
    #             return response.json()
    #     except:
    #         pass
    #     return None
    def read_sensors(self):
        try:
            # Send UDP request
            self.udp_sock.sendto(b"GET", self.server_addr)
            data, _ = self.udp_sock.recvfrom(1024)

            # Unpack binary data
            values = struct.unpack("<f18f3f", data)

            return {
                "status": "OK",
                "sensor1": {
                    "acceleration": {"X": values[1], "Y": values[2], "Z": values[3]},
                    "gyro": {"X": values[4], "Y": values[5], "Z": values[6]},
                    "magnetic": {"X": values[7], "Y": values[8], "Z": values[9]},
                },
                "sensor2": {
                    "acceleration": {"X": values[10], "Y": values[11], "Z": values[12]},
                    "gyro": {"X": values[13], "Y": values[14], "Z": values[15]},
                    "magnetic": {"X": values[16], "Y": values[17], "Z": values[18]},
                },
                "battery": {
                    "voltage": values[19],
                    "current": values[20],
                    "percentage": values[21],
                },
            }
        except:
            return None

    def on_press(self, key):
        try:
            if key == keyboard.Key.space:
                if not self.recording:
                    self.start_recording()
                else:
                    self.stop_recording()
            elif key == keyboard.Key.enter and self.recording:
                elapsed = time.time() - self.start_time
                self.step_times.append(elapsed)
                print(f"Step marked at {elapsed:.2f}s (total: {len(self.step_times)})")
            elif key == keyboard.Key.esc:
                return False  # Stop listener
        except AttributeError:
            pass

    def start_recording(self):
        if self.recording:
            return

        print("\n🟢 Starting recording...")
        self.recording = True
        self.start_time = time.time()
        self.sample_count = 0
        self.last_print = time.time()

        # Reset data
        for key in self.data:
            if isinstance(self.data[key], list):
                self.data[key].clear()
            else:
                for subkey in self.data[key]:
                    self.data[key][subkey].clear()
        self.step_times.clear()

        threading.Thread(target=self.recording_loop, daemon=True).start()

    def stop_recording(self):
        if not self.recording:
            return

        self.recording = False
        duration = time.time() - self.start_time
        actual_rate = self.sample_count / duration if duration > 0 else 0

        print(f"\n🔴 Recording stopped")
        print(f"Duration: {duration:.2f}s")
        print(f"Samples: {self.sample_count}")
        print(f"Actual rate: {actual_rate:.2f} Hz")
        print(f"Steps marked: {len(self.step_times)}")

        # if self.sample_count > 0:
        #     self.save_data()
        #     print("Data saved successfully")
        # else:
        #     print("No data to save")

    def recording_loop(self):
        interval = 1.0 / TARGET_RATE_HZ
        next_sample = time.time()

        while self.recording:
            current_time = time.time()

            if current_time >= next_sample:
                data = self.read_sensors()
                if data and "status" in data and data["status"] == "OK":
                    elapsed = current_time - self.start_time

                    # Store data
                    self.data["time"].append(elapsed)

                    s1 = data["sensor1"]
                    self.data["sensor1"]["accel_x"].append(s1["acceleration"]["X"])
                    self.data["sensor1"]["accel_y"].append(s1["acceleration"]["Y"])
                    self.data["sensor1"]["accel_z"].append(s1["acceleration"]["Z"])
                    self.data["sensor1"]["gyro_x"].append(s1["gyro"]["X"])
                    self.data["sensor1"]["gyro_y"].append(s1["gyro"]["Y"])
                    self.data["sensor1"]["gyro_z"].append(s1["gyro"]["Z"])
                    self.data["sensor1"]["mag_x"].append(s1["magnetic"]["X"])
                    self.data["sensor1"]["mag_y"].append(s1["magnetic"]["Y"])
                    self.data["sensor1"]["mag_z"].append(s1["magnetic"]["Z"])

                    s2 = data["sensor2"]
                    self.data["sensor2"]["accel_x"].append(s2["acceleration"]["X"])
                    self.data["sensor2"]["accel_y"].append(s2["acceleration"]["Y"])
                    self.data["sensor2"]["accel_z"].append(s2["acceleration"]["Z"])
                    self.data["sensor2"]["gyro_x"].append(s2["gyro"]["X"])
                    self.data["sensor2"]["gyro_y"].append(s2["gyro"]["Y"])
                    self.data["sensor2"]["gyro_z"].append(s2["gyro"]["Z"])
                    self.data["sensor2"]["mag_x"].append(s2["magnetic"]["X"])
                    self.data["sensor2"]["mag_y"].append(s2["magnetic"]["Y"])
                    self.data["sensor2"]["mag_z"].append(s2["magnetic"]["Z"])

                    bat = data["battery"]
                    self.data["battery"]["voltage"].append(bat["voltage"])
                    self.data["battery"]["current"].append(bat["current"])
                    self.data["battery"]["percentage"].append(bat["percentage"])

                    self.sample_count += 1

                    # Progress update
                    if current_time - self.last_print >= 2.0:
                        rate = self.sample_count / elapsed if elapsed > 0 else 0
                        print(
                            f"Recording... {elapsed:.1f}s, {self.sample_count} samples, {rate:.2f} Hz, {len(self.step_times)} steps"
                        )
                        self.last_print = current_time

                next_sample += interval

                # Safety limit
                if time.time() - self.start_time > MAX_RECORDING_TIME:
                    print(
                        f"\nMax recording time ({MAX_RECORDING_TIME}s) reached, stopping..."
                    )
                    self.recording = False
                    break
            else:
                time.sleep(0.001)  # 1ms sleep to prevent busy waiting

    def save_data(self):
        if not os.path.exists(SAVE_PATH):
            os.makedirs(SAVE_PATH)

        recording_dir = os.path.join(SAVE_PATH, RECORDING_NAME)
        if not os.path.exists(recording_dir):
            os.makedirs(recording_dir)

        # Save sensor data
        for sensor_name in ["sensor1", "sensor2"]:
            df = pd.DataFrame(
                {
                    "time": self.data["time"],
                    **{
                        f"{key}": self.data[sensor_name][key]
                        for key in self.data[sensor_name]
                    },
                }
            )
            filename = f"{sensor_name}_{'waveshare' if sensor_name == 'sensor1' else 'adafruit'}.csv"
            df.to_csv(os.path.join(recording_dir, filename), index=False)

        # Save battery data
        battery_df = pd.DataFrame({"time": self.data["time"], **self.data["battery"]})
        battery_df.to_csv(os.path.join(recording_dir, "battery.csv"), index=False)

        # Save ground truth
        ground_truth_df = pd.DataFrame({"step_times": self.step_times})
        ground_truth_df.to_csv(
            os.path.join(recording_dir, "ground_truth.csv"), index=False
        )

        # Save metadata
        duration = self.data["time"][-1] if self.data["time"] else 0
        actual_rate = self.sample_count / duration if duration > 0 else 0

        metadata = {
            "recording_name": RECORDING_NAME,
            "recording_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_duration": duration,
            "step_count": len(self.step_times),
            "sampling_frequency": actual_rate,
            "target_frequency": TARGET_RATE_HZ,
            "samples_collected": self.sample_count,
        }

        with open(os.path.join(recording_dir, "metadata.json"), "w") as f:
            json.dump(metadata, f, indent=4)

    def run(self):
        print("=" * 50)
        print("SENSOR PERFORMANCE TEST")
        print("=" * 50)
        print(f"API URL: {API_URL}")
        print(f"Recording: {RECORDING_NAME}")
        print(f"Target rate: {TARGET_RATE_HZ} Hz")
        print(f"Save path: {SAVE_PATH}")
        print()

        if not self.test_connection():
            print("Exiting due to connection failure")
            return

        print("\nControls:")
        print("  SPACE: Start/Stop recording")
        print("  ENTER: Mark step (during recording)")
        print("  ESC: Exit")
        print("\nPress SPACE to start...")

        listener = keyboard.Listener(on_press=self.on_press)
        listener.start()

        try:
            listener.join()  # Wait for ESC key
        except KeyboardInterrupt:
            print("\n\nExiting...")

        if self.recording:
            self.stop_recording()
        self.session.close()


if __name__ == "__main__":
    tester = PerformanceTester()
    tester.run()
