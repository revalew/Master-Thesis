from machine import Pin, Timer  # type: ignore
# import utime as time


class DebouncedInput:
    """
    Micropython Debounced GPIO Input Class
    """


    def __init__(
        self,
        pinNum: int,
        callback: function,
        pinPull: int | None = None,
        pinLogicPressed: bool = False,
        debounceMs: int = 100,
        irqTrigger: int = Pin.IRQ_FALLING,
    ):
        """
        Initialize a DebouncedInput instance.

        Args:
            pinNum (int): The GPIO pin number to read input from.
            callback (Callable[[Pin, bool], None]): A function to be called when the button state changes. It takes two arguments: the Pin object and a boolean indicating the button state.
            pinPull (int | None, optional): The pull state of the pin. If `None`, the pin is not pulled. Default is None.
                - `Pin.PULL_UP` for active low,
                - `Pin.PULL_DOWN` for active high.
            pinLogicPressed (bool, optional): The logic level that represents the button being pressed. Default is False.
                - `False` for active low (`Pin.PULL_UP`),
                - `True` for active high (`Pin.PULL_DOWN`).
            debounceMs (int, optional): The debounce time in milliseconds. Default is 100 ms.
            irqTrigger (Pin.IRQ, optional): The interrupt trigger mode. Default is Pin.IRQ_FALLING.
                - `Pin.IRQ_FALLING` interrupt on falling edge.
                - `Pin.IRQ_RISING` interrupt on rising edge.
                - `Pin.IRQ_RISING | Pin.IRQ_FALLING` interrupt on both edges.

        Attributes:
            pinNum (int): The GPIO pin number.
            pinLogicPressed (bool): The logic level for pressed state.
            debounceMs (int): The debounce duration in milliseconds.
            callback (callable): The function called on button state change.
            expectedValue (bool): The expected stable value of the button.
            pin (Pin): The Pin object for GPIO handling.
            dbTimer (Timer): The Timer object for debounce handling.
            (**NOT USED / ACCESSIBLE**) lastReleaseMs (int): The timestamp of the last button release.
            (**NOT USED / ACCESSIBLE**) lastPressMs (int): The timestamp of the last button press.
        """

        # self.pinNum = pinNum
        self.pinLogicPressed = pinLogicPressed
        self.debounceMs = debounceMs
        self.callback = callback
        # self.lastReleaseMs = 0
        # self.lastPressMs = 0
        self.expectedValue = True
        self.irqTrigger = irqTrigger

        # Initialize GPIO
        # self.pin = Pin(self.pinNum, Pin.IN, pinPull)
        self.pin = Pin(pinNum, Pin.IN, pinPull)
        self.pin.irq(self.__irq_handler, self.irqTrigger)

        # Timer to debounce
        self.dbTimer = Timer(-1)


    def __debounce_timer_expired(
            self,
            timer: Timer
        ) -> None:
        """
        Debounce function - checks if the button is stable

        Args:
            timer: Timer

        Returns:
            None
        """
        # Enable IRQ for button
        self.pin.irq(self.__irq_handler, self.irqTrigger)

        current_value = self.pin.value() == self.pinLogicPressed

        if self.expectedValue and current_value:
            # Button pressed
            self.expectedValue = False
            # self.lastPressMs = time.ticks_ms()
            # msSinceLastPress = (
            #     time.ticks_diff(self.lastPressMs, self.lastReleaseMs)
            #     if self.lastReleaseMs
            #     else 0
            # )
            # self.callback(self.pinNum, True, msSinceLastPress)
            self.callback(self.pin, True) # type: ignore

        elif not self.expectedValue and not current_value:
            # Button released
            self.expectedValue = True
            # self.lastReleaseMs = time.ticks_ms()
            # msDurationOfPress = time.ticks_diff(self.lastReleaseMs, self.lastPressMs)
            # self.callback(self.pinNum, False, msDurationOfPress)
            self.callback(self.pin, False) # type: ignore



    def __irq_handler(self, pin: Pin) -> None:
        """
        Interrupt handler for button state changes.

        Disables the IRQ (so that another edge trigger can't sneak in) and starts the debounce timer.

        Args:
            pin: The Pin object that triggered the interrupt.

        Returns:
            None
        """
        self.pin.irq(trigger=0)  # Disable IRQ for debounce
        self.dbTimer.init(
            mode=Timer.ONE_SHOT,
            period=self.debounceMs,
            callback=self.__debounce_timer_expired,
        )
