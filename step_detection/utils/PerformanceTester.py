#!/usr/bin/env python3

# CONFIGURATION
API_URL = "http://192.168.4.1/api"  # AP mode
# API_URL = "http://10.9.8.119/api" # STA mode
SAVE_PATH = "../analysis/performance_tests"  # Directory to save results
TARGET_RATE_HZ = 200  # Target sampling rate: 25, 50, 100, 200
REQUEST_TIMEOUT = 0.5  # Seconds
MAX_RECORDING_TIME = 16  # Seconds
RECORDING_NAME = f"performance_test_{TARGET_RATE_HZ}hz"

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


class PerformanceTester:
    def __init__(self):
        self.session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=1, pool_maxsize=1, max_retries=0
        )
        self.session.mount("http://", adapter)

        # UDP socket with longer timeouts
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_sock.settimeout(5.0)  # Increased timeout
        self.server_addr = (
            API_URL.split("//")[1].split("/")[0],
            12345,
        )

        self.recording = False
        self.debug_packets = True
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
        self.packet_count = 0
        self.last_print = 0

        # For accurate timing
        self.first_timestamp = None
        self.last_timestamp = None

    def test_connection(self):
        try:
            # Test with STATUS command
            self.udp_sock.sendto(b"STATUS", self.server_addr)
            data, _ = self.udp_sock.recvfrom(1024)

            if len(data) >= 17:
                status = struct.unpack("<BIIII", data[:17])
                print(f"✓ Connected to Pico - Active: {bool(status[0])}")
                return True
            return False
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            return False

    def set_sampling_rate(self, hz):
        """Set sampling rate: 25, 50, 100, 200 Hz"""
        print(f"Setting sampling rate to {hz} Hz...")
        try:
            command = f"SET_RATE_{hz}".encode()
            self.udp_sock.sendto(command, self.server_addr)
            data, _ = self.udp_sock.recvfrom(64)

            if len(data) >= 1:
                success = struct.unpack("<B", data[:1])[0]
                if success:
                    print(f"✓ Rate set to {hz} Hz")
                    return True

        except Exception as e:
            print(f"✗ Rate setting failed: {e}")
        return False

    def start_high_speed_sampling(self):
        """Start high-speed sampling on Pico"""
        print("Starting high-speed sampling...")
        try:
            self.udp_sock.sendto(b"START", self.server_addr)
            data, _ = self.udp_sock.recvfrom(1024)

            if len(data) >= 2:
                ack = struct.unpack("<H", data[:2])[0]
                if ack == 0xACE:
                    print("✓ High-speed sampling started")
                    return True
                else:
                    print(f"✗ Start failed: 0x{ack:04x}")

        except Exception as e:
            print(f"✗ Start failed: {e}")
        return False

    def stop_high_speed_sampling(self):
        """Stop high-speed sampling on Pico"""
        print("Stopping high-speed sampling...")
        try:
            # Try multiple times with longer timeout
            for attempt in range(3):
                try:
                    self.udp_sock.settimeout(3.0)
                    self.udp_sock.sendto(b"STOP", self.server_addr)
                    data, _ = self.udp_sock.recvfrom(1024)

                    if len(data) >= 12:
                        stats = struct.unpack("<III", data[:12])
                        print(
                            f"✓ Stopped - {stats[0]} samples, {stats[1]} packets, {stats[2]} errors"
                        )
                        return True

                except socket.timeout:
                    print(f"Stop attempt {attempt + 1} timed out, retrying...")
                    continue

        except Exception as e:
            print(f"✗ Stop failed: {e}")

        print("✗ Stop failed after 3 attempts")
        return False

    def parse_sample_packet(self, data):
        """Parse high-speed sample packet"""
        if len(data) < 4:
            return []

        # Parse header
        magic, count = struct.unpack("<HH", data[:4])
        if magic != 0xBEEF:
            return []

        samples = []
        sample_size = 76  # 4 + 72 bytes (timestamp int (ticks_ms) + 18 floats)

        if self.debug_packets:
            print(
                f"Packet: magic=0x{magic:04x}, count={count}, data_len={len(data)}, expected_size={4 + count * sample_size}"
            )

        for i in range(count):
            offset = 4 + i * sample_size
            if offset + sample_size <= len(data):
                try:
                    # Unpack: timestamp (I) + 18 floats
                    sample_data = struct.unpack(
                        "<I18f", data[offset : offset + sample_size]
                    )

                    timestamp = sample_data[0]

                    # Sensor 1 data (indices 1-9)
                    s1_accel = sample_data[1:4]  # accel x,y,z
                    s1_gyro = sample_data[4:7]  # gyro x,y,z
                    s1_mag = sample_data[7:10]  # mag x,y,z

                    # Sensor 2 data (indices 10-18)
                    s2_accel = sample_data[10:13]  # accel x,y,z
                    s2_gyro = sample_data[13:16]  # gyro x,y,z
                    s2_mag = sample_data[16:19]  # mag x,y,z

                    samples.append(
                        {
                            "timestamp": timestamp,
                            "sensor1": {
                                "accel": s1_accel,
                                "gyro": s1_gyro,
                                "mag": s1_mag,
                            },
                            "sensor2": {
                                "accel": s2_accel,
                                "gyro": s2_gyro,
                                "mag": s2_mag,
                            },
                        }
                    )

                except struct.error as e:
                    if self.debug_packets:
                        print(f"Struct unpack error at sample {i}: {e}")
                        print(f"Data slice: {data[offset:offset + sample_size].hex()}")
                    continue
            else:
                if self.debug_packets:
                    print(
                        f"Not enough data for sample {i}: need {sample_size}, have {len(data) - offset}"
                    )

        if self.debug_packets:
            print(f"Parsed {len(samples)} samples from packet")
            if len(samples) > 0:
                self.debug_packets = (
                    False  # Turn off debugging after first successful parse
                )
                print("Debug mode disabled - packet parsing working")

        return samples

    def get_battery_info(self):
        """Get battery info via single GET request (avoid during recording)"""
        if self.recording:
            # Don't interfere with high-speed recording
            return {"voltage": 4.0, "current": 0.5, "percentage": 80.0}

        try:
            self.udp_sock.sendto(b"GET", self.server_addr)
            data, _ = self.udp_sock.recvfrom(1024)

            values = struct.unpack("<f18f3f", data)
            return {
                "voltage": values[19],
                "current": values[20],
                "percentage": values[21],
            }
        except:
            return {"voltage": 0.0, "current": 0.0, "percentage": 0.0}

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
            elif hasattr(key, "char"):
                if key.char == "s" and not self.recording:
                    # Save current data
                    if self.sample_count > 0:
                        self.save_data()
                        print("Data saved!")
                    else:
                        print("No data to save")
        except AttributeError:
            pass

    def start_recording(self):
        if self.recording:
            return

        print(f"\n🟢 Starting high-speed recording at {TARGET_RATE_HZ} Hz...")

        # Set sampling rate with retry
        for attempt in range(3):
            if self.set_sampling_rate(TARGET_RATE_HZ):
                break
            if attempt < 2:
                print(f"Retry rate setting (attempt {attempt + 2})...")
                time.sleep(1)
        else:
            print("Failed to set sampling rate after 3 attempts")
            return

        # Start high-speed sampling with retry
        for attempt in range(3):
            if self.start_high_speed_sampling():
                break
            if attempt < 2:
                print(f"Retry start sampling (attempt {attempt + 2})...")
                time.sleep(1)
        else:
            print("Failed to start sampling after 3 attempts")
            return

        self.recording = True
        self.start_time = time.time()
        self.sample_count = 0
        self.packet_count = 0
        self.last_print = time.time()

        # Reset timestamp tracking
        self.first_timestamp = None
        self.last_timestamp = None

        # Reset data
        for key in self.data:
            if isinstance(self.data[key], list):
                self.data[key].clear()
            else:
                for subkey in self.data[key]:
                    self.data[key][subkey].clear()
        self.step_times.clear()

        # Set socket timeout for data reception
        self.udp_sock.settimeout(0.5)
        threading.Thread(target=self.high_speed_recording_loop, daemon=True).start()

    def stop_recording(self):
        if not self.recording:
            return

        self.recording = False

        # Stop high-speed sampling
        self.stop_high_speed_sampling()

        # Calculate duration from packet timestamps (more accurate)
        if self.first_timestamp and self.last_timestamp:
            duration = (self.last_timestamp - self.first_timestamp) / 1000.0
        else:
            duration = time.time() - self.start_time

        actual_rate = self.sample_count / duration if duration > 0 else 0

        print(f"\n🔴 Recording stopped")
        print(f"Duration: {duration:.2f}s (from packet timestamps)")
        print(f"Samples: {self.sample_count}")
        print(f"Packets: {self.packet_count}")
        print(f"Actual rate: {actual_rate:.2f} Hz")
        print(f"Steps marked: {len(self.step_times)}")
        print("\nPress 'S' to save data, or SPACE to start new recording")

    def high_speed_recording_loop(self):
        """High-speed data collection loop"""
        # Disable battery updates during high-speed recording for better performance

        while self.recording:
            try:
                # Receive high-speed data packets
                data, _ = self.udp_sock.recvfrom(4096)
                current_time = time.time()

                # Skip short packets (likely control responses)
                if len(data) < 20:
                    print(
                        f"Skipping short packet: {len(data)} bytes, data: {data.hex()}"
                    )
                    continue

                # Parse samples from packet
                samples = self.parse_sample_packet(data)

                if samples:
                    self.packet_count += 1

                    # Store all samples from this packet
                    for sample in samples:
                        # Use packet timestamp for accurate timing
                        timestamp_ms = sample["timestamp"]

                        if self.first_timestamp is None:
                            self.first_timestamp = timestamp_ms
                        self.last_timestamp = timestamp_ms

                        # Calculate elapsed time from first timestamp
                        elapsed = (timestamp_ms - self.first_timestamp) / 1000.0
                        self.data["time"].append(elapsed)

                        # Sensor 1 data
                        s1 = sample["sensor1"]
                        self.data["sensor1"]["accel_x"].append(s1["accel"][0])
                        self.data["sensor1"]["accel_y"].append(s1["accel"][1])
                        self.data["sensor1"]["accel_z"].append(s1["accel"][2])
                        self.data["sensor1"]["gyro_x"].append(s1["gyro"][0])
                        self.data["sensor1"]["gyro_y"].append(s1["gyro"][1])
                        self.data["sensor1"]["gyro_z"].append(s1["gyro"][2])
                        self.data["sensor1"]["mag_x"].append(s1["mag"][0])
                        self.data["sensor1"]["mag_y"].append(s1["mag"][1])
                        self.data["sensor1"]["mag_z"].append(s1["mag"][2])

                        # Sensor 2 data
                        s2 = sample["sensor2"]
                        self.data["sensor2"]["accel_x"].append(s2["accel"][0])
                        self.data["sensor2"]["accel_y"].append(s2["accel"][1])
                        self.data["sensor2"]["accel_z"].append(s2["accel"][2])
                        self.data["sensor2"]["gyro_x"].append(s2["gyro"][0])
                        self.data["sensor2"]["gyro_y"].append(s2["gyro"][1])
                        self.data["sensor2"]["gyro_z"].append(s2["gyro"][2])
                        self.data["sensor2"]["mag_x"].append(s2["mag"][0])
                        self.data["sensor2"]["mag_y"].append(s2["mag"][1])
                        self.data["sensor2"]["mag_z"].append(s2["mag"][2])

                        # Battery data - use fixed values during recording for performance
                        self.data["battery"]["voltage"].append(4.0)  # Placeholder
                        self.data["battery"]["current"].append(0.5)  # Placeholder
                        self.data["battery"]["percentage"].append(80.0)  # Placeholder

                        self.sample_count += 1

                # Progress update using packet timestamps
                if current_time - self.last_print >= 3.0:
                    if self.first_timestamp and self.last_timestamp:
                        duration = (self.last_timestamp - self.first_timestamp) / 1000.0
                        rate = self.sample_count / duration if duration > 0 else 0
                        efficiency = (
                            (rate / TARGET_RATE_HZ * 100) if TARGET_RATE_HZ > 0 else 0
                        )
                        print(
                            f"Recording... {duration:.1f}s, {self.sample_count} samples, {rate:.1f} Hz ({efficiency:.0f}%), {len(self.step_times)} steps"
                        )
                    self.last_print = current_time

                # Safety limit using real time (not packet time)
                if time.time() - self.start_time > MAX_RECORDING_TIME:
                    print(
                        f"\nMax recording time ({MAX_RECORDING_TIME}s) reached, stopping..."
                    )
                    self.recording = False
                    break

            except socket.timeout:
                # No data received - check if still recording
                if time.time() - self.start_time > 5 and self.sample_count == 0:
                    print("No data received for 5 seconds, stopping...")
                    self.recording = False
                    break
                continue
            except Exception as e:
                print(f"Recording error: {e}")
                continue

    def save_data(self):
        if self.sample_count == 0:
            print("No data to save")
            return

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

        # Calculate accurate duration and rate
        if self.first_timestamp and self.last_timestamp:
            duration = (self.last_timestamp - self.first_timestamp) / 1000.0
        else:
            duration = self.data["time"][-1] if self.data["time"] else 0

        actual_rate = self.sample_count / duration if duration > 0 else 0

        # Save metadata
        metadata = {
            "recording_name": RECORDING_NAME,
            "recording_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_duration": duration,
            "step_count": len(self.step_times),
            "sampling_frequency": actual_rate,
            "target_frequency": TARGET_RATE_HZ,
            "samples_collected": self.sample_count,
            "packets_received": self.packet_count,
            "first_timestamp_ms": self.first_timestamp,
            "last_timestamp_ms": self.last_timestamp,
        }

        with open(os.path.join(recording_dir, "metadata.json"), "w") as f:
            json.dump(metadata, f, indent=4)

        print(f"Data saved to {recording_dir}")
        print(
            f"Metadata: {duration:.2f}s, {actual_rate:.2f} Hz, {self.sample_count} samples"
        )

    def run(self):
        print("=" * 60)
        print("HIGH-SPEED SENSOR PERFORMANCE TEST")
        print("=" * 60)
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
        print("  S: Save data (when stopped)")
        print("  ESC: Exit")
        print(f"Press SPACE to start {TARGET_RATE_HZ} Hz recording...")
        print("Note: Rate setting/stopping may timeout but system usually recovers")

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
