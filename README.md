# Master thesis project - "Step estimation from motion sensors" with RPi Pico W

<br/>
<br/>

> [!CAUTION]
>
> After the migration to the `Pico 2 W`, the project might not be compatible with the original `Pico W` anymore. The `Pico 2 W` has more RAM and storage to handle additional devices and resources.
> 
> To run the project on the original `Pico W`, you might need to modify the code to work with the `Pico W` instead of the `Pico 2 W`. This could include removing some devices (like OLED display), libraries or lines of code (docs and whitespaces) to save both RAM and storage.

<br/>
<br/>

## Overview

The aim of this project is to create a circuit to measure and analyze the data from two different IMUs (Inertial Measurement Units) to determine the accuracy of the step estimation algorithm (multiple if there is time).

<br/>
<br/>

## Required / used components

The project will make use of a variety of components:

- [Raspberry Pi `Pico W` / `Pico 2 W`](https://www.raspberrypi.com/documentation/microcontrollers/raspberry-pi-pico.html) (access point, web server, reading sensors, driving TFT display) running [MicroPython](https://micropython.org/download/RPI_PICO/) with various [CircuitPython Libraries](https://learn.adafruit.com/circuitpython-libraries-on-micropython-using-the-raspberry-pi-pico/overview),

- [Pico-10DOF-IMU](https://www.waveshare.com/wiki/Pico-10DOF-IMU) as the first IMU,

- [ST-9-DOF-Combo](https://learn.adafruit.com/st-9-dof-combo) as the second IMU,

- [Pico-UPS-B](https://www.waveshare.com/wiki/Pico-UPS-B) as a power source,

- [3.5inch_TFT_Touch_Shield](https://www.waveshare.com/wiki/3.5inch_TFT_Touch_Shield) to display the measurements and battery level,

- [Pico-Dual-Expander](https://www.waveshare.com/pico-dual-expander.htm) to hold some components together w/o soldering,

- 3D printed enclosure for the device to protect the circuit (custom design).

<br/>
<br/>

## How to connect the components

Simple list of connections in [`~/.BACKUP/project_circuit_simple_diagram.pdf`](./.BACKUP/project_circuit_simple_diagram.pdf)

<br/>
<br/>

## Project structure and important locations

This project consists of many files and directories, the most important of which are described below:

- Directory [`~/.BACKUP/`](./.BACKUP/) containing the backup and important files that should not be transferred to the Pico:

  - Adding the CircuitPython compatibility layer - short tutorial in [`~/.BACKUP/adafiut_libs/README.md`](./.BACKUP/adafiut_libs/README.md) (with required libraries in the same directory),

  - Raspberry Pi `Pico W` and `Pico 2 W` board pinout in [`~/.BACKUP/pinout/`](./.BACKUP/pinout/) directory,

  - Firmware used in the project (for both `Pico W` and `Pico 2 W`) in [`~/.BACKUP/Firmware/`](./.BACKUP/Firmware/) directory:

    - Pico W: [`~/.BACKUP/Firmware/Pico%20W/RPI_PICO-20240602-v1.23.0.uf2`](./.BACKUP/Firmware/Pico%20W/RPI_PICO-20240602-v1.23.0.uf2),

    - Pico 2 W: [`~/.BACKUP/Firmware/Pico%202W/pico2_w-v0.0.12-pimoroni-micropython.uf2`](./.BACKUP/Firmware/Pico%202W/pico2_w-v0.0.12-pimoroni-micropython.uf2),

  - [`~/.BACKUP/code/`](./.BACKUP/code/) for old / sample / backup code,

  - **(LINUX USERS: MicroPico Extension for VSCode)** script used to resolve user permissions in [`~/.BACKUP/solvePermissions.sh`](./.BACKUP/solvePermissions.sh),

- [`~/classes/`](./classes/) directory (module) containing all necessary classes for easy development,

- [`~/lib/`](./lib/) directory containing all the CircuitPython libraries that may be needed in the project,

- [`~/src/`](./src/) directory contains all the resources needed for the web server (HTML, CSS, JS),

- **[`main.py`](./main.py)** as the main file of the project and the program to be executed on startup.

<br/>
<br/>

## Progress

<br/>
<br/>

### First major success

I managed to create an asynchronous web server that handles clients and reads sensor data at the same time (based on a scheduler, multithreading-coming-soon&trade;). Notable achievements of this release:

- Pico acting as an access point,

- Handling of asynchronous requests,

- Added translation layer for CircuitPython,

- Reading IMU sensor data using the CircuitPython library (Adafruit "LSM6DSOX + LIS3MDL 9 DoF" Sensor),

- Control the device from a web page,

- Live UI update and synchronous data retrieval.

<div align='center'>
  <img src="./.BACKUP/img_README/1/first_success.png" alt="First success PC" width="400"/>
  <img src="./.BACKUP/img_README/1/first_success_mobile.png" alt="First success mobile" height="344" />
</div>

<br/>
<br/>

### Migration to Pico 2 W

I moved the project to the Pico 2 W, and it works just fine now using the [`Blinka`](./lib/adafruit_blinka/), [`Platform Detect`](./lib/adafruit_platformdetect/) and other [`CircuitPython`](./lib/) libraries. 

Doubled RAM and Flash memory of the Pico 2 W makes it possible to run the project without the fear of low RAM (especially when creating new objects / adding more devices and sending WWW resources) and storage issues (as it was the case with the Pico W, but the `gc.collect()` function is still called everywhere just in case :skull: and all WWW resources don't have any white space).

Added new class [`DebouncedInput.py`](./classes/ResponseBuilder.py) to handle the debouncing of the buttons 
This feature is built-in to the standard Python library for the Raspberry Pi like RPi 3/4/5 etc., but not to the MicroPython - `import RPi.GPIO as GPIO; GPIO.add_event_detect(sensor, GPIO.BOTH, bouncetime=300) # signals when the pin goes HIGH/LOW`, full example in [another project](https://github.com/revalew/Plant-Inspector/blob/master/plantinspector.com/public_html/python/sensorDataLogger.py#L138).

Added OLED display (`ssd1306` library) instead of the TFT touch shield to display the measurements and battery level. The display starts turned off, but it can be turned on by pressing the button. Another button can be used to cycle through the measurements of the IMU sensors and battery level. The display is updated every 0.5 seconds for the IMUs and 5 seconds for the battery.

Updated the web page to display the measurements and battery level.

<div align='center'>
  <img src="./.BACKUP/img_README/2/IMU_1.jpg" alt="IMU 1 measurements displayed on the OLED" height="344" />
  <img src="./.BACKUP/img_README/2/IMU_2.jpg" alt="IMU 2 measurements displayed on the OLED" height="344" />

  <br/>

  <img src="./.BACKUP/img_README/2/battery.jpg" alt="Battery level displayed on the OLED" height="344" />
  <img src="./.BACKUP/img_README/2/pico_2_w_on_battery.jpg" alt="Pico 2 W running on the battery" height="344" />

  <br/>

  <img src="./.BACKUP/img_README/2/updated_webpage.png" alt="Updated webpage" width="400"/>
</div>

<br/>
<br/>

### ...