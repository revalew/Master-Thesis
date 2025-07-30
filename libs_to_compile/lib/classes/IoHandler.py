# Async OLED update
# import uasyncio as asyncio
import asyncio

# from time import sleep
import time

# class to handle the IO for the demo setup
# from machine import Pin, ADC
from board import GP6, GP7, GP8, GP9
from busio import I2C

# try:
#     from typing import Tuple

# except ImportError:
#     pass

# Adafruit libraries for IMU 1
# import adafruit_lps2x # pressure n temp
from adafruit_icm20x import ICM20948

# Adafruit libraries for IMU 2
from adafruit_lsm6ds.lsm6dsox import LSM6DSOX as LSM6DS
from adafruit_lis3mdl import LIS3MDL

# Adafruit library for UPS
from adafruit_ina219 import INA219

# Adafruit library for OLED
from adafruit_ssd1306 import SSD1306_I2C

# Class for handling the GPIO debounced input
from .DebouncedInput import DebouncedInput, Pin


class IoHandler:
    # Initializing onboard LED and temperature sensor
    # onboard_led = Pin("LED", Pin.OUT, value=0)  # GPIO pin for onboard LED
    # led_state = 0

    # Buttons controlling the OLED through class properties
    screen_on: bool = False  # Flag for turning the screen on/off
    display_mode: int = 0  # 0 = IMU 1, 1 = IMU 2, 2 = only battery info

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

    # I2C initialization
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
    # OLED display
    oled: SSD1306_I2C = SSD1306_I2C(128, 64, i2c_2, addr=0x3C)
    oledContrast = 10
    oled.contrast(oledContrast)

    # IMU 1 - Waveshare
    # press_temp_wav = adafruit_lps2x.LPS22(i2c, 0x5C)
    imu_wav: ICM20948 = ICM20948(i2c, 0x68)

    # pressure_wav = 0.0
    # temp_wav = 0.0
    acceleration_wav: tuple[float, float, float] = (0.0, 0.0, 0.0)
    gyro_wav: tuple[float, float, float] = (0.0, 0.0, 0.0)
    magnetic_wav: tuple[float, float, float] = (0.0, 0.0, 0.0)

    # IMU 2 - Adafruit
    accel_gyro_ada: LSM6DS = LSM6DS(i2c)
    mag_ada: LIS3MDL = LIS3MDL(i2c)

    acceleration_ada: tuple[float, float, float] = (0.0, 0.0, 0.0)
    gyro_ada: tuple[float, float, float] = (0.0, 0.0, 0.0)
    magnetic_ada: tuple[float, float, float] = (0.0, 0.0, 0.0)

    # UPS - Waveshare
    ups: INA219 = INA219(i2c, 0x43)

    ups_voltage: float = 0.0  # voltage on V- (load side)
    ups_current_draw: float = 0.0  # current in A
    ups_battery_remaining: float = 0.0
    
    _last_sensor_read = 0.0
    # _sensor_cache_duration = 0.1  # 100ms cache = max 10Hz
    # _sensor_cache_duration = 0.04  # 40ms cache = max 25Hz
    # _sensor_cache_duration = 0.02  # 20ms cache = max 50Hz
    # _sensor_cache_duration = 0.01  # 10ms cache = max 100Hz
    _sensor_cache_duration = 0.005  # 5ms cache = max 200Hz
    # _sensor_cache_duration = 0.002  # 2ms = max 500Hz
    _cached_data = {
        "sensor1": {"accel": (0,0,0), "gyro": (0,0,0), "mag": (0,0,0)},
        "sensor2": {"accel": (0,0,0), "gyro": (0,0,0), "mag": (0,0,0)},
        "battery": {"percentage": 0, "voltage": 0, "current": 0}
    }

    # print("IoHandler initialized")
    oled.fill(0)  # Clear the display
    oled.text("IoHandler", 0, 25)
    oled.text("initialized...", 0, 35)
    oled.show()
    time.sleep(2)
    oled.poweroff()

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
