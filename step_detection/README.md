# Step Detection Analysis Module

This module contains the data analysis pipeline for the Master's Thesis project on step detection using IMU sensors. For the complete project overview and hardware setup, see the [main README](../README.md).

## Project Structure

```
step_detection/
├── analysis/                    # Analysis results and screenshots
├── data/                        # Data directory for recorded sensor data
├── plots/                       # Generated plots and visualizations
├── requirements.txt             # Python dependencies
├── step_data_collector.py       # Main GUI application for data collection & analysis
├── step_detection_algorithms.py # Implementation of 5 step detection algorithms
└── README.md                    # This file
```

## Installation

1. Create a virtual environment and activate it:

```bash
python3 -m venv venv
```

```bash
source venv/bin/activate # On Windows: venv\Scripts\activate
```

2. Install Python dependencies:

```bash
pip install -r requirements.txt
```

3. Ensure your Pico 2W is accessible on your network (it creates its own access point by default).

## Usage

### Real-time Data Collection & Analysis

Run the GUI application:

```bash
python step_data_collector.py
```

**Features:**
- Connect to Raspberry Pi Pico 2W via API (`http://192.168.4.1/api`)
- Real-time sensor data visualization
- Manual step marking (spacebar or button)
- Live algorithm analysis with 5 different methods
- Save/load recorded sessions
- Export data to CSV format

### Standalone Algorithm Testing

Generate synthetic data and test algorithms:

```bash
python step_detection_algorithms.py
```

This creates example datasets and comprehensive visualizations in the `./plots/` directory.

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

Each algorithm is evaluated using precision, recall, F1-score, and step count error metrics.

## Hardware Connection

This analysis module connects to the Raspberry Pi Pico 2W hardware via HTTP API. For hardware setup instructions, see the [main project README](../README.md#how-to-connect-the-components).

**Required:** Pico 2W running the main firmware and accessible at `192.168.4.1`

## Troubleshooting

- **Connection Issues**: Ensure you're connected to the Pico 2W's WiFi network
- **Import Errors**: Check that all dependencies are installed: `pip install -r requirements.txt`
- **GUI Issues**: Ensure Tkinter is available (usually included with Python)
- **Plot Errors**: Application closes properly on X button click (fixed threading issues)

## Algorithm Performance

Based on analysis of collected data, typical performance metrics:

- **Spectral Analysis**: Best overall F1-score (~0.31)
- **Peak Detection**: Good balance of precision/recall
- **Adaptive Threshold**: Robust to signal variations
- **Zero Crossing & SHOE**: Specialized use cases

See `analysis/` directory for detailed performance comparisons.

---

**Part of:** [Master's Thesis - Step Detection with RPi Pico 2W](../README.md)  
**Author:** Maksymilian Kisiel  
**Supervisor:** dr hab. inż. Agnieszka Szczęsna, prof. PŚ