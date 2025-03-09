# Master thesis project - "Step estimation from motion sensors" with RPi Pico W

## Overview

The aim of this project is to create a circuit to measure and analyze the data from two different IMUs (Inertial Measurement Units) to determine the accuracy of the step estimation algorithm (multiple if there is time).

## Required / used components

The project will make use of a variety of components:

- [Raspberry Pi `Pico W` / `Pico 2 W`](https://www.raspberrypi.com/documentation/microcontrollers/raspberry-pi-pico.html) (access point, web server, reading sensors, driving TFT display) running [MicroPython](https://micropython.org/download/RPI_PICO/) with various [CircuitPython Libraries](https://learn.adafruit.com/circuitpython-libraries-on-micropython-using-the-raspberry-pi-pico/overview),

- [Pico-10DOF-IMU](https://www.waveshare.com/wiki/Pico-10DOF-IMU) as the first IMU,

- [ST-9-DOF-Combo](https://learn.adafruit.com/st-9-dof-combo) as the second IMU,

- [Pico-UPS-B](https://www.waveshare.com/wiki/Pico-UPS-B) as a power source,

- [3.5inch_TFT_Touch_Shield](https://www.waveshare.com/wiki/3.5inch_TFT_Touch_Shield) to display the measurements and battery level,

- [Pico-Dual-Expander](https://www.waveshare.com/pico-dual-expander.htm) to hold some components together w/o soldering,

- 3D printed enclosure for the device to protect the circuit (custom design).

## How to connect the components

Simple list of connections in [`~/.BACKUP/project_circuit_simple_diagram.pdf`](./.BACKUP/project_circuit_simple_diagram.pdf)

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

## Progress

### First major success

I managed to create an asynchronous web server that handles clients and reads sensor data at the same time (based on a scheduler, multithreading-coming-soon&trade;). Notable achievements of this release:

- Pico acting as an access point,

- Handling of asynchronous requests,

- Added translation layer for CircuitPython,

- Reading IMU sensor data using the CircuitPython library (Adafruit "LSM6DSOX + LIS3MDL 9 DoF" Sensor),

- Control the device from a web page,

- Live UI update and synchronous data retrieval.

<p align='center'>
  <img src="./.BACKUP/img_README/first_success.png" width="400"/>
  <img src="./.BACKUP/img_README/first_success_mobile.png" width="180" height="344" />
</p>
