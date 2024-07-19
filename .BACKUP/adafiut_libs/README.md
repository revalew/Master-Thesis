# HOW TO INSTALL CircuitPython LIBRARIES ON MicroPython BOARD

## Overview

**Libraries in MPY format will not work in MicroPython. You'll need to use the libraries ending in `*.py`.**

First start by downloading the latest CircuitPython library bundle from [circuitpython.org](https://circuitpython.org/libraries).
Download the `adafruit-circuitpython-bundle-py-*.zip` bundle zip file (**REMEMBER TO DOWNLOAD THE `*.py` and not `*.mpy` VERSION**), and unzip a folder of the same name. Inside you'll find a `lib/` folder. The entire collection of libraries is too large to fit on the Raspberry Pi Pico. Instead, add each library as you need it, this will reduce the space usage but you'll need to put in a little more effort.

Same as with with Blinka and PlatformDetect, use file transfer system to navigate to the bundle folder and select any library files or folders you want to transfer, and upload them to Pico.

## Libraries and Tools

**ALL OF THE LIBRARIES HAVE TO BE PLACED IN THE `/lib/` DIRECTORY
ON PICO BOARD (YOU HAVE TO CREATE ONE IF IT IS NOT THERE YET)**

Required libraries from the bundle:

- (entire folder) `adafruit_lsm6ds/`
- (entire folder) `adafruit_bus_device/`
- (entire folder) `adafruit_register/`
- (single file) `adafruit_lis3mdl.py`

Blinka compatibility layer:

- To install the Blinka, navigate to the location where you unzipped the Blinka files and upload everything inside of the **src folder** to the Pico.
- If you want to free up some more room, many of the linux board and microcontroller files can be removed under the `adafruit_blinka/` folder. The only ones used by the Pico are the `adafruit_blinka/microcontroller/generic_micropython` folder, `adafruit_blinka/microcontroller/rp2040.py` and `adafruit_blinka/board/raspberrypi/pico.py`.

Platform detect:

- To install the PlatformDetect, navigate to the location where you unzipped the files and upload the adafruit_platformdetect folder to the Pico.

## I2C Usage

Init the I2C with explicit pins using `busio.I2C()`. The pico doesn't have a default set of pins labeled for I2C, so this:

```python
import board

i2c = board.I2C()  # uses board.SCL and board.SDA
```

has to be modified to this:

```python
import board
import busio

# I2C initialization
# GP4 and GP5 are the default ports for I2C bus no. 1 (pin 6 & 7)
i2c = busio.I2C(board.GP5, board.GP4)
```

If you are using different I2C interface change those values accordingly (check pinout @[`.BACKUP/pico-pinout.svg`](../pico-pinout.svg))
