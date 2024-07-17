# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import board
import adafruit_icm20x
import busio

i2c = busio.I2C(
    board.GP7, board.GP6
)  # Init the I2C with explicit pins using busio.I2C(). The pico doesn't have a default set of pins labeled for I2C.
print(i2c.scan())
icm = adafruit_icm20x.ICM20948(i2c, 0x68)

while True:
    print("Acceleration: X:%.2f, Y: %.2f, Z: %.2f m/s^2" % (icm.acceleration))
    print("Gyro X:%.2f, Y: %.2f, Z: %.2f rads/s" % (icm.gyro))
    print("Magnetometer X:%.2f, Y: %.2f, Z: %.2f uT" % (icm.magnetic))
    print("")
    time.sleep(0.5)
