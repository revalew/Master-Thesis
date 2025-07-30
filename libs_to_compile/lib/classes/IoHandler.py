# Async OLED update
# import uasyncio as asyncio
import asyncio

# from time import sleep
import time

# class to handle the IO for the demo setup
# from machine import Pin, ADC
from board import GP6, GP7, GP8, GP9  # type: ignore
from busio import I2C

# try:
#     from typing import Tuple

# except ImportError:
#     pass

# Adafruit libraries for IMU 1
# import adafruit_lps2x # pressure n temp
from adafruit_icm20x import ICM20948, MagDataRate

# Adafruit libraries for IMU 2
from adafruit_lsm6ds.lsm6dsox import LSM6DSOX as LSM6DS
from adafruit_lsm6ds import Rate
from adafruit_lis3mdl import LIS3MDL, Rate as MagRate

# Adafruit library for UPS
from adafruit_ina219 import INA219

# Adafruit library for OLED
from adafruit_ssd1306 import SSD1306_I2C

# Class for handling the GPIO debounced input
from .DebouncedInput import DebouncedInput, Pin

########################################
# SENSOR FREQUENCY CONFIGURATION
########################################
# Import required enums
# from adafruit_icm20x import MagDataRate
# from adafruit_lsm6ds import Rate
# from adafruit_lis3mdl import Rate as MagRate


