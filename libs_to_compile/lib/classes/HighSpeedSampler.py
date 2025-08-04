import micropython
import struct
import time
from machine import Timer


class HighSpeedSampler:
    def __init__(self, sensor1, sensor2, mag_sensor=None):
        """
        HighSpeedSampler for dual sensor setup:
            - sensor1: Native ICM20948
            - sensor2: Adafruit LSM6DSOX
            - mag_sensor: LIS3MDL magnetometer (part of sensor2)
        """
        self.sensor1 = sensor1  # Native ICM20948
        self.sensor2 = sensor2  # Adafruit LSM6DSOX
        self.mag_sensor = mag_sensor  # Separate LIS3MDL

        # Sampling configuration
        self.target_hz = 50  # Default rate
        self.batch_size = 10

        # Sampling state
        self.sampling_active = False
        self.hardware_timer = Timer(-1)
        self.sample_buffer = []

        # Stats
        self.samples_generated = 0
        self.packets_sent = 0
        self.send_errors = 0

        # Callback for sending data
        self.send_callback = None

    def set_sampling_rate(self, hz: int) -> bool:
        """Set sampling rate: 25, 50, 100, 200 Hz"""
        if hz not in [25, 50, 100, 200]:
            return False

        was_active = self.sampling_active

        # Stop if running
        if self.sampling_active:
            self.stop_sampling()

        self.target_hz = hz

        # Restart if was active
        if was_active and self.send_callback:
            return self.start_sampling()

        return True

    def set_send_callback(self, callback):
        """Set callback function to send batch data"""
        self.send_callback = callback

    def start_sampling(self) -> bool:
        if not self.send_callback:
            return False

        # Force cleanup everything
        self.force_cleanup()

        # Wait for cleanup to complete
        time.sleep_ms(20)

        # Reset all stats for fresh start
        self.samples_generated = 0
        self.packets_sent = 0
        self.send_errors = 0
        self.sample_buffer.clear()

        self.sampling_active = True

        # Calculate timer period
        timer_period = 1000 // self.target_hz

        try:
            self.hardware_timer.init(
                period=timer_period, mode=Timer.PERIODIC, callback=self.timer_callback
            )
            # print(f"Sampling started: {self.target_hz} Hz ({timer_period}ms period)")
            return True
        except Exception as e:
            print(f"Timer init failed: {e}")
            self.sampling_active = False
            return False

    def force_cleanup(self):
        """Force cleanup of timer and state"""
        self.sampling_active = False

        # Multiple attempts to stop timer
        for _ in range(3):
            try:
                self.hardware_timer.deinit()
                break
            except:
                time.sleep_ms(5)

        # Clear buffer
        self.sample_buffer.clear()

    @micropython.native
    def timer_callback(self, timer):
        if not self.sampling_active or not self.send_callback:
            return

        try:
            # Read sensor1 (Native ICM20948)
            s1_accel = s1_gyro = s1_mag = None

            if self.sensor1:
                if hasattr(self.sensor1, "read_all_fast"):
                    s1_accel, s1_gyro, s1_mag = self.sensor1.read_all_fast()
                else:
                    s1_accel = self.sensor1.acceleration
                    s1_gyro = self.sensor1.gyro
                    s1_mag = self.sensor1.magnetic

            # Read sensor2 (Adafruit LSM6DSOX)
            s2_accel = s2_gyro = s2_mag = None

            if self.sensor2:
                s2_accel = self.sensor2.acceleration
                s2_gyro = self.sensor2.gyro

            # Read separate magnetometer
            if self.mag_sensor:
                s2_mag = self.mag_sensor.magnetic

            # Use default values if reads failed
            s1_accel = s1_accel or (0.0, 0.0, 0.0)
            s1_gyro = s1_gyro or (0.0, 0.0, 0.0)
            s1_mag = s1_mag or (0.0, 0.0, 0.0)
            s2_accel = s2_accel or (0.0, 0.0, 0.0)
            s2_gyro = s2_gyro or (0.0, 0.0, 0.0)
            s2_mag = s2_mag or (0.0, 0.0, 0.0)

            timestamp = time.ticks_ms()

            # Pack dual sensor data: timestamp + 18 floats (9 per sensor)
            sample = struct.pack(
                "<I18f",
                timestamp,
                s1_accel[0],
                s1_accel[1],
                s1_accel[2],
                s1_gyro[0],
                s1_gyro[1],
                s1_gyro[2],
                s1_mag[0],
                s1_mag[1],
                s1_mag[2],  # Sensor 1: 9 floats
                s2_accel[0],
                s2_accel[1],
                s2_accel[2],
                s2_gyro[0],
                s2_gyro[1],
                s2_gyro[2],
                s2_mag[0],
                s2_mag[1],
                s2_mag[2],  # Sensor 2: 9 floats
            )

            self.sample_buffer.append(sample)
            self.samples_generated += 1

            # Send batch when ready
            if len(self.sample_buffer) >= self.batch_size:
                self.send_batch()

        except Exception:
            self.send_errors += 1

    @micropython.native
    def send_batch(self):
        if not self.sample_buffer or not self.send_callback:
            return

        try:
            batch_count = len(self.sample_buffer)
            header = struct.pack("<HH", 0xBEEF, batch_count)
            batch_data = header + b"".join(self.sample_buffer)

            if self.send_callback(batch_data):
                self.packets_sent += 1
            else:
                self.send_errors += 1

            self.sample_buffer.clear()

        except Exception:
            self.send_errors += 1

    def stop_sampling(self):
        if not self.sampling_active:
            return

        # print(
        #     f"Stopping sampling (before): {self.samples_generated} samples, {self.packets_sent} packets"
        # )

        # Stop timer first
        self.force_cleanup()

        # Wait for final timer callbacks to complete
        time.sleep_ms(50)

        # Send remaining samples
        if self.sample_buffer:
            self.send_batch()

        # print(
        #     f"Sampling stopped: {self.samples_generated} samples, {self.packets_sent} packets"
        # )

    def get_stats(self):
        return {
            "active": self.sampling_active,
            "rate": self.target_hz,
            "samples": self.samples_generated,
            "packets": self.packets_sent,
            "errors": self.send_errors,
        }

    def reset_stats(self):
        """Reset all statistics counters"""
        self.samples_generated = 0
        self.packets_sent = 0
        self.send_errors = 0
