# TUG Data Parser

Independent parser for TUG (Timed Up and Go) test CSV files that converts sensor data and runs step detection analysis with location-specific parameters.

## Quick Start

1. **Setup Files**

   ```bash
   # Place your TUG CSV files in input directory
   mkdir tug_data_raw
   # Copy your 001-left_ankle.csv, 001-right_ankle.csv, etc. files here
   ```

2. **Configure**

   ```bash
   # Edit main configuration (optional)
   vi tug_parser_config.json
   
   # Edit sensor parameters (optional)
   vi sensor_location_params.json
   ```

3. **Run Parser**

   ```bash
   python run_tug_parser.py
   ```

## Output Modes

The parser supports two output modes controlled by `gui_compatibility` setting:

### GUI Compatible Mode (`"gui_compatibility": true`)

Creates structure compatible with existing GUI application:

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

### Simple Mode (`"gui_compatibility": false`)

Creates simple structure with individual sensor files:

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

## Input File Format

### Naming Convention

Files must follow the pattern: `XXX-sensor_location.csv`

Examples:

- `001-left_ankle.csv`

- `001-right_ankle.csv`

- `001-left_wrist.csv`

- `001-right_wrist.csv`

- `001-sacrum_back.csv`

### CSV Format

Required columns:

```csv
PacketCounter,Acc_X,Acc_Y,Acc_Z,Gyr_X,Gyr_Y,Gyr_Z,Roll,Pitch,Yaw
5758,9.867562,0.006708,-0.797566,0.043418,-0.013966,-0.029659,164.128107,-85.361152,0.098424
5759,9.820398,-0.043264,-0.975658,0.040553,-0.01197,-0.052602,163.838922,-85.345859,0.411857
```

## Configuration Files

### Main Configuration (`tug_parser_config.json`)

```json
{
    "input_directory": "./tug_data_raw",
    "output_directory": "./tug_data_processed", 
    "sampling_rate_hz": 100,
    "run_analysis": true,
    "gui_compatibility": false,
    "sensor_location_params_file": "sensor_location_params.json"
}
```

**Key Parameters:**

- **`gui_compatibility`**: `true` for GUI-compatible structure, `false` for simple structure

- **`sampling_rate_hz`**: Sampling rate used to generate timestamps (default: 100 Hz)

- **`run_analysis`**: Whether to automatically run step detection analysis

### Sensor Location Parameters (`sensor_location_params.json`)

Contains optimized parameters for different sensor locations (most probably will try making them the same for all sensors):

- **`ankle_params`**: For left_ankle, right_ankle sensors

- **`wrist_params`**: For left_wrist, right_wrist sensors  

- **`back_params`**: For sacrum_back sensors

Each location has tuned parameters for all algorithms:

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

## Location-Specific Optimization

The parser automatically selects optimal parameters based on sensor location:

| Location | Characteristics | Parameter Adjustments |
|----------|----------------|----------------------|
| **Ankle** | Clearest step signals, lower noise | Smaller windows, higher thresholds, faster detection |
| **Wrist** | More artifacts from arm swing | Larger windows, higher thresholds, noise reduction |
| **Back/Sacrum** | Whole-body movement patterns | Medium windows, moderate thresholds, balanced approach |

## Step Detection Analysis

If `run_analysis` is enabled, the parser runs multiple step detection algorithms:

- **Peak Detection**: Robust algorithm using adaptive thresholds

- **Zero Crossing**: Good for clean signals with hysteresis

- **Spectral Analysis**: Frequency domain analysis for steady walking

- **Adaptive Threshold**: High accuracy with local adaptation

- **SHOE Algorithm**: Multi-sensor approach using stance detection

Results include step count, timing, and frequency analysis.

## Usage Examples

### Basic Processing

```bash
# Process with default settings
python TUGDataParser.py
```

### GUI Compatible Mode

```json
// Set in tug_parser_config.json
{
    "gui_compatibility": true,
    "run_analysis": true
}
```

Result: Can load processed data in original GUI application

### Simple Analysis Mode  

```json
// Set in tug_parser_config.json
{
    "gui_compatibility": false,
    "run_analysis": true
}
```

Result: Individual sensor files with analysis results

### Convert Only (No Analysis)

```json
// Set in tug_parser_config.json
{
    "run_analysis": false
}
```

Result: Just convert CSV format without running step detection

## Output Files Explained

### Simple Mode Files

**`{sensor_location}.csv`**: Converted sensor data

```csv
time,accel_x,accel_y,accel_z,gyro_x,gyro_y,gyro_z,mag_x,mag_y,mag_z
```

**`{sensor_location}_detection_results.yaml`**: Step detection results

```yaml
Peak Detection:
  Execution Time: 0.0123 s
  Detected Steps: 8
  Step Times: [1.2, 2.1, 3.0, ...]
  Step Rate: 0.64 steps/s
```

**`recording_metadata.json`**: Recording information

```json
{
    "recording_id": "001",
    "gui_compatible": false,
    "sensors": [
        {"location": "left_ankle", "duration": 12.45, "samples": 1245}
    ]
}
```

**`processing_summary.json`**: Overall statistics

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

## Performance Notes

- Processing ~600 recordings takes approximately 3-10 minutes depending on hardware

- Simple mode is faster than GUI-compatible mode

- Analysis can be disabled for faster processing if only conversion is needed

- Missing sensor files are handled gracefully (in GUI mode filled with zeros, in simple mode skipped)

- Location-specific parameters provide better accuracy than generic parameters
