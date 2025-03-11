from machine import Pin, I2C
from adafruit_ssd1306 import SSD1306_I2C

# i2c = I2C(0, scl=Pin(9), sda=Pin(8), freq=400000)

from board import GP6, GP7, GP8, GP9
from busio import I2C

# According to the SSD1306 datasheet, the minimum i2c clock cycle time is 2.5us. Therefore, the maximum i2c clock frequency is 400KHz. The i2c clock frequency used by this project is 400KHz.
i2c = I2C(scl=GP9, sda=GP8, frequency=400000)
# i2c = I2C(scl=GP9, sda=GP8, frequency=100000)

print("I2C Scan:", i2c.scan())

if 0x3C in i2c.scan():
    print("SSD1306 found!")
    oled = SSD1306_I2C(128, 64, i2c, addr=0x3C)
    oled.fill(1)  # Wypełnij ekran na biało
    oled.show()
else:
    print("OLED not found!")
