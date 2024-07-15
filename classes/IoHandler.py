# class to handle the IO for the demo setup
from machine import Pin, ADC

# Adafruit libraries for IMU
import board
from busio import I2C

try:
    from typing import Tuple
except ImportError:
    pass
from adafruit_lsm6ds.lsm6dsox import LSM6DSOX as LSM6DS
from adafruit_lis3mdl import LIS3MDL


class IoHandler:
    # Initializing onboard LED and temperature sensor
    onboard_led = Pin("LED", Pin.OUT, value=0)  # GPIO pin for onboard LED
    led_state = 0

    # GPIO 4 is connected to the temperature sensor
    temp = ADC(4)
    temp_value = 0

    # I2C initialization
    i2c = I2C(board.GP5, board.GP4)
    accel_gyro = LSM6DS(i2c)
    mag = LIS3MDL(i2c)

    acceleration = (0.0, 0.0, 0.0)
    gyro = (0.0, 0.0, 0.0)
    magnetic = (0.0, 0.0, 0.0)

    def __init__(self):
        # get everything into a starting state
        self.__class__.show_onboard_led()

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

    # acceleration handler
    @classmethod
    def get_accel_reading(cls) -> Tuple[float, float, float]:
        cls.acceleration = cls.accel_gyro.acceleration
        # print(
        #     "Acceleration: X:{0:7.2f}, Y:{1:7.2f}, Z:{2:7.2f} m/s^2".format(
        #         *cls.acceleration
        #     )
        # )
        return cls.acceleration

    # gyro handler
    @classmethod
    def get_gyro_reading(cls) -> Tuple[float, float, float]:
        cls.gyro = cls.accel_gyro.gyro
        # print(
        #     "Gyro          X:{0:7.2f}, Y:{1:7.2f}, Z:{2:7.2f} rad/s".format(*cls.gyro)
        # )
        return cls.gyro

    # magnetic handler
    @classmethod
    def get_magnetic_reading(cls) -> Tuple[float, float, float]:
        cls.magnetic = cls.mag.magnetic
        # print(
        #     "Magnetic      X:{0:7.2f}, Y:{1:7.2f}, Z:{2:7.2f} uT".format(*cls.magnetic)
        # )
        return cls.magnetic
