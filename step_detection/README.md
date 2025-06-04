# Step Detection System for Master's Thesis

This repository contains all the necessary code and tools for step detection using IMU sensors with Raspberry Pi Pico 2W. The project implements and compares multiple step detection algorithms to determine the most accurate method for different walking scenarios.

## Project Structure

```
.
├── data/                        # Data directory for recorded sensor data
│   ├── normal_walking/          # Example dataset
│   ├── fast_walking/            # Example dataset
│   └── ...                      # Other example datasets
├── plots/ # Generated plots and visualizations
|   ├── by_scenario/              # Organization by walking scenario
|   │   ├── normal_walking/
|   │   ├── fast_walking/
|   │   ├── slow_walking/
|   │   ├── stairs_up/
|   │   └── stairs_down/
|   ├── by_algorithm/             # Organization by algorithm
|   │   ├── peak_detection/
|   │   ├── zero_crossing/
|   │   ├── spectral_analysis/
|   │   ├── adaptive_threshold/
|   │   └── shoe/
|   ├── by_sensor/                # Organization by sensor
|   │   ├── sensor1_waveshare/
|   │   └── sensor2_adafruit/
|   ├── comparisons/              # Comparison plots
|   │   ├── algorithm_comparisons/
|   │   └── sensor_comparisons/
|   └── summary/                  # Summary plots (metrics, rankings)
├── ../src/                      # Web interface files
│   └── index_advanced.html      # Main web interface
├── step_detection_algorithms.py # Core algorithms implementation
├── step_data_collector.py       # GUI application for data collection
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## System Requirements

- Raspberry Pi Pico 2W with MicroPython firmware

- Python 3.7+ (for analysis tools)

- Required Python libraries (see requirements.txt)

- Web browser (for web interface)

## Hardware Setup

Connect the following components to your Raspberry Pi Pico 2W:

1. **Waveshare Pico-10DOF-IMU** (IMU 1)

   - Connect to I2C0 (GP6/GP7)

2. **Adafruit ST-9-DOF-Combo** (IMU 2)

   - Connect to I2C0 (GP6/GP7)

3. **Waveshare Pico-UPS-B** (Power Supply)

   - Connect to I2C0 (GP6/GP7)

4. **OLED Display (128x64, SSD1306)**

   - Connect to I2C1 (GP8/GP9)

5. **Optional Buttons**

   - Connect to GP14 (Toggle screen)

   - Connect to GP15 (Change display mode)

For exact wiring diagrams, see the documentation in `/.BACKUP/project_circuit_simple_diagram.pdf`.

## Installation

### 1. Setting Up Raspberry Pi Pico 2W

1. Flash MicroPython firmware onto your Pico 2W using the `.uf2` file from `/.BACKUP/Firmware/Pico%202W/`.

2. Copy the necessary MicroPython files to your Pico 2W:
   - Main Pico code (`main.py` and `classes/` directory)

### 2. Setting Up Analysis Environment

1. Create a virtual environment and activate it:

```bash
python3 -m venv venv
```

```bash
source venv/bin/activate
```

2. Install Python dependencies:

```bash
pip install -r requirements.txt
```

3. Ensure your Pico 2W is accessible on your network (it creates its own access point by default).

## Usage

### Web Interface

1. Connect to the Pico 2W's WiFi network (SSID: "Kisiel MasterThesis RPiPico", Password: "myMasterThesis").

2. Open a web browser and navigate to `http://192.168.4.1`.

3. Use the web interface to:

   - Record sensor data

   - Mark steps manually (using the button or spacebar)

   - Download recorded data

### Desktop Application

1. Run the GUI data collector:

```bash
python step_data_collector.py
```

2. Connect to your Pico 2W by entering the API URL (`http://192.168.4.1/api`) and clicking "Connect".

3. Use the GUI to:

   - Record sensor data

   - Mark steps manually

   - Analyze data with different algorithms

   - Visualize results

### Data Analysis

1. Generate example datasets and run algorithm comparisons:

```bash
python step_detection_algorithms.py
```

2. Review the generated plots in the `plots/` directory.

## Step Detection Algorithms

The following algorithms are implemented:

1. **Peak Detection**

   - Detects steps by identifying peaks in the accelerometer signal

   - Parameters: window_size, threshold, min_time_between_steps

2. **Zero-Crossing**

   - Detects steps by analyzing when the signal crosses the zero point

   - Parameters: window_size, min_time_between_steps

3. **Spectral Analysis**

   - Uses frequency domain analysis to identify periodic step patterns

   - Parameters: window_size, overlap, step_freq_range

4. **Adaptive Threshold**

   - Dynamically adjusts the detection threshold based on signal characteristics

   - Parameters: window_size, sensitivity, min_time_between_steps

5. **SHOE (Step Heading Offset Estimator)**

   - Combines accelerometer and gyroscope data for improved detection

   - Parameters: window_size, threshold, min_time_between_steps

## Custom Data Collection

To collect your own walking data:

1. Attach the Pico 2W device to your body (e.g., waist, arm, or leg).

2. Use either the web interface or desktop application to start recording.

3. Walk at different speeds or patterns while recording.

4. Mark each step using the button or spacebar.

5. After recording, save the data for analysis.

## Algorithm Comparison

The collected data can be analyzed to compare the performance of different step detection algorithms:

1. Load your recorded data in the desktop application.

2. Click "Analyze Data" to run all algorithms on the data.

3. Compare the results using metrics such as:

   - Precision (correctly detected steps / all detected steps)

   - Recall (correctly detected steps / actual steps)

   - F1 Score (harmonic mean of precision and recall)

   - Step Count Error (difference in total step count)

## Troubleshooting

- **Connection Issues**: Ensure you're connected to the Pico 2W's WiFi network.

- **Sensor Errors**: Check your wiring and connections.

- **Data Not Saving**: Ensure you have write permissions to the data directory.

- **Visualization Issues**: Check that matplotlib and other dependencies are correctly installed.

## Credits

This project was developed by Maksymilian Kisiel as part of a Master's Thesis at Silesian University of Technology, under the supervision of dr hab. inż. Agnieszka Szczęsna, prof. PŚ.

## License

GPL-3.0 license: [`../LICENSE`](../LICENSE)