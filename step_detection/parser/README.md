# TUG Data Parser

</br>

Independent parser for TUG (Timed Up and Go) test CSV files that converts sensor data and runs step detection analysis with location-specific parameters.

> [!NOTE]
> 
> to use the parser or the simple bulk analyzer, go to the `step_detection` directory and run
>
> `python parser.py`
>
> OR
>
> `python data_analyzer.py`
>
> This will ensure that the imports are available

</br></br>

## In a nutshell

Convert this

</br>

```csv
PacketCounter,Acc_X,Acc_Y,Acc_Z,Gyr_X,Gyr_Y,Gyr_Z,Roll,Pitch,Yaw
5758,9.867562,0.006708,-0.797566,0.043418,-0.013966,-0.029659,164.128107,-85.361152,0.098424
5759,9.820398,-0.043264,-0.975658,0.040553,-0.01197,-0.052602,163.838922,-85.345859,0.411857
```

</br>

to this

</br>

```csv
time,accel_x,accel_y,accel_z,gyro_x,gyro_y,gyro_z,mag_x,mag_y,mag_z
0.0002710,9.8880529,5.83227,0.900219,-0.8409555,0.260866761,-2.71845006,0.0,0.0,0.0
0.0463035,10.175356,2.99035,0.466869,-0.9653935,0.082869835,-2.31662464,0.0,0.0,0.0
```

</br>

and run the analysis.

</br></br>

## Quick Start

<ol>
<li><b>Setup Files</b>

<br/><br/>

```bash
# Place your TUG CSV files in input directory
mkdir tug_data_raw
# Copy your 001-left_ankle.csv, 001-right_ankle.csv, etc. files here
```
    
</li></br>

<li><b>Configure</b>

<br/><br/>

```bash
# Edit main configuration (optional)
vi tug_parser_config.json

# Edit sensor parameters (optional)
vi sensor_location_params.json
```

</li></br>

<li><b>Run Parser</b>

<br/><br/>

```bash
python parser.py
```

</li>
</ol>

</br></br>

## Output Modes

The parser supports two output modes controlled by `gui_compatibility` setting:

</br>

### GUI Compatible Mode (`"gui_compatibility": true`)

Creates structure compatible with existing GUI application:

</br>

```bash
tug_data_processed/
├── 001/
│   ├── ankle_001/
│   │   ├── sensor1_waveshare.csv
│   │   ├── sensor2_adafruit.csv
│   │   ├── ground_truth.csv (empty)
│   │   ├── metadata.json
│   │   └── detection_results.yaml
│   ├── wrist_001/
│   └── sacrum_001/
├── 002/
└── processing_summary.json
```

</br>

### Simple Mode (`"gui_compatibility": false`)

Creates simple structure with individual sensor files:

</br>

```bash
tug_data_processed/
├── 001/
│   ├── left_ankle.csv
│   ├── left_ankle_detection_results.yaml
│   ├── right_ankle.csv
│   ├── right_ankle_detection_results.yaml
│   ├── left_wrist.csv
│   ├── left_wrist_detection_results.yaml
│   ├── right_wrist.csv
│   ├── right_wrist_detection_results.yaml
│   ├── sacrum_back.csv
│   ├── sacrum_back_detection_results.yaml
│   └── recording_metadata.json
├── 002/
└── processing_summary.json
```

</br></br>

## Input File Format

</br>

### Naming Convention

Files must follow the pattern: `XXX-sensor_location.csv`

Examples:

- `001-left_ankle.csv`

- `001-right_ankle.csv`

- `001-left_wrist.csv`

- `001-right_wrist.csv`

- `001-sacrum_back.csv`

</br>

### CSV Format

Required columns:

</br>

```csv
PacketCounter,Acc_X,Acc_Y,Acc_Z,Gyr_X,Gyr_Y,Gyr_Z,Roll,Pitch,Yaw
5758,9.867562,0.006708,-0.797566,0.043418,-0.013966,-0.029659,164.128107,-85.361152,0.098424
5759,9.820398,-0.043264,-0.975658,0.040553,-0.01197,-0.052602,163.838922,-85.345859,0.411857
```

</br></br>

## Configuration Files

</br>

### Main Configuration (`tug_parser_config.json`)

</br>

