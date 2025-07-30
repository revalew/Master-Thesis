# Scenario-Specific Parameter Settings

<br/><br/>

This document provides optimized parameter configurations for different walking scenarios and test protocols. Each configuration is designed for **universal mounting points** and should work consistently across different sensor placements.

You can change the parameters for each algorithm in [`./utils/StepDataCollector.py`](./utils/StepDataCollector.py#L1192-L1218) (method `analyze_data`, variable `param_sets`, lines `1192-1218`).

<br/><br/>

## Test Protocol Overview

<br/>

**Recommended Testing:** 7 scenarios × 4 mounting points × 3 repetitions = **84 total tests**

**Mounting Points:**

1. Pocket/thigh

2. Wrist

3. Upper arm

4. Ankle/calf

<br/><br/>

## Configuration Sets

<br/><br/>

### 1. TUG Test (Timed Up and Go)

**Use Case:** Elderly or mobility-impaired subjects with slow, careful movements

<br/>

```python
tug_params = {
    "peak_detection": {
        "window_size": 1.5,
        "threshold": 0.6,
        "min_time_between_steps": 0.6,
    },
    "zero_crossing": {
        "window_size": 0.8,
        "min_time_between_steps": 0.6,
        "hysteresis_band": 0.2,
    },
    "spectral_analysis": {
        "window_size": 8.0,
        "overlap": 0.8,
        "step_freq_range": (0.4, 1.8),
    },
    "adaptive_threshold": {
        "window_size": 1.2,
        "sensitivity": 0.7,
        "min_time_between_steps": 0.6,
    },
    "shoe": {
        "window_size": 0.8,
        "threshold": 0.4,
        "min_time_between_steps": 0.6,
    },
}
```

<br/><br/>

### 2. Normal Walking

**Use Case:** Standard walking pace for healthy adults (baseline configuration)

<br/>

```python
normal_walking_params = {
    "peak_detection": {
        "window_size": 1.0,
        "threshold": 0.8,
        "min_time_between_steps": 0.4,
    },
    "zero_crossing": {
        "window_size": 0.5,
        "min_time_between_steps": 0.4,
        "hysteresis_band": 0.3,
    },
    "spectral_analysis": {
        "window_size": 6.0,
        "overlap": 0.7,
        "step_freq_range": (0.6, 2.5),
    },
    "adaptive_threshold": {
        "window_size": 0.8,
        "sensitivity": 0.5,
        "min_time_between_steps": 0.4,
    },
    "shoe": {
        "window_size": 0.5,
        "threshold": 0.6,
        "min_time_between_steps": 0.4,
    },
}
```

<br/><br/>

### 3. Fast Walking

**Use Case:** Brisk walking pace with shorter step intervals

<br/>

```python
fast_walking_params = {
    "peak_detection": {
        "window_size": 0.8,
        "threshold": 1.0,
        "min_time_between_steps": 0.3,
    },
    "zero_crossing": {
        "window_size": 0.4,
        "min_time_between_steps": 0.3,
        "hysteresis_band": 0.4,
    },
    "spectral_analysis": {
        "window_size": 5.0,
        "overlap": 0.6,
        "step_freq_range": (1.0, 3.5),
    },
    "adaptive_threshold": {
        "window_size": 0.6,
        "sensitivity": 0.4,
        "min_time_between_steps": 0.3,
    },
    "shoe": {
        "window_size": 0.4,
        "threshold": 0.7,
        "min_time_between_steps": 0.3,
    },
}
```

<br/><br/>

### 4. Running/Jogging

**Use Case:** High-frequency movements with significant accelerations

<br/>

```python
running_params = {
    "peak_detection": {
        "window_size": 0.6,
        "threshold": 1.2,
        "min_time_between_steps": 0.25,
    },
    "zero_crossing": {
        "window_size": 0.3,
        "min_time_between_steps": 0.25,
        "hysteresis_band": 0.5,
    },
    "spectral_analysis": {
        "window_size": 4.0,
        "overlap": 0.5,
        "step_freq_range": (1.5, 4.0),
    },
    "adaptive_threshold": {
        "window_size": 0.5,
        "sensitivity": 0.3,
        "min_time_between_steps": 0.25,
    },
    "shoe": {
        "window_size": 0.3,
        "threshold": 0.8,
        "min_time_between_steps": 0.25,
    },
}
```

<br/><br/>

### 5. Stairs Up

**Use Case:** Slower cadence with emphasis on vertical movement patterns

<br/>

```python
stairs_up_params = {
    "peak_detection": {
        "window_size": 1.2,
        "threshold": 0.7,
        "min_time_between_steps": 0.5,
    },
    "zero_crossing": {
        "window_size": 0.6,
        "min_time_between_steps": 0.5,
        "hysteresis_band": 0.25,
    },
    "spectral_analysis": {
        "window_size": 7.0,
        "overlap": 0.75,
        "step_freq_range": (0.5, 2.0),
    },
    "adaptive_threshold": {
        "window_size": 1.0,
        "sensitivity": 0.6,
        "min_time_between_steps": 0.5,
    },
    "shoe": {
        "window_size": 0.6,
        "threshold": 0.5,
        "min_time_between_steps": 0.5,
    },
}
```

<br/><br/>

### 6. Stairs Down

**Use Case:** Controlled movements with different timing patterns

<br/>

```python
stairs_down_params = {
    "peak_detection": {
        "window_size": 1.3,
        "threshold": 0.9,
        "min_time_between_steps": 0.45,
    },
    "zero_crossing": {
        "window_size": 0.7,
        "min_time_between_steps": 0.45,
        "hysteresis_band": 0.35,
    },
    "spectral_analysis": {
        "window_size": 7.5,
        "overlap": 0.75,
        "step_freq_range": (0.5, 2.2),
    },
    "adaptive_threshold": {
        "window_size": 1.1,
        "sensitivity": 0.45,
        "min_time_between_steps": 0.45,
    },
    "shoe": {
        "window_size": 0.7,
        "threshold": 0.65,
        "min_time_between_steps": 0.45,
    },
}
```

<br/><br/>

### 7. Stairs Mixed (Up + Down)

**Use Case:** Compromise settings for combined stair navigation tests

<br/>

```python
stairs_mixed_params = {
    "peak_detection": {
        "window_size": 1.25,
        "threshold": 0.8,
        "min_time_between_steps": 0.48,
    },
    "zero_crossing": {
        "window_size": 0.65,
        "min_time_between_steps": 0.48,
        "hysteresis_band": 0.3,
    },
    "spectral_analysis": {
        "window_size": 7.2,
        "overlap": 0.75,
        "step_freq_range": (0.5, 2.1),
    },
    "adaptive_threshold": {
        "window_size": 1.05,
        "sensitivity": 0.52,
        "min_time_between_steps": 0.48,
    },
    "shoe": {
        "window_size": 0.65,
        "threshold": 0.58,
        "min_time_between_steps": 0.48,
    },
}
```

<br/><br/>

## Implementation Instructions

<br/>

<ol>
   <li> **Choose appropriate scenario** based on your test protocol
   </li>
   <br/>
   
   <li> **Replace default param_sets** in `analyze_data()` method with scenario-specific parameters:
    
<br/>

```python
# In StepDataCollector.py, replace param_sets with:
param_sets = tug_params  # or normal_walking_params, etc.
```

   </li>
   <br/>
   
   <li> **Run tests** with consistent methodology across all mounting points
   </li>
   <br/>
   
   <li> **Fine-tune if needed** using the [Parameter Tuning Guide](TUNING_PARAMS_GUIDE.md)
   </li>
</ol>

<br/><br/>

## Algorithm Recommendations by Scenario

<br/>

| Scenario                | Best Algorithms               | Notes                               |
| ----------------------- | ----------------------------- | ----------------------------------- |
| **TUG/Stairs**          | Adaptive Threshold, SHOE      | Handle irregular patterns well      |
| **Normal/Fast Walking** | Peak Detection                | Most reliable for steady patterns   |
| **Running**             | Zero Crossing, Peak Detection | Handle high frequencies effectively |
| **Mixed Scenarios**     | Peak Detection                | Best universal performance          |

<br/><br/>

## Expected Performance Characteristics

<br/>

**Robustness Testing Hypotheses:**

- **H1**: Peak Detection will show most consistent performance across mounting points

- **H2**: Wrist mounting may show increased noise due to hand movement artifacts

- **H3**: Stair scenarios will be most challenging regardless of mounting location

- **H4**: Algorithm ranking should remain stable across mounting points (universal robustness)

<br/><br/>

---

<br/>

**See also:** [Parameter Tuning Guide](TUNING_PARAMS_GUIDE.md) for detailed parameter explanations

<br/><br/>
