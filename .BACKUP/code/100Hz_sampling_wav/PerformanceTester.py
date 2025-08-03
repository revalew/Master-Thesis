#!/usr/bin/env python3

"""
Optimized performance tester for Pico 2 W sensor system
Target: 50+ Hz minimum, 100+ Hz preferred
"""

import socket
import struct
import time
import threading
from pynput import keyboard

# Configuration
PICO_IP = "192.168.4.1"
UDP_PORT = 12345
TARGET_RATE_HZ = 150  # Increased to compensate for packet loss


class OptimizedPerformanceTester:
    def __init__(self):
        # UDP socket with larger buffer
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_sock.settimeout(0.5)
        self.udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)
        self.server_addr = (PICO_IP, UDP_PORT)

        # Recording state
        self.recording = False
        self.samples = []
        self.step_times = []

        # Performance tracking
        self.start_time = 0
        self.sample_count = 0
        self.packet_count = 0
        self.errors = 0
        self.last_print = 0

    def test_connection(self):
        """Test connection to Pico system"""
        print("Testing connection to optimized Pico system...")

        try:
            self.udp_sock.sendto(b"STATUS", self.server_addr)
            data, _ = self.udp_sock.recvfrom(1024)

            if len(data) >= 13:
                status = struct.unpack("<BIII", data[:13])
                print(f"Connected to Pico")
                print(f"  Sampling active: {bool(status[0])}")
                print(
                    f"  Samples: {status[1]}, Packets: {status[2]}, Errors: {status[3]}"
                )
                return True
            else:
                print(f"Invalid response: {len(data)} bytes")
                return False

        except Exception as e:
            print(f"Connection failed: {e}")
            return False

    def start_recording(self):
        """Start high-frequency recording"""
        if self.recording:
            return

        print(f"\nStarting recording at {TARGET_RATE_HZ} Hz target...")

        try:
            self.udp_sock.sendto(b"START_HF", self.server_addr)
            data, _ = self.udp_sock.recvfrom(1024)

            if len(data) >= 2:
                ack = struct.unpack("<H", data[:2])[0]
                if ack == 0xACE:
                    print("Recording started on Pico")

                    self.recording = True
                    self.start_time = time.time()
                    self.sample_count = 0
                    self.packet_count = 0
                    self.errors = 0
                    self.last_print = time.time()
                    self.samples.clear()
                    self.step_times.clear()

                    threading.Thread(target=self.receive_thread, daemon=True).start()
                    return

            print(f"Failed to start - response: {data}")

        except Exception as e:
            print(f"Error starting: {e}")

    def stop_recording(self):
        """Stop recording and show results"""
        if not self.recording:
            return

        self.recording = False

        try:
            self.udp_sock.sendto(b"STOP_HF", self.server_addr)
            data, _ = self.udp_sock.recvfrom(1024)

            if len(data) >= 12:
                pico_stats = struct.unpack("<III", data[:12])
                print(f"\nRecording stopped")
                print(
                    f"Pico: {pico_stats[0]} samples, {pico_stats[1]} packets, {pico_stats[2]} errors"
                )

        except Exception as e:
            print(f"Error stopping: {e}")

        # Calculate results
        duration = time.time() - self.start_time
        actual_rate = self.sample_count / duration if duration > 0 else 0
        packet_rate = self.packet_count / duration if duration > 0 else 0

        print(f"\n=== RESULTS ===")
        print(f"Duration: {duration:.2f}s")
        print(f"Samples received: {self.sample_count}")
        print(f"Packets received: {self.packet_count}")
        print(f"Errors: {self.errors}")
        print(
            f"Rate: {actual_rate:.2f} Hz ({actual_rate/TARGET_RATE_HZ*100:.1f}% of target)"
        )
        print(f"Packet rate: {packet_rate:.2f}/s")
        print(f"Steps marked: {len(self.step_times)}")

        # Success criteria
        if actual_rate >= 50:
            print(f"SUCCESS: Achieved {actual_rate:.1f} Hz (>= 50 Hz required)")
        else:
            print(f"FAILED: {actual_rate:.1f} Hz below 50 Hz minimum")

    def receive_thread(self):
        """Simplified receive thread with better error handling"""
        self.udp_sock.settimeout(2.0)

        while self.recording:
            try:
                data, _ = self.udp_sock.recvfrom(4096)
                receive_time = time.time()

                if len(data) < 4:
                    continue

                # Parse batch header
                magic, count = struct.unpack("<HH", data[:4])
                if magic != 0xBEEF:
                    self.errors += 1
                    continue

                self.packet_count += 1

                # Parse samples - each sample is 16 bytes (4 + 4 + 4 + 4)
                sample_size = 16
                samples_parsed = 0

                for i in range(count):
                    offset = 4 + i * sample_size
                    if offset + sample_size <= len(data):
                        try:
                            sample_data = data[offset : offset + sample_size]
                            timestamp, x, y, z = struct.unpack("<Ifff", sample_data)

                            # Store sample
                            elapsed = receive_time - self.start_time
                            self.samples.append(
                                {
                                    "time": elapsed,
                                    "accel_x": x,
                                    "accel_y": y,
                                    "accel_z": z,
                                    "pico_timestamp": timestamp,
                                }
                            )

                            samples_parsed += 1

                        except struct.error:
                            self.errors += 1

                self.sample_count += samples_parsed

                # Progress update
                current_time = time.time()
                if current_time - self.last_print >= 3.0:
                    elapsed = current_time - self.start_time
                    rate = self.sample_count / elapsed if elapsed > 0 else 0
                    efficiency = (
                        (rate / TARGET_RATE_HZ * 100) if TARGET_RATE_HZ > 0 else 0
                    )

                    print(
                        f"Progress: {elapsed:.1f}s | {self.sample_count} samples | "
                        f"{rate:.1f} Hz ({efficiency:.0f}%) | "
                        f"{self.packet_count} packets | {len(self.step_times)} steps"
                    )
                    self.last_print = current_time

            except socket.timeout:
                continue
            except Exception as e:
                self.errors += 1
                print(f"Receive error: {e}")

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
                return False
        except AttributeError:
            pass

    def run(self):
        print("=" * 60)
        print("OPTIMIZED PICO 2 W PERFORMANCE TEST")
        print("=" * 60)
        print(f"Target: {TARGET_RATE_HZ} Hz")
        print(f"Minimum: 50 Hz")
        print(f"Preferred: 100 Hz")
        print()

        if not self.test_connection():
            print("Connection failed - check Pico system")
            return

        print("\nControls:")
        print("  SPACE: Start/Stop recording")
        print("  ENTER: Mark step")
        print("  ESC: Exit")
        print(f"\nPress SPACE to start recording...")

        listener = keyboard.Listener(on_press=self.on_press)
        listener.start()

        try:
            listener.join()
        except KeyboardInterrupt:
            print("\nExiting...")

        if self.recording:
            self.stop_recording()

        self.udp_sock.close()


if __name__ == "__main__":
    tester = OptimizedPerformanceTester()
    tester.run()
