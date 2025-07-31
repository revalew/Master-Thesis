# Step Detection Algorithm Parameters Guide

<br/><br/>

This guide provides comprehensive parameter tuning instructions for the step detection algorithms, optimized for **22Hz sampling rate**.

You can change the parameters for each algorithm in [`./utils/StepDataCollector.py`](./utils/StepDataCollector.py#L1191-L1220) (method `analyze_data`, variable `param_sets`, lines `1191-1220`).

<br/><br/>

## General Tuning Guidelines

<br/>

**Common Issues & Solutions:**

- **Too many false positives**: INCREASE `threshold`/`sensitivity`, INCREASE `min_time_between_steps`

- **Missing steps**: DECREASE `threshold`/`sensitivity`, DECREASE `min_time_between_steps`

- **Noisy results**: INCREASE `window_size` for all algorithms

- **Delayed response**: DECREASE `window_size` for all algorithms

- **For 22Hz sampling**: INCREASE all `window_size` parameters compared to higher sampling rates

<br/><br/>

## Parameter Ranges

<br/>

| Parameter                 | Range        | Description                                 |
| ------------------------- | ------------ | ------------------------------------------- |
| `window_size`             | 0.3-2.0s     | 22Hz needs longer windows than 100Hz        |
| `min_time_between_steps`  | 0.25-0.6s    | Physiological limits: slow=0.6s, fast=0.25s |
| `threshold`/`sensitivity` | 0.3-1.2      | Lower=more sensitive, higher=more selective |
| `hysteresis_band`         | 0.1-0.8 m/s² | Clean data=0.1, noisy=0.8                   |
| `overlap`                 | 0.5-0.8      | Higher overlap=smoother but slower          |
| `step_freq_range`         | (0.5-3.0) Hz | Typical walking: 0.8-2.5 Hz                 |

<br/><br/>

## Default Configuration (tested on 22Hz)

<br/>

```python
param_sets = {
    "peak_detection": {
        "window_size": 0.6,                 # Smoothing window (seconds)
        "threshold": 0.5,                   # Adaptive threshold multiplier
        "min_time_between_steps": 0.35,     # Minimum step interval (seconds)
    },
    "zero_crossing": {
        "window_size": 0.5,                 # Smoothing window (seconds)
        "min_time_between_steps": 0.4,      # Minimum step interval (seconds)
        "hysteresis_band": 0.3,             # Hysteresis threshold (m/s²)
    },
    "spectral_analysis": {
        "window_size": 8.0,                 # STFT window (seconds)
        "overlap": 0.8,                     # STFT overlap (0-1)
        "step_freq_range": (0.8, 2.0),      # Walking frequency range (Hz)
    },
    "adaptive_threshold": {
        "window_size": 0.8,                 # Smoothing window (seconds)
        "sensitivity": 0.5,                 # Threshold sensitivity (0-1)
        "min_time_between_steps": 0.4,      # Minimum step interval (seconds)
    },
    "shoe": {
        "window_size": 0.3,                 # Smoothing window (seconds)
        "threshold": 9.0,                   # Stance detection threshold
        "min_time_between_steps": 0.35,     # Minimum step interval (seconds)
    },
}
```

<br/><br/>

## Algorithm-Specific Guidelines

<br/>

### Peak Detection

**Characteristics:** Most robust algorithm, good starting point

**Tuning:**

- Current optimal: `window_size=0.6`, `threshold=0.5`

- If oversensitive: increase `threshold` to 0.7-0.9

- For noisy data: increase `window_size` to 0.8-1.0s

<br/>

### Zero Crossing

**Characteristics:** Best for clean signals

**Tuning:**

- Current optimal: `hysteresis_band=0.3`

- If chattering occurs: increase `hysteresis_band` to 0.4-0.5

- For weak steps: decrease `hysteresis_band` to 0.2

<br/>

### Spectral Analysis

**Characteristics:** Excellent for steady walking patterns

**Tuning:**

- Current optimal: `window_size=8.0s`, `step_freq_range=(0.8, 2.0)`

- For better frequency resolution: increase `window_size` to 10-12s

- For faster response: decrease `window_size` to 6-7s

- Adjust `step_freq_range` based on expected walking speed

<br/>

### Adaptive Threshold

**Characteristics:** Best accuracy but sensitive to noise

**Tuning:**

- Current optimal: `sensitivity=0.5`, `window_size=0.8`

- For noisy data: lower `sensitivity` to 0.3-0.4

- For better consistency: increase `window_size` to 1.0-1.2s

<br/>

### SHOE Algorithm

**Characteristics:** Best for complex movements, multi-sensor fusion

**Tuning:**

- **Critical:** Use `threshold=9.0` for 22Hz sampling (much higher than typical 0.5-0.8 - [check why](./SCENARIO_SPECIFIC_PARAMS.md#critical-parameter-notes-for-22hz))

- If too many false detections: increase `threshold` to 10-12

- For better stance detection: decrease `threshold` to 7-8

- Lower sampling rates may need different threshold values

<br/><br/>

## Walking Speed Adjustments

<br/>

### Slow Walking

```python
# Adjust these parameters for elderly or TUG tests
min_time_between_steps = 0.5-0.6  # Longer step intervals
# Decrease all thresholds by 20% for higher sensitivity
```

<br/>

### Fast Walking/Running

```python
# Adjust these parameters for brisk walking or jogging
min_time_between_steps = 0.25-0.3  # Shorter step intervals
# Increase all thresholds by 20% for noise reduction
```

<br/><br/>

---

<br/>

**See also:** [Scenario-Specific Parameters](SCENARIO_SPECIFIC_PARAMS.md) for ready-to-use configurations

<br/><br/>