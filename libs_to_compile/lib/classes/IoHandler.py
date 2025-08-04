import asyncio
import time
from machine import I2C, Pin

from board import GP6, GP7, GP8, GP9
from busio import I2C as BusIO_I2C

# Standard Adafruit libraries for IMU 2
from adafruit_lsm6ds.lsm6dsox import LSM6DSOX as LSM6DS
from adafruit_lsm6ds import Rate
from adafruit_lis3mdl import LIS3MDL, Rate as MagRate

# Native driver and high-speed sampler
from .NativeICM20948 import NativeICM20948
from .HighSpeedSampler import HighSpeedSampler

# Other components
from adafruit_ina219 import INA219
from adafruit_ssd1306 import SSD1306_I2C
from .DebouncedInput import DebouncedInput


class IoHandler:
    # ========================================
    # SENSOR INTERNAL RATES CONFIGURATION
    # ========================================
    ACCEL_ADA_HZ = 416  # LSM6DSOX Accelerometer (Hz)
    GYRO_ADA_HZ = 416  # LSM6DSOX Gyroscope (Hz)
    MAG_ADA_HZ = 300  # LIS3MDL Magnetometer (Hz)

    ACCEL_WAV_HZ = 400  # ICM20948 Accelerometer (Hz)
    GYRO_WAV_HZ = 400  # ICM20948 Gyroscope (Hz)
    MAG_WAV_HZ = 100  # AK09916 Magnetometer (Hz) - max 100Hz
    # ========================================
    """
    [28, 67, 92, 104, 106] == [0x1C, 0x43, 0x5C, 0x68, 0x6A]
    [28, 60, 67, 92, 104, 106] == [0x1C, 0x3C, 0x43, 0x5C, 0x68, 0x6A]
    0x3C        => SSD1306 OLED display
    0x1C, 0x6A  => Adafruit IMU
    0x43        => UPS-A
    0x5C, 0x68  => Waveshare IMU
    """

    # Screen control
    screen_on: bool = False
    display_mode: int = 0

    # Button initialization
    btn1: DebouncedInput = DebouncedInput(
        pinNum=14,
        callback=lambda pin, pressed: IoHandler.toggle_screen(pin, pressed),
        pinPull=Pin.PULL_UP,
        debounceMs=30,
        irqTrigger=Pin.IRQ_RISING | Pin.IRQ_FALLING,
    )
    btn2: DebouncedInput = DebouncedInput(
        pinNum=15,
        callback=lambda pin, pressed: IoHandler.change_display_mode(pin, pressed),
        pinPull=Pin.PULL_UP,
        debounceMs=30,
        irqTrigger=Pin.IRQ_RISING | Pin.IRQ_FALLING,
    )

    # I2C setup
    i2c: BusIO_I2C = BusIO_I2C(scl=GP7, sda=GP6)
    i2c_2: BusIO_I2C = BusIO_I2C(scl=GP9, sda=GP8, frequency=400000)

    # Native I2C for high-speed sensors
    native_i2c: I2C = I2C(1, scl=Pin(7), sda=Pin(6), freq=1000000)

    # OLED display
    oled: SSD1306_I2C = SSD1306_I2C(128, 64, i2c_2, addr=0x3C)
    oledContrast = 10

    # IMU 1 - Native Waveshare (high-speed) - Initialize early
    accel_div = max(0, round(1125 / ACCEL_WAV_HZ - 1))
    gyro_div = max(0, round(1100 / GYRO_WAV_HZ - 1))

    imu_wav_native = NativeICM20948(native_i2c, 0x68, accel_div, gyro_div)

    del accel_div, gyro_div

    # IMU 2 - Adafruit
    accel_gyro_ada: LSM6DS = LSM6DS(i2c)
    mag_ada: LIS3MDL = LIS3MDL(i2c)

    # UPS
    ups: INA219 = INA219(i2c, 0x43)

    # High-speed sampling system
    high_speed_sampler: HighSpeedSampler | None = None

    # Cache
    _cached_data = {
        "sensor1": {"accel": (0, 0, 0), "gyro": (0, 0, 0), "mag": (0, 0, 0)},
        "sensor2": {"accel": (0, 0, 0), "gyro": (0, 0, 0), "mag": (0, 0, 0)},
        "battery": {"percentage": 0, "voltage": 0, "current": 0},
    }

    def __init__(self) -> None:
        pass

    @classmethod
    def _get_ada_accel_rate(cls, target_hz):
        """Map target Hz to closest LSM6DSOX Rate enum"""
        rate_map = {
            12: Rate.RATE_12_5_HZ,
            26: Rate.RATE_26_HZ,
            52: Rate.RATE_52_HZ,
            104: Rate.RATE_104_HZ,
            208: Rate.RATE_208_HZ,
            416: Rate.RATE_416_HZ,
            833: Rate.RATE_833_HZ,
            1666: Rate.RATE_1_66K_HZ,
            3330: Rate.RATE_3_33K_HZ,
            6660: Rate.RATE_6_66K_HZ,
        }
        closest = min(rate_map.keys(), key=lambda x: abs(x - target_hz))
        return rate_map[closest], closest

    @classmethod
    def _get_ada_mag_rate(cls, target_hz):
        """Map target Hz to closest LIS3MDL Rate enum"""
        rate_map = {
            0: MagRate.RATE_0_625_HZ,
            1: MagRate.RATE_1_25_HZ,
            2: MagRate.RATE_2_5_HZ,
            5: MagRate.RATE_5_HZ,
            10: MagRate.RATE_10_HZ,
            20: MagRate.RATE_20_HZ,
            40: MagRate.RATE_40_HZ,
            80: MagRate.RATE_80_HZ,
            155: MagRate.RATE_155_HZ,
            300: MagRate.RATE_300_HZ,
            560: MagRate.RATE_560_HZ,
            1000: MagRate.RATE_1000_HZ,
        }
        closest = min(rate_map.keys(), key=lambda x: abs(x - target_hz))
        return rate_map[closest], closest

    @classmethod
    def initialize_high_speed_system(cls):
        """Initialize high-speed sampling system with configured sensor rates"""

        # Configure Adafruit sensors
        ada_accel_rate, ada_accel_actual = cls._get_ada_accel_rate(cls.ACCEL_ADA_HZ)
        ada_gyro_rate, ada_gyro_actual = cls._get_ada_accel_rate(cls.GYRO_ADA_HZ)
        ada_mag_rate, ada_mag_actual = cls._get_ada_mag_rate(cls.MAG_ADA_HZ)

        cls.accel_gyro_ada.accelerometer_data_rate = ada_accel_rate
        cls.accel_gyro_ada.gyro_data_rate = ada_gyro_rate
        cls.mag_ada.data_rate = ada_mag_rate

        # Reinitialize ICM20948 for fresh start
        accel_div = max(0, round(1125 / cls.ACCEL_WAV_HZ - 1))
        gyro_div = max(0, round(1100 / cls.GYRO_WAV_HZ - 1))

        # try:
        #     cls.imu_wav_native = NativeICM20948(
        #         cls.native_i2c, 0x68, accel_div, gyro_div
        #     )
        # except Exception as e:
        #     print(f"ICM20948 reinit failed: {e}")
        #     cls.imu_wav_native = None

        # Force recreate sampler for clean state
        cls.high_speed_sampler = HighSpeedSampler(
            cls.imu_wav_native, cls.accel_gyro_ada, cls.mag_ada
        )

        cls.oled.contrast(cls.oledContrast)
        cls.oled.fill(0)
        cls.oled.text("High-speed system", 0, 20)
        cls.oled.text("initialized", 20, 35)
        cls.oled.show()
        time.sleep(2)
        cls.oled.poweroff()

        # Calculate actual rates for ICM20948
        accel_actual = 1125 / (1 + accel_div) if cls.imu_wav_native else 0
        gyro_actual = 1100 / (1 + gyro_div) if cls.imu_wav_native else 0

        # print(f"=== SENSOR INTERNAL RATES ===")
        # if cls.imu_wav_native:
        #     print(
        #         f"ICM20948: Accel {accel_actual:.1f} Hz, Gyro {gyro_actual:.1f} Hz, Mag {cls.MAG_WAV_HZ} Hz"
        #     )
        # else:
        #     print("ICM20948: FAILED TO INITIALIZE")
        # print(f"LSM6DSOX: Accel {ada_accel_actual} Hz, Gyro {ada_gyro_actual} Hz")
        # print(f"LIS3MDL:  Mag {ada_mag_actual} Hz")

    @classmethod
    def set_sampling_rate(cls, hz: int) -> bool:
        """Set sampling rate: 25, 50, 100, 200 Hz"""
        if not cls.high_speed_sampler:
            cls.initialize_high_speed_system()

        return cls.high_speed_sampler.set_sampling_rate(hz)

    @classmethod
    def start_high_speed_sampling(cls, send_callback) -> bool:
        """Start high-speed sampling with callback for data sending"""
        if not cls.high_speed_sampler:
            cls.initialize_high_speed_system()

        cls.high_speed_sampler.set_send_callback(send_callback)
        return cls.high_speed_sampler.start_sampling()

    @classmethod
    def stop_high_speed_sampling(cls):
        """Stop high-speed sampling"""
        if cls.high_speed_sampler:
            cls.high_speed_sampler.stop_sampling()

    @classmethod
    def get_sampling_stats(cls):
        """Get high-speed sampling statistics"""
        if cls.high_speed_sampler:
            return cls.high_speed_sampler.get_stats()
        return {"active": False, "rate": 0, "samples": 0, "packets": 0, "errors": 0}

    @classmethod
    async def update_oled(cls) -> None:
        """
        Updates the OLED display with the selected data every 0.5 seconds. If screen_on is False, nothing is displayed.

        The display mode is cycled through with the two buttons on the board. The display mode is as follows:
        0 - Display IMU 1 (Waveshare) data
        1 - Display IMU 2 (Adafruit) data
        2 - Display battery info from UPS (Waveshare)

        Data is cleared from the display before being written again, so there is no need to clear the display manually.

        Args:
            None

        Returns:
            None
        """
        cls.oled.fill(0)
        cls.oled.text("IoHandler", 0, 25)
        cls.oled.text("initialized...", 0, 35)
        cls.oled.show()
        await asyncio.sleep(2)
        cls.oled.poweroff()

        sleepTime = 0.5
        while True:
            if not cls.screen_on:
                await asyncio.sleep(1)
                continue

            cls.oled.fill(0)

            if cls.display_mode == 0:  # Waveshare IMU
                accel = cls.get_accel_reading("wav")
                gyro = cls.get_gyro_reading("wav")

                cls.oled.text("IMU Waveshare", 0, 0)
                cls.oled.text("Accel (X Y Z):", 0, 20)
                cls.oled.text(
                    "{:.1f} {:.1f} {:.1f}".format(accel[0], accel[1], accel[2]), 0, 30
                )
                cls.oled.text("Gyro (X Y Z):", 0, 40)
                cls.oled.text(
                    "{:.1f} {:.1f} {:.1f}".format(gyro[0], gyro[1], gyro[2]), 0, 50
                )
                sleepTime = 0.5

            elif cls.display_mode == 1:  # Adafruit IMU
                accel = cls.get_accel_reading("ada")
                gyro = cls.get_gyro_reading("ada")

                cls.oled.text("IMU Adafruit", 0, 0)
                cls.oled.text("Accel (X Y Z):", 0, 20)
                cls.oled.text(
                    "{:.1f} {:.1f} {:.1f}".format(accel[0], accel[1], accel[2]), 0, 30
                )
                cls.oled.text("Gyro (X Y Z):", 0, 40)
                cls.oled.text(
                    "{:.1f} {:.1f} {:.1f}".format(gyro[0], gyro[1], gyro[2]), 0, 50
                )
                sleepTime = 0.5

            else:  # System Status
                battery_percentage, battery_voltage = cls.get_ups_battery_reading()
                battery_current = cls.get_ups_current_reading()

                cls.oled.text("System Status", 0, 0)
                cls.oled.text("{:.1f}%".format(battery_percentage), 0, 15)
                cls.oled.text(
                    "{:.2f}V {:.2f}A".format(battery_voltage, battery_current), 0, 25
                )

                stats = cls.get_sampling_stats()
                if stats["active"]:
                    cls.oled.text(f"Sampling: {stats['rate']}Hz", 0, 40)
                else:
                    cls.oled.text("Sampling: OFF", 0, 40)

                sleepTime = 2

            cls.oled.show()
            await asyncio.sleep(sleepTime)

    @classmethod
    def toggle_screen(cls, pin: Pin, pressed: bool) -> None:
        """
        Called when the button is pressed, turning the OLED screen on/off

        Args:
            pin (Pin): The pin that was pressed
            pressed (bool): Whether the button was pressed

        Returns:
            None
        """
        if pressed:
            cls.screen_on = not cls.screen_on
            if not cls.screen_on:
                cls.oled.poweroff()
            else:
                cls.oled.poweron()
                cls.oled.contrast(cls.oledContrast)

    @classmethod
    def change_display_mode(cls, pin: Pin, pressed: bool) -> None:
        """
        Called when the button is pressed, changes the display mode (IMU 1 -> IMU 2 -> Battery)

        Args:
            pin (Pin): The pin that was pressed
            pressed (bool): Whether the button was pressed

        Returns:
            None
        """
        if pressed:
            cls.display_mode = (cls.display_mode + 1) % 3

    @classmethod
    def get_all_sensor_data_direct(cls):
        """Direct sensor reads for maximum speed"""
        wav_a = wav_g = wav_m = (0.0, 0.0, 0.0)
        ada_a = ada_g = ada_m = (0.0, 0.0, 0.0)

        if cls.imu_wav_native:
            try:
                if hasattr(cls.imu_wav_native, "read_all_fast"):
                    wav_all = cls.imu_wav_native.read_all_fast()
                    wav_a, wav_g, wav_m = (
                        wav_all[0] or (0, 0, 0),
                        wav_all[1] or (0, 0, 0),
                        wav_all[2] or (0, 0, 0),
                    )
                else:
                    wav_a = cls.imu_wav_native.acceleration or (0, 0, 0)
                    wav_g = cls.imu_wav_native.gyro or (0, 0, 0)
                    wav_m = cls.imu_wav_native.magnetic or (0, 0, 0)
            except:
                pass

        try:
            ada_a = cls.accel_gyro_ada.acceleration
            ada_g = cls.accel_gyro_ada.gyro
            ada_m = cls.mag_ada.magnetic
        except:
            pass

        try:
            ups_voltage = cls.ups.bus_voltage
            ups_current = cls.ups.current / 1000 if cls.ups.current >= 0 else 0.0
            ups_percentage = max(0.0, min(100.0, (ups_voltage - 3) / 1.18 * 100))
        except:
            ups_voltage = ups_current = ups_percentage = 0.0

        return (
            wav_a[0],
            wav_a[1],
            wav_a[2],
            wav_g[0],
            wav_g[1],
            wav_g[2],
            wav_m[0],
            wav_m[1],
            wav_m[2],  # 9 values from native sensor
            ada_a[0],
            ada_a[1],
            ada_a[2],
            ada_g[0],
            ada_g[1],
            ada_g[2],
            ada_m[0],
            ada_m[1],
            ada_m[2],  # 9 values from adafruit sensor
            ups_voltage,
            ups_current,
            ups_percentage,  # 3 battery values
        )

    @classmethod
    def get_all_sensor_data(cls):
        """Standard cached data for web API"""
        try:
            cls._cached_data["sensor1"]["accel"] = cls.get_accel_reading("wav")
            cls._cached_data["sensor1"]["gyro"] = cls.get_gyro_reading("wav")
            cls._cached_data["sensor1"]["mag"] = cls.get_magnetic_reading("wav")

            cls._cached_data["sensor2"]["accel"] = cls.get_accel_reading("ada")
            cls._cached_data["sensor2"]["gyro"] = cls.get_gyro_reading("ada")
            cls._cached_data["sensor2"]["mag"] = cls.get_magnetic_reading("ada")

            battery_percentage, battery_voltage = cls.get_ups_battery_reading()
            battery_current = cls.get_ups_current_reading()

            cls._cached_data["battery"]["percentage"] = battery_percentage
            cls._cached_data["battery"]["voltage"] = battery_voltage
            cls._cached_data["battery"]["current"] = battery_current

        except Exception as e:
            print(f"Sensor read error: {e}")

        return cls._cached_data

    @classmethod
    def get_accel_reading(cls, imu: str) -> tuple[float, float, float]:
        """
        Returns the acceleration reading of the specified IMU

        Args:
            imu (str): The IMU to read from. Must be either "wav" or "ada"

        Returns:
            tuple: The acceleration reading as a tuple of (x, y, z) in m/s^2

        Raises:
            ValueError: If `imu` is not "wav" or "ada"
        """
        if imu == "wav":
            if cls.imu_wav_native:
                return cls.imu_wav_native.acceleration or (0, 0, 0)
            return (0, 0, 0)
        elif imu == "ada":
            try:
                return cls.accel_gyro_ada.acceleration
            except:
                return (0, 0, 0)
        else:
            raise ValueError(f"Invalid IMU: {imu}")

    @classmethod
    def get_gyro_reading(cls, imu: str) -> tuple[float, float, float]:
        """
        Returns the gyroscope reading of the specified IMU

        Args:
            imu (str): The IMU to read from. Must be either "wav" or "ada"

        Returns:
            tuple: The gyroscope reading as a tuple of (x, y, z) in rads/s

        Raises:
            ValueError: If `imu` is not "wav" or "ada"
        """
        if imu == "wav":
            if cls.imu_wav_native:
                return cls.imu_wav_native.gyro or (0, 0, 0)
            return (0, 0, 0)
        elif imu == "ada":
            try:
                return cls.accel_gyro_ada.gyro
            except:
                return (0, 0, 0)
        else:
            raise ValueError(f"Invalid IMU: {imu}")

    @classmethod
    def get_magnetic_reading(cls, imu: str) -> tuple[float, float, float]:
        """
        Returns the magnetometer reading of the specified IMU

        Args:
            imu (str): The IMU to read from. Must be either "wav" or "ada"

        Returns:
            tuple: The magnetometer reading as a tuple of (x, y, z) in uT

        Raises:
            ValueError: If `imu` is not "wav" or "ada"
        """
        if imu == "wav":
            if cls.imu_wav_native:
                return cls.imu_wav_native.magnetic or (0, 0, 0)
            return (0, 0, 0)
        elif imu == "ada":
            try:
                return cls.mag_ada.magnetic
            except:
                return (0, 0, 0)
        else:
            raise ValueError(f"Invalid IMU: {imu}")

    @classmethod
    def get_ups_current_reading(cls) -> float:
        """
        Returns the current draw of the device in Amperes (A) as a float.

        The current is read from the Waveshare UPS board and converted from milliamps (mA) to Amperes (A) for convenience.

        Args:
            None

        Returns:
            float: The current draw in Amperes (A)
        """
        try:
            current = cls.ups.current / 1000
            return current if current >= 0 else 0.0
        except:
            return 0.0

    @classmethod
    def get_ups_battery_reading(cls) -> tuple[float, float]:
        """
        Returns the current battery percentage and voltage of the Waveshare UPS board

        The battery percentage is calculated based on the voltage reading from the INA219
        on the UPS board. The calculation is as follows:

        battery_percentage = (voltage - 3) / 1.18 * 100

        The range of the calculation is from 0% to 100%.

        The voltage is also returned as a float in Volts (V)

        Args:
            None

        Returns:
            tuple: A tuple containing the current battery percentage and voltage
        """
        try:
            # INA219 measure bus voltage on the load side. So PSU voltage = bus_voltage + shunt_voltage
            voltage = cls.ups.bus_voltage
            percentage = (voltage - 3) / 1.18 * 100
            percentage = max(0.0, min(100.0, percentage))
            return (percentage, voltage)
        except:
            return (0.0, 0.0)
