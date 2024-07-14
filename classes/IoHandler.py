# class to handle the IO for the demo setup
from machine import Pin, ADC


class IoHandler:
    # Initializing onboard LED and temperature sensor
    onboard_led = Pin("LED", Pin.OUT, value=0)  # GPIO pin for onboard LED
    led_state = 0

    # GPIO 4 is connected to the temperature sensor
    temp = ADC(4)
    temp_value = 0

    def __init__(self):
        # get everything into a starting state
        self.__class__.show_onboard_led()

    # red onboard_led handlers
    @classmethod
    def show_onboard_led(cls):
        cls.onboard_led.value(cls.led_state)

    @classmethod
    def toggle_onboard_led(cls):
        cls.led_state = 0 if cls.led_state == 1 else 1
        cls.show_onboard_led()

    @classmethod
    def get_onboard_led(cls):
        return 0 if cls.led_state == 0 else 1

    @classmethod
    def set_onboard_led(cls, state):
        cls.led_state = 0 if state == 0 else 1
        cls.show_onboard_led()

    # temp handler
    @classmethod
    def get_temp_reading(cls):
        temp_voltage = cls.temp.read_u16() * (3.3 / 65535)
        cls.temp_value = 27 - (temp_voltage - 0.706) / 0.001721
        return cls.temp_value
