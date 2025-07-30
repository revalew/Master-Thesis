# Step Detection Analysis Module

<br/><br/>

This module contains the data analysis pipeline for the Master's Thesis project on step detection using IMU sensors. For the complete project overview and hardware setup, see the [main README](../README.md).

<br/><br/>

## Project Structure

<br/>

```
step_detection/
├── analysis/                    # Analysis results and screenshots
├── data/                        # Data directory for recorded sensor data
├── plots/                       # Generated plots and visualizations
├── utils/                       # Module with the GUI app and algorithm implementations
├── requirements.txt             # Python dependencies
├── step_data_collector.py       # Main
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

- Save/load recorded sessions

- Export data to CSV format

<br/>

### Standalone Algorithm Testing

Generate synthetic data and test algorithms:

<br/>

```bash
python step_detection_algorithms.py
```

<br/>

This creates example datasets and comprehensive visualizations in the [`./plots/`](./plots/) directory.

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

You can change the parameters for each algorithm in [`./utils/StepDataCollector.py`](./utils/StepDataCollector.py#L1192-L1218) (method `analyze_data`, variable `param_sets`, lines `1192-1218`).

<br/>

### Quick Start

For most applications, use the **Normal Walking** configuration from [`SCENARIO_SPECIFIC_PARAMS.md`](SCENARIO_SPECIFIC_PARAMS.md).

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

All parameter sets are designed to work **universally across different sensor mounting points** (pocket, wrist, arm, ankle) without requiring algorithm-specific adjustments.

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