```json
{
    "input_directory": "./tug_data_raw",
    "output_directory": "./tug_data_processed", 
    "sensor_location_params_file": "sensor_location_params.json",
    "sampling_rate_hz": 100,
    "run_analysis": true,
    "gui_compatibility": false
}
```

</br>

**Key Parameters:**

- **`gui_compatibility`**: `true` for GUI-compatible structure, `false` for simple structure

- **`sampling_rate_hz`**: Sampling rate used to generate timestamps (default: 100 Hz)

- **`run_analysis`**: Whether to automatically run step detection analysis

</br>

### Sensor Location Parameters (`sensor_location_params.json`)

Contains optimized parameters for different sensor locations (most probably will try making them the same for all sensors):

- **`ankle_params`**: For left_ankle, right_ankle sensors

- **`wrist_params`**: For left_wrist, right_wrist sensors  

- **`back_params`**: For sacrum_back sensors

Each location has tuned parameters for all algorithms:

</br>

```json
{
    "ankle_params": {
        "peak_detection": {
            "window_size": 0.4,
            "threshold": 0.6,
            "min_time_between_steps": 0.3
        }
    }
}
```

</br></br>

## Location-Specific Optimization

The parser automatically selects optimal parameters based on sensor location

</br>
<div align="center">

| Location | Characteristics | Parameter Adjustments |
|----------|----------------|----------------------|
| **Ankle** | Clearest step signals, lower noise | Smaller windows, higher thresholds, faster detection |
| **Wrist** | More artifacts from arm swing | Larger windows, higher thresholds, noise reduction |
| **Back/Sacrum** | Whole-body movement patterns | Medium windows, moderate thresholds, balanced approach |

</div>

</br></br>

## Step Detection Analysis

If `run_analysis` is enabled, the parser runs multiple step detection algorithms:

- **Peak Detection**: Robust algorithm using adaptive thresholds

- **Zero Crossing**: Good for clean signals with hysteresis

- **Spectral Analysis**: Frequency domain analysis for steady walking

- **Adaptive Threshold**: High accuracy with local adaptation

- **SHOE Algorithm**: Multi-sensor approach using stance detection

Results include step count, timing, and frequency analysis.

</br></br>

## Usage Examples

</br>

### Basic Processing

</br>

```bash
# Process with default settings
python parser.py
```

</br>

### GUI Compatible Mode

</br>

```json
// Set in tug_parser_config.json
{
    "gui_compatibility": true,
    "run_analysis": true
}
```

</br>

Result: Can load processed data in original GUI application

</br>

### Simple Analysis Mode  

</br>

```json
// Set in tug_parser_config.json
{
    "gui_compatibility": false,
    "run_analysis": true
}
```

</br>

Result: Individual sensor files with analysis results

</br>

### Convert Only (No Analysis)

</br>

```json
// Set in tug_parser_config.json
{
    "run_analysis": false
}
```

</br>

Result: Just convert CSV format without running step detection

</br></br>

## Output Files Explained

**`{sensor_location}.csv`**: Converted sensor data

</br>

```csv
time,accel_x,accel_y,accel_z,gyro_x,gyro_y,gyro_z,mag_x,mag_y,mag_z
```

</br>

**`{sensor_location}_detection_results.yaml`**: Step detection results

</br>

```yaml
Peak Detection:
  Execution Time: 0.0123 s
  Detected Steps: 8
  Step Times: [1.2, 2.1, 3.0, ...]
  Step Rate: 0.64 steps/s
```

</br>

**`recording_metadata.json`**: Recording information

</br>

```json
{
    "recording_id": "001",
    "gui_compatible": false,
    "sensors": [
        {"location": "left_ankle", "duration": 12.45, "samples": 1245}
    ]
}
```

</br>

**`processing_summary.json`**: Overall statistics

</br>

```json
{
    "duration_seconds": 0.075246,
    "total_recordings": 771,
    "successful_analysis": 3855,
    "gui_compatibility_mode": false,
    "recordings": {
        "001": {
            "left_ankle": "analyzed",
            "right_ankle": "analyzed"
        }
    }
}
```

</br></br>

## Performance Notes

- Processing ~600 recordings takes approximately 1-5 minutes depending on hardware

- Simple mode is faster than GUI-compatible mode

- Analysis can be disabled for faster processing if only conversion is needed

- Missing sensor files are handled gracefully (in GUI mode filled with zeros, in simple mode skipped)

- Location-specific parameters provide better accuracy than generic parameters

</br></br>