class IoHandler:
    # Initializing onboard LED and temperature sensor
    # onboard_led = Pin("LED", Pin.OUT, value=0)  # GPIO pin for onboard LED
    # led_state = 0

    ########################################
    # Button initialization
    ########################################
    # Buttons controlling the OLED through class properties
    screen_on: bool = False  # Flag for turning the screen on/off
    display_mode: int = 0  # 0 = IMU 1, 1 = IMU 2, 2 = only battery info

    btn1: DebouncedInput = DebouncedInput(
        pinNum=14,
        callback=lambda pin, pressed: IoHandler.toggle_screen(pin, pressed),  # type: ignore
        pinPull=Pin.PULL_UP,
        debounceMs=30,
        irqTrigger=Pin.IRQ_RISING | Pin.IRQ_FALLING,
    )
    btn2: DebouncedInput = DebouncedInput(
        pinNum=15,
        callback=lambda pin, pressed: IoHandler.change_display_mode(pin, pressed),  # type: ignore
        pinPull=Pin.PULL_UP,
        debounceMs=30,
        irqTrigger=Pin.IRQ_RISING | Pin.IRQ_FALLING,
    )

    ########################################
    # I2C initialization
    ########################################
    # default frequency is 100kHz (`frequency=100000`)
    i2c: I2C = I2C(scl=GP7, sda=GP6)  # I2C(SCL, SDA)
    # print(i2c.scan())

    # According to the SSD1306 datasheet, the minimum i2c clock cycle time is 2.5us. Therefore, the maximum i2c clock frequency is 400KHz. The i2c clock frequency used by this project is 400KHz.
    i2c_2: I2C = I2C(scl=GP9, sda=GP8, frequency=400000)  # I2C(SCL, SDA)

    """
    [28, 67, 92, 104, 106] == [0x1C, 0x43, 0x5C, 0x68, 0x6A]
    [28, 60, 67, 92, 104, 106] == [0x1C, 0x3C, 0x43, 0x5C, 0x68, 0x6A]
    0x3C        => SSD1306 OLED display
    0x1C, 0x6A  => Adafruit IMU
    0x43        => UPS-A
    0x5C, 0x68  => Waveshare IMU
    """
    ########################################
    # OLED initialization
    ########################################
    # OLED display
    oled: SSD1306_I2C = SSD1306_I2C(128, 64, i2c_2, addr=0x3C)
    oledContrast = 10
    oled.contrast(oledContrast)

    ########################################
    # IMU 1 - Waveshare
    ########################################
    # press_temp_wav = adafruit_lps2x.LPS22(i2c, 0x5C)
    imu_wav: ICM20948 = ICM20948(i2c, 0x68)

    # pressure_wav = 0.0
    # temp_wav = 0.0
    acceleration_wav: tuple[float, float, float] = (0.0, 0.0, 0.0)
    gyro_wav: tuple[float, float, float] = (0.0, 0.0, 0.0)
    magnetic_wav: tuple[float, float, float] = (0.0, 0.0, 0.0)

    ########################################
    # IMU 2 - Adafruit
    ########################################
    accel_gyro_ada: LSM6DS = LSM6DS(i2c)
    mag_ada: LIS3MDL = LIS3MDL(i2c)

    acceleration_ada: tuple[float, float, float] = (0.0, 0.0, 0.0)
    gyro_ada: tuple[float, float, float] = (0.0, 0.0, 0.0)
    magnetic_ada: tuple[float, float, float] = (0.0, 0.0, 0.0)

    ########################################
    # UPS - Waveshare
    ########################################
    ups: INA219 = INA219(i2c, 0x43)

    ups_voltage: float = 0.0  # voltage on V- (load side)
    ups_current_draw: float = 0.0  # current in A
    ups_battery_remaining: float = 0.0

    ########################################
    # Cache
    ########################################
    _last_sensor_read = 0.0
    # _sensor_cache_duration = 0.1  # 100ms cache = max 10Hz
    # _sensor_cache_duration = 0.04  # 40ms cache = max 25Hz
    # _sensor_cache_duration = 0.02  # 20ms cache = max 50Hz
    # _sensor_cache_duration = 0.01  # 10ms cache = max 100Hz
    _sensor_cache_duration = 0.005  # 5ms cache = max 200Hz
    # _sensor_cache_duration = 0.002  # 2ms = max 500Hz
    _cached_data = {
        "sensor1": {"accel": (0, 0, 0), "gyro": (0, 0, 0), "mag": (0, 0, 0)},
        "sensor2": {"accel": (0, 0, 0), "gyro": (0, 0, 0), "mag": (0, 0, 0)},
        "battery": {"percentage": 0, "voltage": 0, "current": 0},
    }

    def __init__(self) -> None:
        # get everything into a starting state
        # self.__class__.show_onboard_led()
        """
        Initializes the IoHandler class, setting up the I2C communication and
        preparing the display, IMUs, and UPS for data reading. This method
        prepares all components into a starting state.

        Args:
            self: The instance of the IoHandler class.

        Returns:
            None
        """
        pass

    @classmethod
    def set_sample_rate(cls, sample_rate: int = 50, print_config: bool = False) -> None:
        """
        FREQUENCY SUMMARY:

        100 Hz Option:
            - Waveshare:
                - Accel ~102 Hz,
                - Gyro 100 Hz,
                - Mag 100 Hz

            - Adafruit:
                - Accel 104 Hz,
                - Gyro 104 Hz,
                - Mag 80 Hz

        50 Hz Option:
            - Waveshare:
                - Accel ~49 Hz,
                - Gyro 50 Hz,
                - Mag 50 Hz

            - Adafruit:
                - Accel 52 Hz,
                - Gyro 52 Hz,
                - Mag 40 Hz

        Args:
            sample_rate (int): The sample rate to set for the IMUs.

        Returns:
            None
        """
        if sample_rate == 100:
            setting = "=== SENSOR FREQUENCIES SET TO ~100 Hz ==="

            # === WAVESHARE IMU (ICM20948) - 100 Hz for all sensors ===
            # Accelerometer: formula 1125/(1+divisor) = target_freq
            # For 100 Hz: divisor = 10 (gives 102.27 Hz)
            accelerometer_data_rate_divisor = 10  # ~102.27 Hz

            # Gyro: formula 1100/(1+divisor) = target_freq
            # For 100 Hz: divisor = 10 (gives exactly 100 Hz)
            gyro_data_rate_divisor = 10  # 100 Hz

            # Magnetometer: uses MagDataRate enum
            magnetometer_data_rate = MagDataRate.RATE_100HZ  # type: ignore # 100 Hz
            magnetometer_data_rate_str = "MagDataRate.RATE_100HZ"

            # === ADAFRUIT IMU (LSM6DSOX + LIS3MDL) - 104 Hz (closest to 100 Hz) ===
            accelerometer_data_rate = Rate.RATE_104_HZ  # type: ignore # 104 Hz
            gyro_data_rate = Rate.RATE_104_HZ  # type: ignore # 104 Hz
            accel_gyro_rate_str = "Rate.RATE_104_HZ"

            # Magnetometer LIS3MDL
            data_rate = MagRate.RATE_80_HZ  # type: ignore # 80 Hz (closest to 100 Hz)
            data_rate_str = "MagRate.RATE_80_HZ"

        elif sample_rate == 50:
            setting = "=== SENSOR FREQUENCIES SET TO ~50 Hz ==="

            # === WAVESHARE IMU (ICM20948) - 50 Hz for all sensors ===
            # Accelerometer: formula 1125/(1+divisor) = target_freq
            # For 50 Hz: divisor = 22 (gives 48.91 Hz)
            accelerometer_data_rate_divisor = 22  # ~48.91 Hz

            # Gyro: formula 1100/(1+divisor) = target_freq
            # For 50 Hz: divisor = 21 (gives 50 Hz)
            gyro_data_rate_divisor = 21  # 50 Hz

            # had to add the "return" clause
            # in the "adafruit_icm20x.py" file
            # in "magnetometer_data_rate" property
            # because it was missing :skull:
            # print(f"\nBefore:\nmagnetometer_data_rate: {cls.imu_wav.magnetometer_data_rate}")
            # print(f"MagDataRate.RATE_100HZ: {MagDataRate.RATE_100HZ}")
            # Magnetometer: uses MagDataRate enum
            magnetometer_data_rate = MagDataRate.RATE_50HZ  # type: ignore # 50 Hz
            # print(f"\nAfter:\nmagnetometer_data_rate: {cls.imu_wav.magnetometer_data_rate}")
            # print(f"MagDataRate.RATE_50HZ: {MagDataRate.RATE_50HZ}")
            magnetometer_data_rate_str = "MagDataRate.RATE_50HZ"

            # === ADAFRUIT IMU (LSM6DSOX + LIS3MDL) - 52 Hz (closest to 50 Hz) ===
            accelerometer_data_rate = Rate.RATE_52_HZ  # type: ignore # 52 Hz
            gyro_data_rate = Rate.RATE_52_HZ  # type: ignore # 52 Hz
            accel_gyro_rate_str = "Rate.RATE_52_HZ"

            # Magnetometer LIS3MDL
            data_rate = MagRate.RATE_40_HZ  # type: ignore # 40 Hz (closest to 50 Hz)
            data_rate_str = "MagRate.RATE_40_HZ"

        elif sample_rate == 10:
            setting = "=== SENSOR FREQUENCIES SET TO ~10 Hz ==="

            # === WAVESHARE IMU (ICM20948) - 10 Hz ===
            # Accelerometer: 1125/(1+divisor) = 10 -> divisor = 111.5 -> 111 (gives 10.045 Hz)
            accelerometer_data_rate_divisor = 111  # ~10.045 Hz

            # Gyro: 1100/(1+divisor) = 10 -> divisor = 109 (gives 10 Hz)
            gyro_data_rate_divisor = 109  # 10 Hz

            # Magnetometer
            magnetometer_data_rate = MagDataRate.RATE_10HZ  # type: ignore
            magnetometer_data_rate_str = "MagDataRate.RATE_10HZ"

            # === ADAFRUIT IMU - 12.5 Hz (closest to 10 Hz) ===
            accelerometer_data_rate = Rate.RATE_12_5_HZ  # type: ignore
            gyro_data_rate = Rate.RATE_12_5_HZ  # type: ignore
            accel_gyro_rate_str = "Rate.RATE_12_5_HZ"

            # Magnetometer LIS3MDL - 10 Hz exact match
            data_rate = MagRate.RATE_10_HZ  # type: ignore
            data_rate_str = "MagRate.RATE_10_HZ"

        elif sample_rate == 20:
            setting = "=== SENSOR FREQUENCIES SET TO ~20 Hz ==="

            # === WAVESHARE IMU (ICM20948) - 20 Hz ===
            # Accelerometer: 1125/(1+divisor) = 20 -> divisor = 55.25 -> 55 (gives 20.45 Hz)
            accelerometer_data_rate_divisor = 55  # ~20.45 Hz

            # Gyro: 1100/(1+divisor) = 20 -> divisor = 54 (gives 20.0 Hz)
            gyro_data_rate_divisor = 54  # 20 Hz

            # Magnetometer
            magnetometer_data_rate = MagDataRate.RATE_20HZ  # type: ignore
            magnetometer_data_rate_str = "MagDataRate.RATE_20HZ"

            # === ADAFRUIT IMU - 26 Hz (closest to 20 Hz) ===
            accelerometer_data_rate = Rate.RATE_26_HZ  # type: ignore
            gyro_data_rate = Rate.RATE_26_HZ  # type: ignore
            accel_gyro_rate_str = "Rate.RATE_26_HZ"

            # Magnetometer LIS3MDL - 20 Hz exact match
            data_rate = MagRate.RATE_20_HZ  # type: ignore
            data_rate_str = "MagRate.RATE_20_HZ"

        elif sample_rate == 200:
            setting = "=== SENSOR FREQUENCIES SET TO ~200 Hz ==="

            # === WAVESHARE IMU (ICM20948) - 200 Hz ===
            # Accelerometer: 1125/(1+divisor) = 200 -> divisor = 4.625 -> 5 (gives 187.5 Hz)
            accelerometer_data_rate_divisor = 5  # ~187.5 Hz

            # Gyro: 1100/(1+divisor) = 200 -> divisor = 4.5 -> 4 (gives 220 Hz)
            gyro_data_rate_divisor = 4  # 220 Hz

            # Magnetometer - max available is 100 Hz
            magnetometer_data_rate = MagDataRate.RATE_100HZ  # type: ignore
            magnetometer_data_rate_str = "MagDataRate.RATE_100HZ (MAX)"

            # === ADAFRUIT IMU - 208 Hz ===
            accelerometer_data_rate = Rate.RATE_208_HZ  # type: ignore
            gyro_data_rate = Rate.RATE_208_HZ  # type: ignore
            accel_gyro_rate_str = "Rate.RATE_208_HZ"

            # Magnetometer LIS3MDL - 155 Hz (highest practical)
            data_rate = MagRate.RATE_155_HZ  # type: ignore
            data_rate_str = "MagRate.RATE_155_HZ"

        elif sample_rate == 400:
            setting = "=== SENSOR FREQUENCIES SET TO ~400 Hz ==="

            # === WAVESHARE IMU (ICM20948) - 400 Hz ===
            # Accelerometer: 1125/(1+divisor) = 400 -> divisor = 1.8125 -> 2 (gives 375 Hz)
            accelerometer_data_rate_divisor = 2  # ~375 Hz

            # Gyro: 1100/(1+divisor) = 400 -> divisor = 1.75 -> 2 (gives 366.67 Hz)
            gyro_data_rate_divisor = 2  # 366.67 Hz

            # Magnetometer - max available is 100 Hz
            magnetometer_data_rate = MagDataRate.RATE_100HZ  # type: ignore
            magnetometer_data_rate_str = "MagDataRate.RATE_100HZ (MAX)"

            # === ADAFRUIT IMU - 416 Hz ===
            accelerometer_data_rate = Rate.RATE_416_HZ  # type: ignore
            gyro_data_rate = Rate.RATE_416_HZ  # type: ignore
            accel_gyro_rate_str = "Rate.RATE_416_HZ"

            # Magnetometer LIS3MDL - 300 Hz
            data_rate = MagRate.RATE_300_HZ  # type: ignore
            data_rate_str = "MagRate.RATE_300_HZ"

        elif sample_rate == 800:
            setting = "=== SENSOR FREQUENCIES SET TO ~800 Hz ==="

            # === WAVESHARE IMU (ICM20948) - 800 Hz ===
            # Accelerometer: 1125/(1+divisor) = 800 -> divisor = 0.41 -> 0 (gives 1125 Hz MAX)
            accelerometer_data_rate_divisor = 0  # 1125 Hz (MAX)

            # Gyro: 1100/(1+divisor) = 800 -> divisor = 0.375 -> 0 (gives 1100 Hz MAX)
            gyro_data_rate_divisor = 0  # 1100 Hz (MAX)

            # Magnetometer - max available is 100 Hz
            magnetometer_data_rate = MagDataRate.RATE_100HZ  # type: ignore
            magnetometer_data_rate_str = "MagDataRate.RATE_100HZ (MAX)"

            # === ADAFRUIT IMU - 833 Hz ===
            accelerometer_data_rate = Rate.RATE_833_HZ  # type: ignore
            gyro_data_rate = Rate.RATE_833_HZ  # type: ignore
            accel_gyro_rate_str = "Rate.RATE_833_HZ"

            # Magnetometer LIS3MDL - 560 Hz
            data_rate = MagRate.RATE_560_HZ  # type: ignore
            data_rate_str = "MagRate.RATE_560_HZ"

        elif sample_rate == 1000:
            setting = "=== SENSOR FREQUENCIES SET TO ~1000 Hz ==="

            # === WAVESHARE IMU (ICM20948) - MAX FREQUENCIES ===
            accelerometer_data_rate_divisor = 0  # 1125 Hz (MAX)
            gyro_data_rate_divisor = 0  # 1100 Hz (MAX)
            magnetometer_data_rate = MagDataRate.RATE_100HZ  # type: ignore
            magnetometer_data_rate_str = "MagDataRate.RATE_100HZ (MAX)"

            # === ADAFRUIT IMU - 1.66 kHz ===
            accelerometer_data_rate = Rate.RATE_1_66K_HZ  # type: ignore # 1666 Hz
            gyro_data_rate = Rate.RATE_1_66K_HZ  # type: ignore # 1666 Hz
            accel_gyro_rate_str = "Rate.RATE_1_66K_HZ"

            # Magnetometer LIS3MDL - 1000 Hz (MAX)
            data_rate = MagRate.RATE_1000_HZ  # type: ignore
            data_rate_str = "MagRate.RATE_1000_HZ"

        else:
            raise ValueError(f"Invalid sample rate: {sample_rate}")

        cls.imu_wav.accelerometer_data_rate_divisor = accelerometer_data_rate_divisor
        cls.imu_wav.gyro_data_rate_divisor = gyro_data_rate_divisor
        cls.imu_wav.magnetometer_data_rate = magnetometer_data_rate
        cls.accel_gyro_ada.accelerometer_data_rate = accelerometer_data_rate
        cls.accel_gyro_ada.gyro_data_rate = gyro_data_rate
        cls.mag_ada.data_rate = data_rate

        if print_config:
            print(setting)

            print("\n=== WAVESHARE IMU ===")
            print(f"accelerometer_data_rate: {cls.imu_wav.accelerometer_data_rate}")
            print(
                f"accelerometer_data_rate_divisor: {cls.imu_wav.accelerometer_data_rate_divisor}"
            )

            print(f"\ngyro_data_rate: {cls.imu_wav.gyro_data_rate}")
            print(f"gyro_data_rate_divisor: {cls.imu_wav.gyro_data_rate_divisor}")

            print(
                f"\nmagnetometer_data_rate: {cls.imu_wav.magnetometer_data_rate} ({magnetometer_data_rate_str})"
            )

            # print(f"\n_low_power: {cls.imu_wav._low_power}")

            print("\n=== ADAFRUIT IMU ===")

            print(
                f"accelerometer_data_rate: {cls.accel_gyro_ada.accelerometer_data_rate} ({accel_gyro_rate_str})"
            )

            print(
                f"\ngyro_data_rate: {cls.accel_gyro_ada.gyro_data_rate} ({accel_gyro_rate_str})"
            )

            print(
                f"\nmagnetometer_data_rate: {cls.mag_ada.data_rate} ({data_rate_str})"
            )
        
        ########################################
        # Print initialized text
        ########################################
        # print("IoHandler initialized")
        cls.oled.fill(0)  # Clear the display
        cls.oled.text("IoHandler", 0, 25)
        cls.oled.text("initialized...", 0, 35)
        cls.oled.show()
        time.sleep(2)
        cls.oled.poweroff()

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
        sleepTime = 0.5  # Repeat task every X seconds
        while True:
            if not cls.screen_on:  # If the screen is off display nothing
                await asyncio.sleep(1)
                continue

            cls.oled.fill(0)  # Clear the display

            if cls.display_mode == 0:  # Display IMU 1 (Waveshare)
                # Read data from IMU 1 (Waveshare)
                accel = cls.get_accel_reading("wav")
                gyro = cls.get_gyro_reading("wav")

                cls.oled.text("IMU 1 Waveshare", 0, 0)

                cls.oled.text("Accel (X Y Z):", 0, 20)
                cls.oled.text(
                    "{:.1f} {:.1f} {:.1f}".format(accel[0], accel[1], accel[2]), 0, 30
                )

                cls.oled.text("Gyro (X Y Z):", 0, 40)
                cls.oled.text(
                    "{:.1f} {:.1f} {:.1f}".format(gyro[0], gyro[1], gyro[2]), 0, 50
                )

                sleepTime = 0.5

            elif cls.display_mode == 1:  # Display IMU 2 (Adafruit)
                # Read data from IMU 2 (Adafruit)
                accel = cls.get_accel_reading("ada")
                gyro = cls.get_gyro_reading("ada")

                cls.oled.text("IMU 2 Adafruit", 0, 0)

                cls.oled.text("Accel (X Y Z):", 0, 20)
                cls.oled.text(
                    "{:.1f} {:.1f} {:.1f}".format(accel[0], accel[1], accel[2]), 0, 30
                )

                cls.oled.text("Gyro (X Y Z):", 0, 40)
                cls.oled.text(
                    "{:.1f} {:.1f} {:.1f}".format(gyro[0], gyro[1], gyro[2]), 0, 50
                )

                sleepTime = 0.5

            else:  # `display_mode == 2` - Display battery info
                # Read data from UPS (Waveshare)
                battery_percentage, battery_voltage = cls.get_ups_battery_reading()
                battery_current = cls.get_ups_current_reading()

                cls.oled.text("Battery Info", 0, 0)
                cls.oled.text("{:.1f}%".format(battery_percentage), 0, 20)
                cls.oled.text("Load:", 0, 40)
                cls.oled.text(
                    "{:.2f}V, {:.2f}A".format(battery_voltage, battery_current), 0, 50
                )

                sleepTime = 5

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
            # print(f"Button {pin} pressed")
            cls.screen_on = not cls.screen_on

            # print(f"cls.screen_on: {cls.screen_on}")

            if not cls.screen_on:
                # print("OFF")
                cls.oled.poweroff()

            else:
                # print("ON")
                cls.oled.poweron()
                cls.oled.contrast(cls.oledContrast)

    @classmethod
    def change_display_mode(cls, pin: Pin, pressed: bool) -> None:
        """
        Called when the button is pressed, changes the display mode (IMU 1 → IMU 2 → Battery)

        Args:
            pin (Pin): The pin that was pressed
            pressed (bool): Whether the button was pressed

        Returns:
            None
        """
        if pressed:
            # print(f"Button {pin} pressed")
            cls.display_mode = (cls.display_mode + 1) % 3  # Cycle: 0 → 1 → 2 → 0 → ...

            # print(f"cls.display_mode: {cls.display_mode}")

    @classmethod
    def get_all_sensor_data_direct(cls):
        """Direct sensor reads, minimal function calls"""
        wav_a_1, wav_a_2, wav_a_3 = cls.imu_wav.acceleration
        wav_g_1, wav_g_2, wav_g_3 = cls.imu_wav.gyro
        wav_m_1, wav_m_2, wav_m_3 = cls.imu_wav.magnetic

        ada_a_1, ada_a_2, ada_a_3 = cls.accel_gyro_ada.acceleration
        ada_g_1, ada_g_2, ada_g_3 = cls.accel_gyro_ada.gyro
        ada_m_1, ada_m_2, ada_m_3 = cls.mag_ada.magnetic

        ups_voltage = cls.ups.bus_voltage
        ups_current = cls.ups.current / 1000 if cls.ups.current >= 0 else 0.0
        ups_percentage = max(0.0, min(100.0, (ups_voltage - 3) / 1.18 * 100))

        return (
            wav_a_1,
            wav_a_2,
            wav_a_3,
            wav_g_1,
            wav_g_2,
            wav_g_3,
            wav_m_1,
            wav_m_2,
            wav_m_3,
            ada_a_1,
            ada_a_2,
            ada_a_3,
            ada_g_1,
            ada_g_2,
            ada_g_3,
            ada_m_1,
            ada_m_2,
            ada_m_3,
            ups_voltage,
            ups_current,
            ups_percentage,
        )

    @classmethod
    def get_all_sensor_data_cached(cls):
        """Get all sensor data with caching for better performance"""
        current_time = time.time()

        # Check if cache is still valid
        if (current_time - cls._last_sensor_read) < cls._sensor_cache_duration:
            return cls._cached_data

        # Update cache
        try:
            # Read all sensors
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

            cls._last_sensor_read = current_time

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
            tuple[float, float, float] The acceleration reading as a tuple of (x, y, z) in m/s^2

        Raises:
            ValueError: If `imu` is not "wav" or "ada"
        """
        if imu == "wav":
            cls.acceleration_wav = cls.imu_wav.acceleration
            # print("Acceleration: X:%.2f, Y: %.2f, Z: %.2f m/s^2" % (cls.acceleration_wav))
            return cls.acceleration_wav

        elif imu == "ada":
            cls.acceleration_ada = cls.accel_gyro_ada.acceleration
            # print("Acceleration: X:{0:7.2f}, Y:{1:7.2f}, Z:{2:7.2f} m/s^2".format(*cls.acceleration_ada))
            return cls.acceleration_ada

        else:
            raise ValueError(f"Invalid IMU: {imu}")

    @classmethod
    def get_gyro_reading(cls, imu: str) -> tuple[float, float, float]:
        """
        Returns the gyroscope reading of the specified IMU

        Args:
            imu (str): The IMU to read from. Must be either "wav" or "ada"

        Returns:
            tuple[float, float, float] The gyroscope reading as a tuple of (x, y, z) in rads/s

        Raises:
            ValueError: If `imu` is not "wav" or "ada"
        """
        if imu == "wav":
            cls.gyro_wav = cls.imu_wav.gyro
            # print("Gyro X:%.2f, Y: %.2f, Z: %.2f rads/s" % (cls.gyro_wav))
            return cls.gyro_wav

        elif imu == "ada":
            cls.gyro_ada = cls.accel_gyro_ada.gyro
            # print(
            #     "Gyro          X:{0:7.2f}, Y:{1:7.2f}, Z:{2:7.2f} rad/s".format(*cls.gyro_ada)
            # )
            return cls.gyro_ada

        else:
            raise ValueError(f"Invalid IMU: {imu}")

    @classmethod
    def get_magnetic_reading(cls, imu: str) -> tuple[float, float, float]:
        """
        Returns the magnetometer reading of the specified IMU

        Args:
            imu (str): The IMU to read from. Must be either "wav" or "ada"

        Returns:
            tuple[float, float, float] The magnetometer reading as a tuple of (x, y, z) in uT

        Raises:
            ValueError: If `imu` is not "wav" or "ada"
        """
        if imu == "wav":
            cls.magnetic_wav = cls.imu_wav.magnetic
            # print("Magnetometer X:%.2f, Y: %.2f, Z: %.2f uT" % (cls.magnetic_wav))
            return cls.magnetic_wav

        elif imu == "ada":
            cls.magnetic_ada = cls.mag_ada.magnetic
            # print(
            #     "Magnetic      X:{0:7.2f}, Y:{1:7.2f}, Z:{2:7.2f} uT".format(*cls.magnetic_ada)
            # )
            return cls.magnetic_ada

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
        cls.ups_current_draw = (
            cls.ups.current
        ) / 1000  # (current in mA) / 1000 = current in A

        if cls.ups_current_draw < 0:
            cls.ups_current_draw = 0

        # print("Current:  {:6.3f} A".format(cls.ups_current_draw))
        return cls.ups_current_draw

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
            tuple[float, float] A tuple containing the current battery percentage and voltage
        """
        # INA219 measure bus voltage on the load side. So PSU voltage = bus_voltage + shunt_voltage
        cls.ups_voltage = cls.ups.bus_voltage  # voltage on V- (load side)
        # print("Voltage:  {:6.3f} V".format(cls.ups_voltage))

        cls.ups_battery_remaining = (cls.ups_voltage - 3) / 1.18 * 100

        if cls.ups_battery_remaining < 0:
            cls.ups_battery_remaining = 0

        elif cls.ups_battery_remaining > 100:
            cls.ups_battery_remaining = 100

        # print("Percent:  {:6.1f} %".format(cls.ups_battery_remaining))
        return (cls.ups_battery_remaining, cls.ups_voltage)

    """
    # onboard_led handlers
    @classmethod
    def show_onboard_led(cls) -> None:
        cls.onboard_led.value(cls.led_state)

    @classmethod
    def toggle_onboard_led(cls) -> None:
        cls.led_state = 0 if cls.led_state == 1 else 1
        cls.show_onboard_led()

    @classmethod
    def get_onboard_led(cls) -> int:
        return 0 if cls.led_state == 0 else 1

    @classmethod
    def set_onboard_led(cls, state: int) -> None:
        cls.led_state = 0 if state == 0 else 1
        cls.show_onboard_led()

    # temp handler
    @classmethod
    def get_temp_reading(cls) -> float:
        temp_voltage = cls.temp.read_u16() * (3.3 / 65535)
        cls.temp_value = 27 - (temp_voltage - 0.706) / 0.001721
        return cls.temp_value
    """
    """
    # Waveshare pressure handler
    @classmethod
    def get_pressure_wav_reading(cls) -> float:
        cls.pressure_wav = cls.press_temp_wav.pressure
        # print("Pressure: %.2f hPa" % cls.pressure_wav)
        return cls.pressure_wav

    # Waveshare temperature handler
    @classmethod
    def get_temp_wav_reading(cls) -> float:
        cls.temp_wav = cls.press_temp_wav.temperature
        # print("Temperature: %.2f C" % cls.temp_wav)
        return cls.temp_wav
    """
