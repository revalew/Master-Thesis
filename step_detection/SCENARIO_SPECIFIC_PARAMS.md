# Scenario-Specific Parameter Settings

<br/><br/>

This document provides optimized parameter configurations for different walking scenarios and test protocols. Each configuration is designed for **universal mounting points** and **22Hz sampling rate** based on the test results.

You can change the parameters for each algorithm in [`./utils/StepDataCollector.py`](./utils/StepDataCollector.py#L1191-L1220) (method `analyze_data`, variable `param_sets`, lines `1191-1220`).

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
        "window_size": 0.8,
        "threshold": 0.4,
        "min_time_between_steps": 0.55,
    },
    "zero_crossing": {
        "window_size": 0.7,
        "min_time_between_steps": 0.55,
        "hysteresis_band": 0.25,
    },
    "spectral_analysis": {
        "window_size": 9.0,
        "overlap": 0.8,
        "step_freq_range": (0.5, 1.8),
    },
    "adaptive_threshold": {
        "window_size": 1.0,
        "sensitivity": 0.6,
        "min_time_between_steps": 0.55,
    },
    "shoe": {
        "window_size": 0.4,
        "threshold": 7.5,
        "min_time_between_steps": 0.55,
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
        "window_size": 0.6,
        "threshold": 0.5,
        "min_time_between_steps": 0.35,
    },
    "zero_crossing": {
        "window_size": 0.5,
        "min_time_between_steps": 0.4,
        "hysteresis_band": 0.3,
    },
    "spectral_analysis": {
        "window_size": 8.0,
        "overlap": 0.8,
        "step_freq_range": (0.8, 2.0),
    },
    "adaptive_threshold": {
        "window_size": 0.8,
        "sensitivity": 0.5,
        "min_time_between_steps": 0.4,
    },
    "shoe": {
        "window_size": 0.3,
        "threshold": 9.0,
        "min_time_between_steps": 0.35,
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
        "window_size": 0.5,
        "threshold": 0.6,
        "min_time_between_steps": 0.3,
    },
    "zero_crossing": {
        "window_size": 0.4,
        "min_time_between_steps": 0.3,
        "hysteresis_band": 0.35,
    },
    "spectral_analysis": {
        "window_size": 7.0,
        "overlap": 0.75,
        "step_freq_range": (1.0, 2.5),
    },
    "adaptive_threshold": {
        "window_size": 0.6,
        "sensitivity": 0.4,
        "min_time_between_steps": 0.3,
    },
    "shoe": {
        "window_size": 0.25,
        "threshold": 10.0,
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
        "window_size": 0.4,
        "threshold": 0.7,
        "min_time_between_steps": 0.25,
    },
    "zero_crossing": {
        "window_size": 0.3,
        "min_time_between_steps": 0.25,
        "hysteresis_band": 0.4,
    },
    "spectral_analysis": {
        "window_size": 6.0,
        "overlap": 0.7,
        "step_freq_range": (1.5, 3.5),
    },
    "adaptive_threshold": {
        "window_size": 0.5,
        "sensitivity": 0.35,
        "min_time_between_steps": 0.25,
    },
    "shoe": {
        "window_size": 0.2,
        "threshold": 11.0,
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
        "window_size": 0.7,
        "threshold": 0.45,
        "min_time_between_steps": 0.45,
    },
    "zero_crossing": {
        "window_size": 0.6,
        "min_time_between_steps": 0.45,
        "hysteresis_band": 0.28,
    },
    "spectral_analysis": {
        "window_size": 8.5,
        "overlap": 0.8,
        "step_freq_range": (0.6, 1.8),
    },
    "adaptive_threshold": {
        "window_size": 0.9,
        "sensitivity": 0.55,
        "min_time_between_steps": 0.45,
    },
    "shoe": {
        "window_size": 0.35,
        "threshold": 8.5,
        "min_time_between_steps": 0.45,
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
        "window_size": 0.7,
        "threshold": 0.55,
        "min_time_between_steps": 0.4,
    },
    "zero_crossing": {
        "window_size": 0.6,
        "min_time_between_steps": 0.4,
        "hysteresis_band": 0.32,
    },
    "spectral_analysis": {
        "window_size": 8.5,
        "overlap": 0.8,
        "step_freq_range": (0.6, 2.0),
    },
    "adaptive_threshold": {
        "window_size": 0.9,
        "sensitivity": 0.48,
        "min_time_between_steps": 0.4,
    },
    "shoe": {
        "window_size": 0.35,
        "threshold": 9.5,
        "min_time_between_steps": 0.4,
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
        "window_size": 0.7,
        "threshold": 0.5,
        "min_time_between_steps": 0.42,
    },
    "zero_crossing": {
        "window_size": 0.6,
        "min_time_between_steps": 0.42,
        "hysteresis_band": 0.3,
    },
    "spectral_analysis": {
        "window_size": 8.5,
        "overlap": 0.8,
        "step_freq_range": (0.6, 1.9),
    },
    "adaptive_threshold": {
        "window_size": 0.9,
        "sensitivity": 0.52,
        "min_time_between_steps": 0.42,
    },
    "shoe": {
        "window_size": 0.35,
        "threshold": 9.0,
        "min_time_between_steps": 0.42,
    },
}
```

<br/><br/>

## Implementation Instructions

<br/>

<ol>
   <li> <b>Choose appropriate scenario</b> based on your test protocol
   </li>
   <br/>
   
   <li> <b>Replace default param_sets</b> in <code>analyze_data()</code> method with scenario-specific parameters:
    
<br/>

```python
# In StepDataCollector.py, replace param_sets with:
param_sets = normal_walking_params  # or tug_params, fast_walking_params, etc.
```

   </li>
   <br/>
   
   <li> <b>Run tests</b> with consistent methodology across all mounting points
   </li>
   <br/>
   
   <li> <b>Fine-tune if needed</b> using the <a href="./TUNING_PARAMS_GUIDE.md">Parameter Tuning Guide</a>
   </li>
</ol>

<br/><br/>

## Algorithm Recommendations by Scenario

<br/>

| Scenario                | Best Algorithms                | Notes                               |
| ----------------------- | ------------------------------ | ----------------------------------- |
| **TUG/Stairs**          | Adaptive Thr., SHOE, Peak Det. | Handle irregular patterns well      |
| **Normal/Fast Walking** | Peak Detection, Adaptive Thr.  | Most reliable for steady patterns   |
| **Running**             | Peak Detection, Zero Crossing  | Handle high frequencies effectively |
| **Mixed Scenarios**     | Peak Detection                 | Best universal performance          |

<br/><br/>

<!-- **Hypotheses:**

- **H1**: Peak Detection shows most consistent performance across mounting points

- **H2**: Wrist mounting shows manageable noise with proper filtering

- **H3**: Stair scenarios benefit from longer window sizes and adjusted frequency ranges

- **H4**: Algorithm ranking remains stable with universal parameter sets

<br/><br/> -->

## Critical Parameter Notes for 22Hz

<br/>

**SHOE Algorithm:** Requires `threshold=9.0` (much higher than literature values of $`[0.5, 0.8]`$) due to **mounting point characteristics**. SHOE was designed for foot-mounted sensors where true stance phases occur (foot stationary on ground). With pocket/wrist mounting, there are no true stationary periods during walking. The algorithm expects `accel_var < 0.075` and `gyro_mean < 0.045`, but pocket mounting produces minimum values of `accel_var` $`\thickapprox \mathbf{0.47}`$ and `gyro_mean` $`\thickapprox \mathbf{1.33}`$. The high threshold ($`9.0`$) compensates by relaxing stance detection criteria to find quasi-stationary periods in continuous motion.

**Window Sizes:** All window sizes optimized for $`22 Hz`$ - do not use with higher sampling rates without adjustment.

**Frequency Ranges:** Spectral analysis ranges tuned for $`22 Hz`$ resolution and typical walking speeds.

<br/><br/>

---

<br/>

**See also:** [Parameter Tuning Guide](TUNING_PARAMS_GUIDE.md) for detailed parameter explanations

<br/><br/>
