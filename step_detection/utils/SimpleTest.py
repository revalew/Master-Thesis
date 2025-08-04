#!/usr/bin/env python3

"""
Robust test for Pico 2 W sensor system
Tests multiple start/stop cycles and error recovery
"""

import socket
import struct
import time

PICO_IP = "192.168.4.1"
UDP_PORT = 12345


class SimpleTest:
    def __init__(self):
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_sock.settimeout(3.0)
        self.server_addr = (PICO_IP, UDP_PORT)

    def send_command(self, command, expect_response=True, timeout=5.0):
        """Send command and get response with longer timeout"""
        original_timeout = self.udp_sock.gettimeout()
        try:
            self.udp_sock.settimeout(timeout)
            self.udp_sock.sendto(command, self.server_addr)
            if expect_response:
                data, _ = self.udp_sock.recvfrom(1024)
                return data
            return None
        except Exception as e:
            print(f"Command failed: {e}")
            return None
        finally:
            self.udp_sock.settimeout(original_timeout)

    def test_connection(self):
        """Test basic connection"""
        print("Testing connection...")
        data = self.send_command(b"STATUS")
        if data and len(data) >= 17:
            status = struct.unpack("<BIIII", data[:17])
            print(f"✓ Connected - Active: {bool(status[0])}")
            return True
        print("✗ Connection failed")
        return False

    def set_rate(self, hz):
        """Set sampling rate"""
        print(f"Setting rate to {hz} Hz...")
        data = self.send_command(f"SET_RATE_{hz}".encode())
        if data and len(data) >= 1:
            success = struct.unpack("<B", data[:1])[0]
            if success:
                print(f"✓ Rate set to {hz} Hz")
                return True
        print(f"✗ Failed to set rate to {hz} Hz")
        return False

    def start_sampling(self):
        """Start sampling"""
        print("Starting sampling...")
        data = self.send_command(b"START")
        if data and len(data) >= 2:
            ack = struct.unpack("<H", data[:2])[0]
            if ack == 0xACE:
                print("✓ Sampling started")
                return True
            elif ack == 0xFFFF:
                print("✗ Sampling failed to start (error)")
                return False
            else:
                print(f"✗ Unexpected response: 0x{ack:04x}")
                return False
        print("✗ No response to start command")
        return False

    def stop_sampling(self):
        """Stop sampling"""
        print("Stopping sampling...")
        data = self.send_command(b"STOP")
        if data and len(data) >= 12:
            stats = struct.unpack("<III", data[:12])
            print(
                f"✓ Stopped - {stats[0]} samples, {stats[1]} packets, {stats[2]} errors"
            )
            return True
        print("✗ Failed to stop properly")
        return False

    def collect_data(self, duration=3):
        """Collect data for specified duration"""
        print(f"Collecting data for {duration}s...")
        start_time = time.time()
        samples = 0
        packets = 0

        while time.time() - start_time < duration:
            try:
                data, _ = self.udp_sock.recvfrom(4096)
                if len(data) >= 4:
                    magic, count = struct.unpack("<HH", data[:4])
                    if magic == 0xBEEF:
                        packets += 1
                        samples += count
            except socket.timeout:
                continue
            except Exception:
                break

        actual_duration = time.time() - start_time
        rate = samples / actual_duration if actual_duration > 0 else 0
        print(f"Collected {samples} samples, {packets} packets, {rate:.1f} Hz")
        return samples, packets, rate

    def test_start_stop_cycle(self, hz, duration=3):
        """Test complete start/stop cycle"""
        print(f"\n=== Testing {hz} Hz cycle ===")

        if not self.set_rate(hz):
            return False

        # Small delay before start
        time.sleep(0.5)

        if not self.start_sampling():
            return False

        samples, packets, rate = self.collect_data(duration)

        if not self.stop_sampling():
            return False

        # Delay after stop before next cycle
        time.sleep(0.5)

        # Check if rate is reasonable
        efficiency = (rate / hz * 100) if hz > 0 else 0
        success = rate >= hz * 0.5  # At least 50% efficiency

        print(f"Efficiency: {efficiency:.1f}% - {'PASS' if success else 'FAIL'}")
        return success

    def test_multiple_cycles(self):
        """Test multiple start/stop cycles"""
        print("\n=== TESTING MULTIPLE CYCLES ===")

        cycles = [
            (50, 3),  # 50 Hz for 3 seconds
            (100, 3),  # 100 Hz for 3 seconds
            (50, 2),  # 50 Hz for 2 seconds
            (200, 2),  # 200 Hz for 2 seconds
            (100, 3),  # 100 Hz for 3 seconds
        ]

        results = []
        for i, (hz, duration) in enumerate(cycles, 1):
            print(f"\n--- Cycle {i}/{len(cycles)} ---")
            success = self.test_start_stop_cycle(hz, duration)
            results.append((hz, success))

            # Longer pause between cycles for cleanup
            time.sleep(2)

        return results


    def run_tests(self):
        """Run all tests"""
        print("=== ROBUST PICO SYSTEM TEST ===")
        print("Testing timer cleanup and error recovery")
        print()

        if not self.test_connection():
            return

        # Test basic cycles
        results = self.test_multiple_cycles()

        # Summary
        print(f"\n=== SUMMARY ===")
        passed = sum(1 for _, success in results if success)
        total = len(results)

        for hz, success in results:
            status = "PASS" if success else "FAIL"
            print(f"{hz:3d} Hz: {status}")

        print(f"\nPassed: {passed}/{total} cycles")

        if passed == total:
            print("✓ ALL TESTS PASSED - System is robust")
        elif passed >= total * 0.8:
            print("⚠ MOSTLY WORKING - Minor issues")
        else:
            print("✗ MULTIPLE FAILURES - System needs fixes")

        self.udp_sock.close()


if __name__ == "__main__":
    tester = SimpleTest()
    tester.run_tests()
