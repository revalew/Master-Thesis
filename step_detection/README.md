# Step Detection Analysis Module

<br/><br/>

This module contains the data analysis pipeline for the Master's Thesis project on step detection using IMU sensors. For the complete project overview and hardware setup, see the [main README](../README.md).

<br/><br/>

## Project Structure

<br/>

```
step_detection/
├── analysis/                    # Analysis results and screenshots
├── parser/                      # Parser for TUG (Timed Up and Go) test data and bulk analysis 
├── utils/                       # Module with the GUI app and algorithm implementations
├── requirements.txt             # Python dependencies
├── data_analyzer.py             # Run bulk analysis in given directory
├── parser.py                    # Parser for TUG (Timed Up and Go) test data (which I got from my supervisor)
├── step_data_collector.py       # Main GUI
├── detection_params.json        # Algorithm parameters
├── TUNING_PARAMS_GUIDE.md       # Parameter tuning guide
├── SCENARIO_SPECIFIC_PARAMS.md  # Ready-to-use parameter sets
└── README.md                    # This file
```

<br/><br/>

## Installation

<ol>
   <li> Create a virtual environment and activate it
    
<br/>
<br/>

```bash
python3 -m venv venv
```

```bash
source venv/bin/activate # On Windows: venv\Scripts\activate
```

   </li>
   <br/>
    
   <li> Install Python dependencies
    
<br/>
<br/>

```bash
pip install -r requirements.txt
```

   </li>
   <br/>
   
   <li> Ensure your Pico 2W is accessible on your network (it creates its own access point by default).
   </li>
</ol>

<br/><br/>

## Usage

<br/>

### Real-time Data Collection & Analysis

Run the GUI application:

<br/>

```bash
python step_data_collector.py
```

<br/>

**Features:**

- Connect to Raspberry Pi Pico 2W via API (`http://192.168.4.1/api`)

- Real-time sensor data visualization

- Manual step marking (spacebar / GUI button / mouse)

- Mouse bindings for marking ground truth steps (`right-click`) and starting/stopping recording (`middle-click`)

