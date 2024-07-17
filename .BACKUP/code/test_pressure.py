# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import board
import adafruit_lps2x
import busio

i2c = busio.I2C(
    board.GP7, board.GP6
)  # Init the I2C with explicit pins using busio.I2C(). The pico doesn't have a default set of pins labeled for I2C.
# print(i2c.scan())
lps = adafruit_lps2x.LPS22(i2c, 0x5C)

while True:
    print("Pressure: %.2f hPa" % lps.pressure)
    print("Temperature: %.2f C" % lps.temperature)
    time.sleep(1)
