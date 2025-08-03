"""
Native ICM20948 driver for Pico 2 W - bypasses Adafruit limitations
Target: 100+ Hz accelerometer sampling
"""

import asyncio
import socket
import struct
import time
import micropython
import gc
import machine
from machine import Timer, freq, Pin, I2C

# from board import GP6, GP7
# from busio import I2C

# Performance settings
freq(240000000)
gc.threshold(32768)
micropython.alloc_emergency_exception_buf(100)

from classes import WiFiConnection

# Native I2C setup
i2c = I2C(1, scl=Pin(7), sda=Pin(6), freq=1000000)
# i2c = I2C(1, scl=Pin(7), sda=Pin(6), freq=400000)
# i2c = I2C(scl=GP7, sda=GP6, frequency=400000)

# ICM20948 constants
ICM20948_ADDR = 0x68
ICM20948_WHO_AM_I = 0x00
ICM20948_PWR_MGMT_1 = 0x06
ICM20948_ACCEL_XOUT_H = 0x2D
ICM20948_REG_BANK_SEL = 0x7F
ICM20948_ACCEL_SMPLRT_DIV_1 = 0x10
ICM20948_ACCEL_SMPLRT_DIV_2 = 0x11
ICM20948_ACCEL_CONFIG_1 = 0x14


class FastICM20948:
    def __init__(self, i2c_bus):
        self.i2c = i2c_bus
        self.setup_sensor()

    def setup_sensor(self):
        """Initialize sensor for maximum speed"""
        print("Setting up ICM20948...")

        # Check WHO_AM_I
        who_am_i = self.read_register(0, ICM20948_WHO_AM_I)
        print(f"WHO_AM_I: 0x{who_am_i:02x}")

        # Wake up sensor
        self.write_register(0, ICM20948_PWR_MGMT_1, 0x01)  # Auto clock
        time.sleep_ms(10)

        # Configure accelerometer for max speed (Bank 2)
        self.write_register(2, ICM20948_ACCEL_SMPLRT_DIV_1, 0x00)  # Div high byte
        self.write_register(
            2, ICM20948_ACCEL_SMPLRT_DIV_2, 0x00
        )  # Div low byte = max speed
        self.write_register(2, ICM20948_ACCEL_CONFIG_1, 0x14)  # ±8g range, no DLPF

        print("ICM20948 configured for maximum speed")

    def write_register(self, bank, reg, value):
        """Write to register in specific bank"""
        # Set bank
        self.i2c.writeto_mem(ICM20948_ADDR, ICM20948_REG_BANK_SEL, bytes([bank << 4]))
        # Write register
        self.i2c.writeto_mem(ICM20948_ADDR, reg, bytes([value]))

    def read_register(self, bank, reg):
        """Read from register in specific bank"""
        # Set bank
        self.i2c.writeto_mem(ICM20948_ADDR, ICM20948_REG_BANK_SEL, bytes([bank << 4]))
        # Read register
        data = self.i2c.readfrom_mem(ICM20948_ADDR, reg, 1)
        return data[0]

    @micropython.native
    def read_acceleration_fast(self):
        """Ultra-fast acceleration read - no bank switching, no sleep"""
        try:
            # Assume bank 0 is already set (optimization)
            raw_data = self.i2c.readfrom_mem(ICM20948_ADDR, ICM20948_ACCEL_XOUT_H, 6)

            # Convert to signed 16-bit values (big endian)
            x_raw = (raw_data[0] << 8) | raw_data[1]
            y_raw = (raw_data[2] << 8) | raw_data[3]
            z_raw = (raw_data[4] << 8) | raw_data[5]

            # Convert to signed
            if x_raw > 32767:
                x_raw -= 65536
            if y_raw > 32767:
                y_raw -= 65536
            if z_raw > 32767:
                z_raw -= 65536

            # Scale to m/s² (±8g range, 4096 LSB/g)
            scale = 8.0 / 4096.0 * 9.80665
            return (x_raw * scale, y_raw * scale, z_raw * scale)

        except Exception:
            return None