- Live algorithm analysis with [5 different methods](#step-detection-algorithms)

- Adjustable detection parameters (through [`./detection_params.json`](./detection_params.json); can be modified without restarting the application - just reopen the analysis window afterwards)

- Save/load recorded sessions

- Export data to CSV format

<br/>

### Standalone Performance Analysis (bulk analysis)

Manually going through $`84`$ experiments using the GUI could take a long time. Run the analysis module without the GUI for all subfolders
in the [`./analysis/experiments/`](./analysis/experiments/) directory (or any other directory of your choice):

<br/>

```bash
python data_analyzer.py
```

<br/>

This creates (or updates) the analysis results of each experiment in the given directory,

e.g.: [`./analysis/experiments/1_mount_thigh_pocket/1_TUG/tug_thigh_1/detection_results.yaml`](./analysis/experiments/1_mount_thigh_pocket/1_TUG/tug_thigh_1/detection_results.yaml)

<br/>

### Parser for TUG (Timed Up and Go) test data

After the consultation with my supervisor, I got the task of adjusting the recordings of her experiments to fit the required format of this project. This allows us to evaluate the performance of the algorithms on the same data.

Go read the README there [`./parser/`](./parser/) and see how the parser converts the data into the format used by this project.

<br/>

```bash
python parser.py
```

<br/><br/>

## Step Detection Algorithms

The following algorithms are implemented in [`./utils/step_detection_algorithms.py`](./utils/step_detection_algorithms.py):

1. **`Peak Detection`**

   - Detects steps by identifying peaks in the accelerometer signal

   - Parameters: `window_size`, `threshold`, `min_time_between_steps`

2. **`Zero-Crossing`**

   - Detects steps by analyzing when the signal crosses the zero point

   - Parameters: `window_size`, `min_time_between_steps`, `hysteresis_band`

3. **`Spectral Analysis`**

   - Uses frequency domain analysis to identify periodic step patterns

   - Parameters: `window_size`, `overlap`, `step_freq_range`

4. **`Adaptive Threshold`**

   - Dynamically adjusts the detection threshold based on signal characteristics

   - Parameters: `window_size`, `sensitivity`, `min_time_between_steps`

5. **`SHOE (Step Heading Offset Estimator)`**

   - Combines accelerometer and gyroscope data for improved detection

   - Parameters: `window_size`, `threshold`, `min_time_between_steps`

<br/>

**Each algorithm is evaluated** using `precision`, `recall`, `F1-score`, `step count error`, `execution time` and `MSE (with penalty)` metrics.

<br/><br/>

## Parameter Configuration

<br/>

### GUI and bulk analysis

You can change the parameters for each algorithm in [`./detection_params.json`](./detection_params.json)
Each sensor has its own section

- [`sensor_1`](./detection_params.json#L17-L43)

- [`sensor_2`](./detection_params.json#L45-L71).

<br/>

### TUG Parser

You can change the parameters for each algorithm (and mounting point) in 
[`./parser/sensor_location_params.json`](./parser/sensor_location_params.json).
Each sensor pair has its own section

- [`ankle_params`](./parser/sensor_location_params.json#L14-L40)

- [`wrist_params`](./parser/sensor_location_params.json#L42-L68)

- [`back_params`](./parser/sensor_location_params.json#L70-L96)

<br/>

### Quick Start

For most applications, use the **Normal Walking** configuration from [`SCENARIO_SPECIFIC_PARAMS.md`](SCENARIO_SPECIFIC_PARAMS.md#2-normal-walking).

<br/>

### Detailed Guides

- **[Parameter Tuning Guide](TUNING_PARAMS_GUIDE.md)** - Comprehensive parameter explanations and tuning strategies

- **[Scenario-Specific Parameters](SCENARIO_SPECIFIC_PARAMS.md)** - Ready-to-use configurations for different test protocols:

  - TUG Test (Timed Up and Go)

  - Normal Walking

  - Fast Walking

  - Running/Jogging

  - Stairs Up/Down/Mixed

<br/>

### Universal Configuration Philosophy

All parameter sets should be designed to work **universally across different sensor mounting points** (pocket, wrist, arm, ankle) without requiring algorithm-specific adjustments.

<br/><br/>

## Hardware Connection

This analysis module connects to the Raspberry Pi Pico 2W hardware via HTTP API. For hardware setup instructions, see the [main project README](../README.md#how-to-connect-the-components).

**Required:** Pico 2W running the [main firmware](../main.py) and accessible at `192.168.4.1`

<br/><br/>

## Algorithm Performance

Based on analysis of collected data, typical performance metrics could be:

- **Peak Detection**: Best universal performance across scenarios and mounting points

- **Spectral Analysis**: Good for steady walking patterns

- **Adaptive Threshold**: Robust to signal variations

- **Zero Crossing & SHOE**: Specialized use cases

<br/>

See [`analysis/`](./analysis/) directory for detailed performance comparisons.

<br/><br/>

## Troubleshooting

- **Connection Issues**: Ensure you're connected to the Pico 2W's WiFi network

- **Import Errors**: Check that all dependencies are installed: `pip install -r requirements.txt`

- **GUI Issues**: Ensure Tkinter is available (usually included with Python)

- **Plot Errors**: Check if Matplotlib is installed and application closes properly on `X` button click (threading issues)

- **Parameter Issues**: See [Parameter Tuning Guide](TUNING_PARAMS_GUIDE.md) for troubleshooting specific algorithm behavior

<br/><br/>

---

<br/><br/>

**Part of:** [Master's Thesis - Step Detection with RPi Pico 2W](https://github.com/revalew/Master-Thesis)

**Author:** Maksymilian Kisiel

**Supervisor:** dr hab. inż. Agnieszka Szczęsna, prof. PŚ

<br/><br/>
