from machine import Pin, Timer

from DebouncedInput import DebouncedInput # only this class is uploaded to the device and the code is executed using "Run current file"


def print_msg(pin: Pin, pressed: bool) -> None:
    if pressed:
        print(f"You pressed the button {pin}!")
    # else:
    #     print(f"You released the button {pin}!")

# button = Pin(17, mode=Pin.IN, pull=Pin.PULL_UP)
# button.irq(trigger=Pin.IRQ_FALLING, handler=print_msg)
button = DebouncedInput(
    pinNum=17,
    callback=print_msg,
    pinPull=Pin.PULL_UP,
    debounceMs=50,
)

button2 = DebouncedInput(
    pinNum=16,
    callback=print_msg,
    pinPull=Pin.PULL_UP,
    debounceMs=50,
)


while True:
    ...
