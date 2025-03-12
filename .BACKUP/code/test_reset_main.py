import machine
import time

from board import GP8, GP9
from busio import I2C

from adafruit_ssd1306 import SSD1306_I2C

i2c_2: I2C = I2C(scl=GP9, sda=GP8, frequency=400000)  # I2C(SCL, SDA)
oled: SSD1306_I2C = SSD1306_I2C(128, 64, i2c_2, addr=0x3C)
oledContrast = 10
oled.contrast(oledContrast)

oled.fill(0)  # Clear the display
oled.text("Initializing...", 0, 30)
oled.show()

# Po 5 sekundach restartujemy urządzenie
time.sleep(2)
oled.fill(0)  # Clear the display
oled.text("Reset...", 0, 30)
oled.show()
time.sleep(2)
oled.fill(0)  # Clear the display
oled.show()
machine.reset()  # Wywołuje restart urządzenia
