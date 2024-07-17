# class to handle the IO for the demo setup
# from machine import Pin, ADC
import board
from busio import I2C

try:
    from typing import Tuple
except ImportError:
    pass

# Adafruit libraries for IMU 1
# import adafruit_lps2x # pressure n temp
import adafruit_icm20x

# Adafruit libraries for IMU 2
from adafruit_lsm6ds.lsm6dsox import LSM6DSOX as LSM6DS
from adafruit_lis3mdl import LIS3MDL

# Adafruit library for UPS
from adafruit_ina219 import INA219


class IoHandler:
    # Initializing onboard LED and temperature sensor
    # onboard_led = Pin("LED", Pin.OUT, value=0)  # GPIO pin for onboard LED
    # led_state = 0

    # I2C initialization
    i2c = I2C(board.GP7, board.GP6)  # I2C(SCL, SDA)
    # print(i2c.scan())
    """
    [28, 67, 92, 104, 106] == [0x1C, 0x43, 0x5C, 0x68, 0x6A]
    0x1C, 0x6A  => Adafruit IMU
    0x43        => UPS-A
    0x5C, 0x68  => Waveshare IMU
    """
    # """
    # IMU 1 - Waveshare
    # press_temp_wav = adafruit_lps2x.LPS22(i2c, 0x5C)
    imu_wav = adafruit_icm20x.ICM20948(i2c, 0x68)

    # pressure_wav = 0.0
    # temp_wav = 0.0
    acceleration_wav = (0.0, 0.0, 0.0)
    gyro_wav = (0.0, 0.0, 0.0)
    magnetic_wav = (0.0, 0.0, 0.0)
    # """
    # IMU 2 - Adafruit
    accel_gyro_ada = LSM6DS(i2c)
    mag_ada = LIS3MDL(i2c)

    acceleration_ada = (0.0, 0.0, 0.0)
    gyro_ada = (0.0, 0.0, 0.0)
    magnetic_ada = (0.0, 0.0, 0.0)

    # """
    # UPS - Waveshare
    ups = INA219(i2c, 0x43)

    ups_voltage = 0.0  # voltage on V- (load side)
    ups_current_draw = 0.0  # current in A
    ups_battery_remaining = 0.0
    # """

    def __init__(self):
        # get everything into a starting state
        # self.__class__.show_onboard_led()
        pass

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

    # Adafruit acceleration handler
    @classmethod
    def get_accel_ada_reading(cls) -> Tuple[float, float, float]:
        cls.acceleration_ada = cls.accel_gyro_ada.acceleration
        # print(
        #     "Acceleration: X:{0:7.2f}, Y:{1:7.2f}, Z:{2:7.2f} m/s^2".format(
        #         *cls.acceleration_ada
        #     )
        # )
        return cls.acceleration_ada

    # Adafruit gyro handler
    @classmethod
    def get_gyro_ada_reading(cls) -> Tuple[float, float, float]:
        cls.gyro_ada = cls.accel_gyro_ada.gyro
        # print(
        #     "Gyro          X:{0:7.2f}, Y:{1:7.2f}, Z:{2:7.2f} rad/s".format(*cls.gyro_ada)
        # )
        return cls.gyro_ada

    # Adafruit magnetic handler
    @classmethod
    def get_magnetic_ada_reading(cls) -> Tuple[float, float, float]:
        cls.magnetic_ada = cls.mag_ada.magnetic
        # print(
        #     "Magnetic      X:{0:7.2f}, Y:{1:7.2f}, Z:{2:7.2f} uT".format(*cls.magnetic_ada)
        # )
        return cls.magnetic_ada

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

    # Waveshare acceleration handler
    @classmethod
    def get_accel_wav_reading(cls) -> Tuple[float, float, float]:
        cls.acceleration_wav = cls.imu_wav.acceleration
        # print("Acceleration: X:%.2f, Y: %.2f, Z: %.2f m/s^2" % (cls.acceleration_wav))
        return cls.acceleration_wav

    # Waveshare gyro handler
    @classmethod
    def get_gyro_wav_reading(cls) -> Tuple[float, float, float]:
        cls.gyro_wav = cls.imu_wav.gyro
        # print("Gyro X:%.2f, Y: %.2f, Z: %.2f rads/s" % (cls.gyro_wav))
        return cls.gyro_wav

    # Waveshare magnetic handler
    @classmethod
    def get_magnetic_wav_reading(cls) -> Tuple[float, float, float]:
        cls.magnetic_wav = cls.imu_wav.magnetic
        # print("Magnetometer X:%.2f, Y: %.2f, Z: %.2f uT" % (cls.magnetic_wav))
        return cls.magnetic_wav

    # """
    # Waveshare UPS voltage handler
    @classmethod
    def get_ups_voltage_reading(cls) -> float:
        # INA219 measure bus voltage on the load side. So PSU voltage = bus_voltage + shunt_voltage
        cls.ups_voltage = cls.ups.bus_voltage  # voltage on V- (load side)
        # print("Voltage:  {:6.3f} V".format(cls.ups_voltage))
        return cls.ups_voltage

    # Waveshare UPS current handler
    @classmethod
    def get_ups_current_reading(cls) -> float:
        cls.ups_current_draw = (
            cls.ups.current
        ) / 1000  # (current in mA) / 1000 = current in A
        # print("Current:  {:6.3f} A".format(cls.ups_current_draw))
        return cls.ups_current_draw

    # Waveshare UPS battery percentage handler
    @classmethod
    def get_ups_battery_reading(cls) -> Tuple[float, float]:
        cls.ups_battery_remaining = (cls.ups.bus_voltage - 3) / 1.18 * 100
        if cls.ups_battery_remaining < 0:
            cls.ups_battery_remaining = 0
        elif cls.ups_battery_remaining > 100:
            cls.ups_battery_remaining = 100
        # print("Percent:  {:6.1f} %".format(cls.ups_battery_remaining))
        return (cls.ups_battery_remaining, cls.ups.bus_voltage)

    # """
