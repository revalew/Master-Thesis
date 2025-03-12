# Master thesis project - "Step estimation from motion sensors" with RPi Pico 2 W

<br/>
<br/>

<div align='center'>


[![GitHub License](https://img.shields.io/github/license/revalew/Master-Thesis)](https://github.com/revalew/Master-Thesis/blob/master/LICENSE)

[![GitHub](https://img.shields.io/github/commit-activity/t/revalew/Master-Thesis?style=social)](https://github.com/revalew/Master-Thesis)
[![GitHub](https://img.shields.io/github/last-commit/revalew/Master-Thesis?style=social)](https://github.com/revalew/Master-Thesis)

[![GitHub](https://img.shields.io/github/repo-size/revalew/Master-Thesis?style=social)](https://github.com/revalew/Master-Thesis) [![GitHub](https://img.shields.io/github/languages/top/revalew/Master-Thesis?style=social)](https://github.com/revalew/Master-Thesis)

</div>


<br/>
<br/>

> [!CAUTION]
>
> After the migration to the `Pico 2 W`, the project might not be compatible with the original `Pico W` anymore. The `Pico 2 W` has more RAM and storage to handle additional devices and resources.
> 
> To run the project on the original `Pico W`, you might need to modify the code to work with the `Pico W` instead of the `Pico 2 W`. This could include removing some devices (like OLED display), libraries or lines of code (docs and whitespaces) to save both RAM and storage.
>
> Try uploading the compiled libraries to the `Pico W` and see if it works. If it doesn't, you might need to modify the code to work with the `Pico W` and recompile the libraries.

<br/>
<br/>

## Overview

The aim of this project is to create a circuit to measure and analyze the data from two different IMUs (Inertial Measurement Units) to determine the accuracy of the step estimation algorithm (multiple if there is time).

<br/>
<br/>

## Table of contents

- [Required / used components](#required--used-components)
- [How to connect the components](#how-to-connect-the-components)
- [Project structure and important locations](#project-structure-and-important-locations)
- [Progress](#progress)
  - [First major success](#first-major-success)
  - [Migration to Pico 2 W](#migration-to-pico-2-w)
  - [Compiling the libraries for Pico 2 W (`.py` to `.mpy`)](#compiling-the-libraries-for-pico-2-w-py-to-mpy)

<br/>
<br/>

## Required / used components

The project will make use of a variety of components:

- [Raspberry Pi `Pico W` / `Pico 2 W`](https://www.raspberrypi.com/documentation/microcontrollers/raspberry-pi-pico.html) (access point, web server, reading sensors, driving TFT display) running [MicroPython](https://micropython.org/download/RPI_PICO/) with various [CircuitPython Libraries](https://learn.adafruit.com/circuitpython-libraries-on-micropython-using-the-raspberry-pi-pico/overview),

- [Pico-10DOF-IMU](https://www.waveshare.com/wiki/Pico-10DOF-IMU) as the first IMU,

- [ST-9-DOF-Combo](https://learn.adafruit.com/st-9-dof-combo) as the second IMU,

- [Pico-UPS-B](https://www.waveshare.com/wiki/Pico-UPS-B) as a power source,

- [0.96inch_OLED_Module](https://www.waveshare.com/wiki/0.96inch_OLED_Module) to display the measurements and battery level (I used no-name super-cheap I2C `128x64` OLED display marked as [`gm009605v4.2`](https://allegro.pl/oferta/wyswietlacz-oled-0-96-i2c-ssd1306-bialy-17251217815), originally planned to use [3.5inch_TFT_Touch_Shield](https://www.waveshare.com/wiki/3.5inch_TFT_Touch_Shield)),

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


- [`~/libs_to_compile/`](./libs_to_compile/) directory containing all the CircuitPython libraries that may be needed in the project (before compilation, [`~/libs_to_compile/lib/`](./libs_to_compile/lib/)) and instructions on how to compile them along with the scripts to do it,

  - [`~/libs_to_compile/lib/classes/`](./libs_to_compile/lib/classes/) directory (module) containing all necessary custom-written classes for easy development,

- [`~/libs/`](./libs/) directory containing all the CircuitPython libraries after compilation,

- [`~/src/`](./src/) directory contains all the resources needed for the web server (HTML, CSS, JS),

- [`Makefile`](./Makefile) file for automating the `git` workflow (committing, pushing, adding new tags, etc.),

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

Added OLED display (`ssd1306` library) instead of the TFT touch shield to display the measurements and battery level. Separate I2C interface is used to connect the display to the `Pico 2 W`, because it requires `frequency=400000` instead of the default `frequency=100000`. The display starts turned off, but it can be turned on by pressing the button attached to `GP14`. Another button (`GP15`) can be used to cycle through the measurements of the IMU sensors and battery level. The display is updated every 0.5 seconds for the IMUs and 5 seconds for the battery.

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

### Compiling the libraries for Pico 2 W (`.py` to `.mpy`)

The libraries of the project were successfully compiled for the `Pico 2 W` using the script [`./libs_to_compile/mpy_compile_all_libs.sh`](./libs_to_compile/mpy_compile_all_libs.sh) to optimize the size of the libraries and RAM usage. It seems to be faster than before.

The script is in the [`libs_to_compile/`](./libs_to_compile/) directory and it compiles all the libraries in the `libs_to_compile/lib` directory into `../lib/` (root of the project). Instructions for the script can be found in the [`./libs_to_compile/README.md`](./libs_to_compile/README.md) file.

<br/>
<br/>

### ...

<br/>
<br/>