class HighSpeedUDPHandler:
    def __init__(self, sensor, target_hz=100):
        self.sensor = sensor
        self.target_hz = target_hz

        # UDP setup
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_sock.bind(("0.0.0.0", 12345))
        self.udp_sock.settimeout(0.001)

        # Sampling state
        self.sampling_active = False
        self.hardware_timer = Timer(-1)
        self.sample_buffer = []
        self.batch_size = 10

        # Stats
        self.samples_generated = 0
        self.packets_sent = 0
        self.send_errors = 0
        self.client_addr = None

        print(f"High-speed handler: {target_hz} Hz target")

    def start_sampling(self):
        if self.sampling_active:
            return

        print(f"Starting native sampling at {self.target_hz} Hz")
        self.sampling_active = True
        self.samples_generated = 0
        self.packets_sent = 0
        self.send_errors = 0
        self.sample_buffer.clear()

        # Direct timer at target rate
        timer_period = 1000 // self.target_hz

        self.hardware_timer.init(
            period=timer_period, mode=Timer.PERIODIC, callback=self.timer_callback
        )

        print(f"Native timer: {self.target_hz} Hz ({timer_period}ms period)")

    @micropython.native
    def timer_callback(self, timer):
        """High-speed timer callback with native I2C"""
        if not self.sampling_active or not self.client_addr:
            return

        try:
            # Ultra-fast sensor read
            accel_data = self.sensor.read_acceleration_fast()
            if accel_data is None:
                self.send_errors += 1
                return

            timestamp = time.ticks_ms()

            # Pack and store
            sample = struct.pack(
                "<Ifff", timestamp, accel_data[0], accel_data[1], accel_data[2]
            )
            self.sample_buffer.append(sample)
            self.samples_generated += 1

            # Send when batch ready
            if len(self.sample_buffer) >= self.batch_size:
                self.send_batch()

        except Exception:
            self.send_errors += 1

    @micropython.native
    def send_batch(self):
        """Send batch efficiently"""
        if not self.sample_buffer or not self.client_addr:
            return

        try:
            batch_count = len(self.sample_buffer)
            header = struct.pack("<HH", 0xBEEF, batch_count)
            batch_data = header + b"".join(self.sample_buffer)

            self.udp_sock.sendto(batch_data, self.client_addr)
            self.sample_buffer.clear()
            self.packets_sent += 1

        except Exception:
            self.send_errors += 1

    def stop_sampling(self):
        if not self.sampling_active:
            return

        self.sampling_active = False
        self.hardware_timer.deinit()

        if self.sample_buffer:
            self.send_batch()

        print(
            f"Stopped: {self.samples_generated} samples, {self.packets_sent} packets, {self.send_errors} errors"
        )

    async def handle_requests(self):
        """Handle UDP commands"""
        print("Native UDP handler waiting...")

        while True:
            try:
                data, addr = self.udp_sock.recvfrom(64)

                if data == b"START_HF":
                    self.client_addr = addr
                    self.start_sampling()
                    ack = struct.pack("<H", 0xACE)
                    self.udp_sock.sendto(ack, addr)

                elif data == b"STOP_HF":
                    self.stop_sampling()
                    self.client_addr = None
                    stats = struct.pack(
                        "<III",
                        self.samples_generated,
                        self.packets_sent,
                        self.send_errors,
                    )
                    self.udp_sock.sendto(stats, addr)

                elif data == b"STATUS":
                    status = struct.pack(
                        "<BIII",
                        1 if self.sampling_active else 0,
                        self.samples_generated,
                        self.packets_sent,
                        self.send_errors,
                    )
                    self.udp_sock.sendto(status, addr)

            except OSError:
                await asyncio.sleep_ms(1)
            except Exception as e:
                print(f"Handler error: {e}")
                await asyncio.sleep_ms(10)


async def performance_monitor(handler):
    """Performance monitoring"""
    await asyncio.sleep(3)

    while True:
        await asyncio.sleep(5)

        if handler.sampling_active:
            rate = handler.samples_generated / 5
            pkt_rate = handler.packets_sent / 5

            print(
                f"NATIVE PERF: {rate:.1f} Hz, {pkt_rate:.1f} pkt/s, {handler.send_errors} errors"
            )

            if rate >= 100:
                print("EXCELLENT: 100+ Hz achieved!")
            elif rate >= 50:
                print("SUCCESS: 50+ Hz achieved!")
            else:
                print("Still below target...")

            # Reset counters
            handler.samples_generated = 0
            handler.packets_sent = 0
            handler.send_errors = 0


async def main():
    """Main loop with native driver"""

    print("Setting up WiFi AP...")
    if not WiFiConnection.start_ap_mode():
        raise RuntimeError("WiFi AP failed")

    print("WiFi AP ready at 192.168.4.1")

    # Test native sensor
    print("Initializing native ICM20948...")
    sensor = FastICM20948(i2c)

    # Speed test
    print("Testing native sensor speed...")
    start_time = time.ticks_ms()
    count = 0
    while time.ticks_diff(time.ticks_ms(), start_time) < 3000:
        accel = sensor.read_acceleration_fast()
        if accel:
            count += 1

    duration = time.ticks_diff(time.ticks_ms(), start_time)
    native_rate = count * 1000 / duration
    print(f"Native sensor rate: {native_rate:.1f} Hz ({count} reads in {duration}ms)")

    if native_rate < 50:
        print("WARNING: Native driver still slow")
    else:
        print("SUCCESS: Native driver faster than Adafruit!")

    handler = HighSpeedUDPHandler(sensor, target_hz=200)

    # Start tasks
    asyncio.create_task(handler.handle_requests())
    asyncio.create_task(performance_monitor(handler))

    print("=== NATIVE HIGH-SPEED SYSTEM READY ===")
    print("Commands via UDP:")
    print("  b'START_HF' - Start native 100+ Hz sampling")
    print("  b'STOP_HF' - Stop sampling")
    print("  b'STATUS' - Get stats")
    print("=========================================")

    # Main loop
    while True:
        await asyncio.sleep(10)
        gc.collect()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Interrupted")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        machine.reset()
