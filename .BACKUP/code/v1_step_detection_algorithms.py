import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from scipy import signal
from scipy.fft import fft, fftfreq
import os
from datetime import datetime
import json

# --------------------------------
# Sample Data Generation Functions
# --------------------------------

def generate_walking_data(duration=60, fs=50, noise_level=0.1, 
                          step_freq=1.8, sensor_bias=0.0, seed=None):
    """
    Generate synthetic accelerometer data that simulates walking.
    
    Parameters:
    - duration: Duration of the recording in seconds
    - fs: Sampling frequency in Hz
    - noise_level: Standard deviation of the noise
    - step_freq: Step frequency in Hz (typical walking ~1.5-2.0 Hz)
    - sensor_bias: Bias to add to the signal (to simulate different sensors)
    - seed: Random seed for reproducibility
    
    Returns:
    - time: Time array
    - accel_x, accel_y, accel_z: Accelerometer data for three axes
    - gyro_x, gyro_y, gyro_z: Gyroscope data for three axes
    - mag_x, mag_y, mag_z: Magnetometer data for three axes
    - step_times: Array of actual step times for ground truth
    """
    if seed is not None:
        np.random.seed(seed)
        
    # Time array
    time = np.arange(0, duration, 1/fs)
    n_samples = len(time)
    
    # Generate steps (ground truth)
    # Each step is approximately 1/step_freq seconds apart
    # But we add some variability to make it realistic
    step_interval = 1/step_freq
    step_times = []
    next_step = np.random.uniform(0, step_interval/2)  # Random start
    
    while next_step < duration:
        step_times.append(next_step)
        # Add some variability to step interval (±10%)
        next_step += step_interval * np.random.uniform(0.9, 1.1)
    
    # Create base signals
    # Accelerometer Z-axis shows the most distinct pattern during walking
    accel_z = np.zeros(n_samples)
    
    # For each step, create a characteristic double-bump pattern
    for step_time in step_times:
        # Find the indices corresponding to this step
        step_idx = int(step_time * fs)
        if step_idx >= n_samples:
            continue
            
        # Duration of the step impact (in samples)
        impact_duration = int(0.3 * fs)  # 300ms
        if step_idx + impact_duration >= n_samples:
            impact_duration = n_samples - step_idx - 1
            
        # Create the double-bump pattern (heel strike followed by toe push-off)
        t = np.linspace(0, 1, impact_duration)
        # First bump (heel strike) - negative acceleration
        heel_strike = -2.5 * np.exp(-(t[:len(t)//2]-0.2)**2 / 0.01)
        # Second bump (toe push-off) - positive acceleration
        toe_pushoff = 3.0 * np.exp(-(t[len(t)//2:]-0.7)**2 / 0.02)
        
        # Combine the two parts
        pattern = np.concatenate([heel_strike, toe_pushoff])
        
        # Add the pattern to the signal at the step time
        end_idx = min(step_idx + impact_duration, n_samples)
        pattern_len = end_idx - step_idx
        accel_z[step_idx:end_idx] += pattern[:pattern_len]
    
    # Add gravity component (9.81 m/s²) to Z axis
    accel_z += 9.81
    
    # Generate X and Y acceleration with less pronounced patterns
    accel_x = np.zeros(n_samples)
    accel_y = np.zeros(n_samples)
    
    # Add some lateral movement during walking
    for step_time in step_times:
        step_idx = int(step_time * fs)
        if step_idx >= n_samples:
            continue
            
        impact_duration = int(0.3 * fs)
        if step_idx + impact_duration >= n_samples:
            impact_duration = n_samples - step_idx - 1
            
        t = np.linspace(0, 1, impact_duration)
        
        # Alternating lateral movement (X-axis)
        # This simulates the side-to-side sway during walking
        if len(step_times) % 2 == 0:  # Alternate the direction
            x_pattern = 1.0 * np.sin(np.pi * t)
        else:
            x_pattern = -1.0 * np.sin(np.pi * t)
            
        # Forward acceleration/deceleration (Y-axis)
        y_pattern = 0.8 * np.sin(2 * np.pi * t)
        
        end_idx = min(step_idx + impact_duration, n_samples)
        pattern_len = end_idx - step_idx
        
        accel_x[step_idx:end_idx] += x_pattern[:pattern_len]
        accel_y[step_idx:end_idx] += y_pattern[:pattern_len]
    
    # Generate gyroscope data
    # During walking, there's rotation around all three axes
    gyro_x = np.zeros(n_samples)  # Frontal axis (side-to-side tilting)
    gyro_y = np.zeros(n_samples)  # Sagittal axis (forward-backward tilting)
    gyro_z = np.zeros(n_samples)  # Vertical axis (turning)
    
    for step_time in step_times:
        step_idx = int(step_time * fs)
        if step_idx >= n_samples:
            continue
            
        impact_duration = int(0.3 * fs)
        if step_idx + impact_duration >= n_samples:
            impact_duration = n_samples - step_idx - 1
            
        t = np.linspace(0, 1, impact_duration)
        
        # X rotation (frontal axis - side tilting during weight shift)
        if len(step_times) % 2 == 0:
            x_rot = 0.4 * np.sin(np.pi * t)
        else:
            x_rot = -0.4 * np.sin(np.pi * t)
            
        # Y rotation (sagittal axis - forward lean during step)
        y_rot = 0.3 * np.sin(2 * np.pi * t - np.pi/4)
        
        # Z rotation (vertical axis - slight turning during walk)
        z_rot = 0.1 * np.sin(np.pi * t)
        
        end_idx = min(step_idx + impact_duration, n_samples)
        pattern_len = end_idx - step_idx
        
        gyro_x[step_idx:end_idx] += x_rot[:pattern_len]
        gyro_y[step_idx:end_idx] += y_rot[:pattern_len]
        gyro_z[step_idx:end_idx] += z_rot[:pattern_len]
    
    # Generate magnetometer data
    # This would depend on orientation relative to Earth's magnetic field
    # For simplicity, we'll create patterns similar to gyro but with different phase
    mag_x = 20 + 2 * np.sin(2 * np.pi * 0.1 * time) + sensor_bias
    mag_y = 40 + 2 * np.sin(2 * np.pi * 0.1 * time + np.pi/3) + sensor_bias
    mag_z = 30 + 1 * np.sin(2 * np.pi * 0.1 * time + np.pi/6) + sensor_bias
    
    # Add noise to all signals
    accel_x += np.random.normal(0, noise_level, n_samples) + sensor_bias
    accel_y += np.random.normal(0, noise_level, n_samples) + sensor_bias
    accel_z += np.random.normal(0, noise_level, n_samples) + sensor_bias
    
    gyro_x += np.random.normal(0, noise_level*0.5, n_samples) + sensor_bias*0.1
    gyro_y += np.random.normal(0, noise_level*0.5, n_samples) + sensor_bias*0.1
    gyro_z += np.random.normal(0, noise_level*0.5, n_samples) + sensor_bias*0.1
    
    mag_x += np.random.normal(0, noise_level*2, n_samples)
    mag_y += np.random.normal(0, noise_level*2, n_samples)
    mag_z += np.random.normal(0, noise_level*2, n_samples)
    
    return time, accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z, mag_x, mag_y, mag_z, step_times

def generate_datasets():
    """
    Generate multiple datasets for different walking scenarios and sensors.
    """
    scenarios = {
        'normal_walking': {'duration': 60, 'fs': 50, 'noise_level': 0.1, 'step_freq': 1.8},
        'fast_walking': {'duration': 60, 'fs': 50, 'noise_level': 0.12, 'step_freq': 2.3},
        'slow_walking': {'duration': 60, 'fs': 50, 'noise_level': 0.08, 'step_freq': 1.2},
        'stairs_up': {'duration': 60, 'fs': 50, 'noise_level': 0.15, 'step_freq': 1.5},
        'stairs_down': {'duration': 60, 'fs': 50, 'noise_level': 0.15, 'step_freq': 1.6}
    }
    
    datasets = {}
    
    for scenario_name, params in scenarios.items():
        # Generate data for sensor 1 (Waveshare)
        time, ax1, ay1, az1, gx1, gy1, gz1, mx1, my1, mz1, steps = generate_walking_data(
            duration=params['duration'],
            fs=params['fs'],
            noise_level=params['noise_level'],
            step_freq=params['step_freq'],
            sensor_bias=0.05,  # Slight bias for sensor 1
            seed=42  # Fixed seed for reproducibility
        )
        
        # Generate data for sensor 2 (Adafruit) with slightly different characteristics
        _, ax2, ay2, az2, gx2, gy2, gz2, mx2, my2, mz2, _ = generate_walking_data(
            duration=params['duration'],
            fs=params['fs'],
            noise_level=params['noise_level'] * 0.8,  # Slightly less noise (better sensor)
            step_freq=params['step_freq'],
            sensor_bias=-0.03,  # Different bias for sensor 2
            seed=42  # Same seed to keep the step pattern the same
        )
        
        # Store the data
        datasets[scenario_name] = {
            'time': time,
            'sensor1': {
                'accel_x': ax1, 'accel_y': ay1, 'accel_z': az1,
                'gyro_x': gx1, 'gyro_y': gy1, 'gyro_z': gz1,
                'mag_x': mx1, 'mag_y': my1, 'mag_z': mz1
            },
            'sensor2': {
                'accel_x': ax2, 'accel_y': ay2, 'accel_z': az2,
                'gyro_x': gx2, 'gyro_y': gy2, 'gyro_z': gz2,
                'mag_x': mx2, 'mag_y': my2, 'mag_z': mz2
            },
            'ground_truth': {
                'step_times': steps,
                'step_count': len(steps)
            },
            'params': params
        }
    
    return datasets

def save_datasets(datasets, output_dir='./data'):
    """
    Save the generated datasets to CSV files.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    for scenario_name, data in datasets.items():
        # Create scenario directory
        scenario_dir = os.path.join(output_dir, scenario_name)
        if not os.path.exists(scenario_dir):
            os.makedirs(scenario_dir)
        
        # Save sensor 1 data
        sensor1_df = pd.DataFrame({
            'time': data['time'],
            'accel_x': data['sensor1']['accel_x'],
            'accel_y': data['sensor1']['accel_y'],
            'accel_z': data['sensor1']['accel_z'],
            'gyro_x': data['sensor1']['gyro_x'],
            'gyro_y': data['sensor1']['gyro_y'],
            'gyro_z': data['sensor1']['gyro_z'],
            'mag_x': data['sensor1']['mag_x'],
            'mag_y': data['sensor1']['mag_y'],
            'mag_z': data['sensor1']['mag_z']
        })
        sensor1_df.to_csv(os.path.join(scenario_dir, 'sensor1_waveshare.csv'), index=False)
        
        # Save sensor 2 data
        sensor2_df = pd.DataFrame({
            'time': data['time'],
            'accel_x': data['sensor2']['accel_x'],
            'accel_y': data['sensor2']['accel_y'],
            'accel_z': data['sensor2']['accel_z'],
            'gyro_x': data['sensor2']['gyro_x'],
            'gyro_y': data['sensor2']['gyro_y'],
            'gyro_z': data['sensor2']['gyro_z'],
            'mag_x': data['sensor2']['mag_x'],
            'mag_y': data['sensor2']['mag_y'],
            'mag_z': data['sensor2']['mag_z']
        })
        sensor2_df.to_csv(os.path.join(scenario_dir, 'sensor2_adafruit.csv'), index=False)
        
        # Save ground truth data
        ground_truth_df = pd.DataFrame({
            'step_times': data['ground_truth']['step_times']
        })
        ground_truth_df.to_csv(os.path.join(scenario_dir, 'ground_truth.csv'), index=False)
        
        # Save parameters as JSON
        with open(os.path.join(scenario_dir, 'params.json'), 'w') as f:
            json.dump({
                'duration': data['params']['duration'],
                'sampling_frequency': data['params']['fs'],
                'noise_level': data['params']['noise_level'],
                'step_frequency': data['params']['step_freq'],
                'step_count': data['ground_truth']['step_count']
            }, f, indent=4)

# --------------------------------
# Step Detection Algorithms
# --------------------------------

def peak_detection_algorithm(accel_data, fs, window_size=0.1, threshold=1.0, min_time_between_steps=0.3):
    """
    Step detection using peak detection with fixed threshold.
    
    Parameters:
    - accel_data: Accelerometer data (3D array [x, y, z])
    - fs: Sampling frequency in Hz
    - window_size: Size of the moving average window in seconds
    - threshold: Threshold for peak detection
    - min_time_between_steps: Minimum time between consecutive steps in seconds
    
    Returns:
    - detected_steps: Array of detected step times
    """
    # Calculate the magnitude of acceleration (removing gravity)
    accel_mag = np.sqrt(accel_data[0]**2 + accel_data[1]**2 + (accel_data[2] - 9.81)**2)
    
    # Apply moving average filter
    window_len = int(window_size * fs)
    if window_len % 2 == 0:
        window_len += 1  # Make sure window length is odd
    
    filtered_signal = signal.savgol_filter(accel_mag, window_len, 2)
    
    # Find peaks
    min_distance = int(min_time_between_steps * fs)
    peaks, _ = signal.find_peaks(filtered_signal, height=threshold, distance=min_distance)
    
    # Convert peak indices to times
    detected_steps = peaks / fs
    
    return detected_steps, filtered_signal

def zero_crossing_algorithm(accel_data, fs, window_size=0.1, min_time_between_steps=0.3):
    """
    Step detection using zero-crossing method.
    
    Parameters:
    - accel_data: Accelerometer data (3D array [x, y, z])
    - fs: Sampling frequency in Hz
    - window_size: Size of the moving average window in seconds
    - min_time_between_steps: Minimum time between consecutive steps in seconds
    
    Returns:
    - detected_steps: Array of detected step times
    """
    # Use vertical acceleration (Z-axis) after removing gravity
    accel_z = accel_data[2] - 9.81
    
    # Apply moving average filter
    window_len = int(window_size * fs)
    if window_len % 2 == 0:
        window_len += 1  # Make sure window length is odd
    
    filtered_signal = signal.savgol_filter(accel_z, window_len, 2)
    
    # Find zero crossings with positive slope
    zero_crossings = np.where(np.diff(np.signbit(filtered_signal)))[0]
    
    # Keep only positive slope zero crossings
    pos_slope = zero_crossings[np.where(filtered_signal[zero_crossings+1] > filtered_signal[zero_crossings])]
    
    # Apply minimum time between steps
    min_samples = int(min_time_between_steps * fs)
    
    # Filter out crossings that are too close
    filtered_crossings = []
    if len(pos_slope) > 0:
        filtered_crossings = [pos_slope[0]]
        for crossing in pos_slope[1:]:
            if crossing - filtered_crossings[-1] >= min_samples:
                filtered_crossings.append(crossing)
    
    # Convert to numpy array and to times
    detected_steps = np.array(filtered_crossings) / fs
    
    return detected_steps, filtered_signal

def spectral_analysis_algorithm(accel_data, fs, window_size=5.0, overlap=0.5, step_freq_range=(1.0, 2.5)):
    """
    Step detection using spectral analysis.
    
    Parameters:
    - accel_data: Accelerometer data (3D array [x, y, z])
    - fs: Sampling frequency in Hz
    - window_size: Size of FFT window in seconds
    - overlap: Overlap between consecutive windows (0-1)
    - step_freq_range: Range of expected step frequencies in Hz
    
    Returns:
    - detected_steps: Array of detected step times
    """
    # Calculate the magnitude of acceleration (removing gravity)
    accel_mag = np.sqrt(accel_data[0]**2 + accel_data[1]**2 + (accel_data[2] - 9.81)**2)
    
    # Parameters for the STFT
    nperseg = int(window_size * fs)
    noverlap = int(nperseg * overlap)
    
    # Compute STFT
    f, t, Zxx = signal.stft(accel_mag, fs=fs, nperseg=nperseg, noverlap=noverlap)
    
    # Find the frequency bin indices corresponding to the step frequency range
    freq_min_idx = np.argmin(np.abs(f - step_freq_range[0]))
    freq_max_idx = np.argmin(np.abs(f - step_freq_range[1]))
    
    # For each time window, find the dominant frequency in the step frequency range
    step_freqs = []
    for i in range(Zxx.shape[1]):
        # Get the power spectrum for this time window
        power_spectrum = np.abs(Zxx[:, i])
        
        # Find the dominant frequency in the step frequency range
        dom_freq_idx = freq_min_idx + np.argmax(power_spectrum[freq_min_idx:freq_max_idx+1])
        step_freqs.append(f[dom_freq_idx])
    
    # Calculate the number of steps in each window
    # Number of steps = frequency (steps/sec) * window duration (sec)
    # We use overlap to avoid double counting
    effective_window_duration = window_size * (1 - overlap)
    steps_per_window = np.array(step_freqs) * effective_window_duration
    
    # Total number of steps is the sum of steps in each window
    total_steps = int(np.sum(steps_per_window))
    
    # We don't have exact step times from this method, so we'll distribute them evenly
    # This is a limitation of the spectral approach
    time_duration = accel_mag.size / fs
    if total_steps > 0:
        # Distribute steps evenly
        step_interval = time_duration / total_steps
        detected_steps = np.arange(step_interval/2, time_duration, step_interval)
    else:
        detected_steps = np.array([])
    
    return detected_steps, np.array(step_freqs)

def adaptive_threshold_algorithm(accel_data, fs, window_size=0.1, sensitivity=0.6, min_time_between_steps=0.3):
    """
    Step detection using adaptive thresholding.
    
    Parameters:
    - accel_data: Accelerometer data (3D array [x, y, z])
    - fs: Sampling frequency in Hz
    - window_size: Size of the moving average window in seconds
    - sensitivity: Sensitivity parameter (0-1) controlling the adaptive threshold
    - min_time_between_steps: Minimum time between consecutive steps in seconds
    
    Returns:
    - detected_steps: Array of detected step times
    """
    # Calculate the magnitude of acceleration (removing gravity)
    accel_mag = np.sqrt(accel_data[0]**2 + accel_data[1]**2 + (accel_data[2] - 9.81)**2)
    
    # Apply moving average filter
    window_len = int(window_size * fs)
    if window_len % 2 == 0:
        window_len += 1  # Make sure window length is odd
    
    filtered_signal = signal.savgol_filter(accel_mag, window_len, 2)
    
    # Calculate the adaptive threshold using a longer window
    long_window = int(2.0 * fs)  # 2-second window
    
    # Compute the running mean and standard deviation
    running_mean = np.zeros_like(filtered_signal)
    running_std = np.zeros_like(filtered_signal)
    
    for i in range(len(filtered_signal)):
        start_idx = max(0, i - long_window)
        window_data = filtered_signal[start_idx:i+1]
        running_mean[i] = np.mean(window_data)
        running_std[i] = np.std(window_data)
    
    # Adaptive threshold = mean + sensitivity * std
    adaptive_threshold = running_mean + sensitivity * running_std
    
    # Find peaks above the adaptive threshold
    min_distance = int(min_time_between_steps * fs)
    peaks, _ = signal.find_peaks(filtered_signal, height=adaptive_threshold, distance=min_distance)
    
    # Convert peak indices to times
    detected_steps = peaks / fs
    
    return detected_steps, filtered_signal, adaptive_threshold

def shoe_algorithm(accel_data, gyro_data, fs, window_size=0.1, threshold=0.8, min_time_between_steps=0.3):
    """
    Step detection using SHOE (Step Heading Offset Estimator) approach.
    This is a simplified version that uses both acceleration and gyroscope data.
    
    Parameters:
    - accel_data: Accelerometer data (3D array [x, y, z])
    - gyro_data: Gyroscope data (3D array [x, y, z])
    - fs: Sampling frequency in Hz
    - window_size: Size of the moving average window in seconds
    - threshold: Threshold parameter for step detection
    - min_time_between_steps: Minimum time between consecutive steps in seconds
    
    Returns:
    - detected_steps: Array of detected step times
    """
    # Calculate the magnitude of acceleration (removing gravity)
    accel_mag = np.sqrt(accel_data[0]**2 + accel_data[1]**2 + (accel_data[2] - 9.81)**2)
    
    # Calculate the magnitude of angular velocity
    gyro_mag = np.sqrt(gyro_data[0]**2 + gyro_data[1]**2 + gyro_data[2]**2)
    
    # Apply moving average filter to both signals
    window_len = int(window_size * fs)
    if window_len % 2 == 0:
        window_len += 1  # Make sure window length is odd
    
    filtered_accel = signal.savgol_filter(accel_mag, window_len, 2)
    filtered_gyro = signal.savgol_filter(gyro_mag, window_len, 2)
    
    # Normalize both signals to 0-1 range
    norm_accel = (filtered_accel - np.min(filtered_accel)) / (np.max(filtered_accel) - np.min(filtered_accel))
    norm_gyro = (filtered_gyro - np.min(filtered_gyro)) / (np.max(filtered_gyro) - np.min(filtered_gyro))
    
    # Combine the signals (simple weighted sum)
    combined_signal = 0.7 * norm_accel + 0.3 * norm_gyro
    
    # Find peaks in the combined signal
    min_distance = int(min_time_between_steps * fs)
    peaks, _ = signal.find_peaks(combined_signal, height=threshold, distance=min_distance)
    
    # Convert peak indices to times
    detected_steps = peaks / fs
    
    return detected_steps, combined_signal

# --------------------------------
# Evaluation Functions
# --------------------------------

def evaluate_algorithm(detected_steps, ground_truth_steps, tolerance=0.2):
    """
    Evaluate the performance of a step detection algorithm.
    
    Parameters:
    - detected_steps: Array of detected step times
    - ground_truth_steps: Array of ground truth step times
    - tolerance: Time tolerance in seconds for matching steps
    
    Returns:
    - metrics: Dictionary of evaluation metrics
    """
    # Count true positives, false positives, and false negatives
    true_positives = 0
    matched_ground_truth = set()
    
    for detected in detected_steps:
        # Check if this detected step matches any ground truth step
        matched = False
        for i, gt_step in enumerate(ground_truth_steps):
            if abs(detected - gt_step) <= tolerance and i not in matched_ground_truth:
                true_positives += 1
                matched_ground_truth.add(i)
                matched = True
                break
    
    false_positives = len(detected_steps) - true_positives
    false_negatives = len(ground_truth_steps) - true_positives
    
    # Calculate metrics
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    f1_score = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    
    # Mean absolute error in step count
    step_count_error = abs(len(detected_steps) - len(ground_truth_steps))
    
    return {
        'true_positives': true_positives,
        'false_positives': false_positives,
        'false_negatives': false_negatives,
        'precision': precision,
        'recall': recall,
        'f1_score': f1_score,
        'step_count': len(detected_steps),
        'ground_truth_count': len(ground_truth_steps),
        'step_count_error': step_count_error,
        'step_count_error_percent': 100 * step_count_error / len(ground_truth_steps) if len(ground_truth_steps) > 0 else float('inf')
    }

def run_all_algorithms(dataset, param_sets=None):
    """
    Run all step detection algorithms on a dataset.
    
    Parameters:
    - dataset: Dictionary containing the dataset
    - param_sets: Dictionary of parameter sets for each algorithm (optional)
    
    Returns:
    - results: Dictionary of results for each algorithm and sensor
    """
    # Default parameters if not provided
    if param_sets is None:
        param_sets = {
            'peak_detection': {'window_size': 0.1, 'threshold': 1.0, 'min_time_between_steps': 0.3},
            'zero_crossing': {'window_size': 0.1, 'min_time_between_steps': 0.3},
            'spectral_analysis': {'window_size': 5.0, 'overlap': 0.5, 'step_freq_range': (1.0, 2.5)},
            'adaptive_threshold': {'window_size': 0.1, 'sensitivity': 0.6, 'min_time_between_steps': 0.3},
            'shoe': {'window_size': 0.1, 'threshold': 0.8, 'min_time_between_steps': 0.3}
        }
    
    results = {'sensor1': {}, 'sensor2': {}}
    fs = dataset['params']['fs']
    ground_truth_steps = dataset['ground_truth']['step_times']
    
    # Process sensor 1
    accel_data1 = [
        dataset['sensor1']['accel_x'],
        dataset['sensor1']['accel_y'],
        dataset['sensor1']['accel_z']
    ]
    gyro_data1 = [
        dataset['sensor1']['gyro_x'],
        dataset['sensor1']['gyro_y'],
        dataset['sensor1']['gyro_z']
    ]
    
    # Process sensor 2
    accel_data2 = [
        dataset['sensor2']['accel_x'],
        dataset['sensor2']['accel_y'],
        dataset['sensor2']['accel_z']
    ]
    gyro_data2 = [
        dataset['sensor2']['gyro_x'],
        dataset['sensor2']['gyro_y'],
        dataset['sensor2']['gyro_z']
    ]
    
    # Run peak detection algorithm
    pd_params = param_sets['peak_detection']
    detected_steps1_pd, filtered_signal1_pd = peak_detection_algorithm(
        accel_data1, fs, pd_params['window_size'], pd_params['threshold'], pd_params['min_time_between_steps']
    )
    detected_steps2_pd, filtered_signal2_pd = peak_detection_algorithm(
        accel_data2, fs, pd_params['window_size'], pd_params['threshold'], pd_params['min_time_between_steps']
    )
    
    results['sensor1']['peak_detection'] = {
        'detected_steps': detected_steps1_pd,
        'filtered_signal': filtered_signal1_pd,
        'metrics': evaluate_algorithm(detected_steps1_pd, ground_truth_steps)
    }
    results['sensor2']['peak_detection'] = {
        'detected_steps': detected_steps2_pd,
        'filtered_signal': filtered_signal2_pd,
        'metrics': evaluate_algorithm(detected_steps2_pd, ground_truth_steps)
    }
    
    # Run zero crossing algorithm
    zc_params = param_sets['zero_crossing']
    detected_steps1_zc, filtered_signal1_zc = zero_crossing_algorithm(
        accel_data1, fs, zc_params['window_size'], zc_params['min_time_between_steps']
    )
    detected_steps2_zc, filtered_signal2_zc = zero_crossing_algorithm(
        accel_data2, fs, zc_params['window_size'], zc_params['min_time_between_steps']
    )
    
    results['sensor1']['zero_crossing'] = {
        'detected_steps': detected_steps1_zc,
        'filtered_signal': filtered_signal1_zc,
        'metrics': evaluate_algorithm(detected_steps1_zc, ground_truth_steps)
    }
    results['sensor2']['zero_crossing'] = {
        'detected_steps': detected_steps2_zc,
        'filtered_signal': filtered_signal2_zc,
        'metrics': evaluate_algorithm(detected_steps2_zc, ground_truth_steps)
    }
    
    # Run spectral analysis algorithm
    sa_params = param_sets['spectral_analysis']
    detected_steps1_sa, step_freqs1_sa = spectral_analysis_algorithm(
        accel_data1, fs, sa_params['window_size'], sa_params['overlap'], sa_params['step_freq_range']
    )
    detected_steps2_sa, step_freqs2_sa = spectral_analysis_algorithm(
        accel_data2, fs, sa_params['window_size'], sa_params['overlap'], sa_params['step_freq_range']
    )
    
    results['sensor1']['spectral_analysis'] = {
        'detected_steps': detected_steps1_sa,
        'step_frequencies': step_freqs1_sa,
        'metrics': evaluate_algorithm(detected_steps1_sa, ground_truth_steps)
    }
    results['sensor2']['spectral_analysis'] = {
        'detected_steps': detected_steps2_sa,
        'step_frequencies': step_freqs2_sa,
        'metrics': evaluate_algorithm(detected_steps2_sa, ground_truth_steps)
    }
    
    # Run adaptive threshold algorithm
    at_params = param_sets['adaptive_threshold']
    detected_steps1_at, filtered_signal1_at, threshold1_at = adaptive_threshold_algorithm(
        accel_data1, fs, at_params['window_size'], at_params['sensitivity'], at_params['min_time_between_steps']
    )
    detected_steps2_at, filtered_signal2_at, threshold2_at = adaptive_threshold_algorithm(
        accel_data2, fs, at_params['window_size'], at_params['sensitivity'], at_params['min_time_between_steps']
    )
    
    results['sensor1']['adaptive_threshold'] = {
        'detected_steps': detected_steps1_at,
        'filtered_signal': filtered_signal1_at,
        'threshold': threshold1_at,
        'metrics': evaluate_algorithm(detected_steps1_at, ground_truth_steps)
    }
    results['sensor2']['adaptive_threshold'] = {
        'detected_steps': detected_steps2_at,
        'filtered_signal': filtered_signal2_at,
        'threshold': threshold2_at,
        'metrics': evaluate_algorithm(detected_steps2_at, ground_truth_steps)
    }
    
    # Run SHOE algorithm
    shoe_params = param_sets['shoe']
    detected_steps1_shoe, combined_signal1_shoe = shoe_algorithm(
        accel_data1, gyro_data1, fs, shoe_params['window_size'], shoe_params['threshold'], shoe_params['min_time_between_steps']
    )
    detected_steps2_shoe, combined_signal2_shoe = shoe_algorithm(
        accel_data2, gyro_data2, fs, shoe_params['window_size'], shoe_params['threshold'], shoe_params['min_time_between_steps']
    )
    
    results['sensor1']['shoe'] = {
        'detected_steps': detected_steps1_shoe,
        'combined_signal': combined_signal1_shoe,
        'metrics': evaluate_algorithm(detected_steps1_shoe, ground_truth_steps)
    }
    results['sensor2']['shoe'] = {
        'detected_steps': detected_steps2_shoe,
        'combined_signal': combined_signal2_shoe,
        'metrics': evaluate_algorithm(detected_steps2_shoe, ground_truth_steps)
    }
    
    return results

# --------------------------------
# Visualization Functions
# --------------------------------

def plot_algorithm_results(dataset, results, algorithm_name, sensor_name, time_range=None):
    """
    Plot the results of a step detection algorithm.
    
    Parameters:
    - dataset: Dictionary containing the dataset
    - results: Dictionary of results from run_all_algorithms
    - algorithm_name: Name of the algorithm to plot
    - sensor_name: Name of the sensor to plot ('sensor1' or 'sensor2')
    - time_range: Tuple of (start_time, end_time) to plot a specific range
    """
    time = dataset['time']
    ground_truth_steps = dataset['ground_truth']['step_times']
    
    # Get algorithm results
    alg_result = results[sensor_name][algorithm_name]
    detected_steps = alg_result['detected_steps']
    metrics = alg_result['metrics']
    
    # Set up the figure
    plt.figure(figsize=(12, 8))
    plt.suptitle(f"{algorithm_name} - {sensor_name} (F1: {metrics['f1_score']:.2f}, Count Error: {metrics['step_count_error']})")
    
    # If time range is specified, filter the data
    if time_range is not None:
        start_idx = np.argmin(np.abs(time - time_range[0]))
        end_idx = np.argmin(np.abs(time - time_range[1]))
        time = time[start_idx:end_idx]
        
        # Filter step times to be within the range
        ground_truth_steps = ground_truth_steps[(ground_truth_steps >= time_range[0]) & (ground_truth_steps <= time_range[1])]
        detected_steps = detected_steps[(detected_steps >= time_range[0]) & (detected_steps <= time_range[1])]
    
    # Plot the accelerometer data
    plt.subplot(3, 1, 1)
    plt.plot(time, dataset[sensor_name]['accel_x'], 'r-', label='X', alpha=0.5)
    plt.plot(time, dataset[sensor_name]['accel_y'], 'g-', label='Y', alpha=0.5)
    plt.plot(time, dataset[sensor_name]['accel_z'], 'b-', label='Z', alpha=0.5)
    plt.axhline(y=9.81, color='k', linestyle='--', alpha=0.3)  # Gravity line
    plt.title('Accelerometer Data')
    plt.xlabel('Time (s)')
    plt.ylabel('Acceleration (m/s²)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Plot the filtered signal or algorithm-specific data
    plt.subplot(3, 1, 2)
    
    if algorithm_name == 'peak_detection':
        plt.plot(time, alg_result['filtered_signal'], 'k-', label='Filtered Signal')
        for step in detected_steps:
            plt.axvline(x=step, color='r', linestyle='-', alpha=0.5)
            
    elif algorithm_name == 'zero_crossing':
        plt.plot(time, alg_result['filtered_signal'], 'k-', label='Filtered Signal')
        plt.axhline(y=0, color='b', linestyle='--', alpha=0.5)  # Zero line
        for step in detected_steps:
            plt.axvline(x=step, color='r', linestyle='-', alpha=0.5)
            
    elif algorithm_name == 'spectral_analysis':
        # For spectral analysis, we can plot the step frequencies over time
        t = np.linspace(0, time[-1], len(alg_result['step_frequencies']))
        plt.plot(t, alg_result['step_frequencies'], 'k-', label='Step Frequency')
        plt.ylabel('Frequency (Hz)')
        
    elif algorithm_name == 'adaptive_threshold':
        plt.plot(time, alg_result['filtered_signal'], 'k-', label='Filtered Signal')
        plt.plot(time, alg_result['threshold'], 'r--', label='Adaptive Threshold')
        for step in detected_steps:
            plt.axvline(x=step, color='r', linestyle='-', alpha=0.5)
            
    elif algorithm_name == 'shoe':
        plt.plot(time, alg_result['combined_signal'], 'k-', label='Combined Signal')
        for step in detected_steps:
            plt.axvline(x=step, color='r', linestyle='-', alpha=0.5)
    
    plt.title(f'Algorithm-Specific Data - {algorithm_name}')
    plt.xlabel('Time (s)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Plot the detected steps vs ground truth
    plt.subplot(3, 1, 3)
    plt.vlines(ground_truth_steps, 0, 0.8, color='g', label='Ground Truth')
    plt.vlines(detected_steps, 0.2, 1.0, color='r', label='Detected Steps')
    plt.title('Step Detection Results')
    plt.xlabel('Time (s)')
    plt.yticks([])
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.subplots_adjust(top=0.92)
    
    return plt.gcf()

def compare_algorithms(dataset, results, sensor_name='sensor1', time_range=None):
    """
    Compare the performance of all algorithms for a given sensor.
    
    Parameters:
    - dataset: Dictionary containing the dataset
    - results: Dictionary of results from run_all_algorithms
    - sensor_name: Name of the sensor to plot ('sensor1' or 'sensor2')
    - time_range: Tuple of (start_time, end_time) to plot a specific range
    """
    time = dataset['time']
    ground_truth_steps = dataset['ground_truth']['step_times']
    
    # Set up the figure
    plt.figure(figsize=(14, 10))
    plt.suptitle(f"Algorithm Comparison - {sensor_name}")
    
    # If time range is specified, filter the data
    if time_range is not None:
        start_idx = np.argmin(np.abs(time - time_range[0]))
        end_idx = np.argmin(np.abs(time - time_range[1]))
        time = time[start_idx:end_idx]
        
        # Filter step times to be within the range
        ground_truth_steps = ground_truth_steps[(ground_truth_steps >= time_range[0]) & (ground_truth_steps <= time_range[1])]
    
    # Plot the accelerometer data
    plt.subplot(6, 1, 1)
    plt.plot(time, dataset[sensor_name]['accel_x'], 'r-', label='X', alpha=0.5)
    plt.plot(time, dataset[sensor_name]['accel_y'], 'g-', label='Y', alpha=0.5)
    plt.plot(time, dataset[sensor_name]['accel_z'], 'b-', label='Z', alpha=0.5)
    plt.title('Accelerometer Data')
    plt.ylabel('Accel. (m/s²)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Plot results for each algorithm
    algorithms = ['peak_detection', 'zero_crossing', 'spectral_analysis', 'adaptive_threshold', 'shoe']
    
    for i, alg_name in enumerate(algorithms):
        plt.subplot(6, 1, i+2)
        
        # Get algorithm results
        alg_result = results[sensor_name][alg_name]
        detected_steps = alg_result['detected_steps']
        metrics = alg_result['metrics']
        
        # Filter steps if time range is specified
        if time_range is not None:
            detected_steps = detected_steps[(detected_steps >= time_range[0]) & (detected_steps <= time_range[1])]
        
        # Plot ground truth and detected steps
        plt.vlines(ground_truth_steps, 0, 0.8, color='g', label='Ground Truth')
        plt.vlines(detected_steps, 0.2, 1.0, color='r', label='Detected')
        
        plt.title(f"{alg_name} (F1: {metrics['f1_score']:.2f}, Count Error: {metrics['step_count_error']})")
        plt.yticks([])
        plt.grid(True, alpha=0.3)
        
        if i == len(algorithms) - 1:
            plt.xlabel('Time (s)')
        
        plt.legend(loc='upper right')
    
    plt.tight_layout()
    plt.subplots_adjust(top=0.92)
    
    return plt.gcf()

def compare_sensors(dataset, results, algorithm_name='adaptive_threshold'):
    """
    Compare the performance of both sensors for a given algorithm.
    
    Parameters:
    - dataset: Dictionary containing the dataset
    - results: Dictionary of results from run_all_algorithms
    - algorithm_name: Name of the algorithm to use for comparison
    """
    time = dataset['time']
    ground_truth_steps = dataset['ground_truth']['step_times']
    
    # Get algorithm results for both sensors
    sensor1_result = results['sensor1'][algorithm_name]
    sensor2_result = results['sensor2'][algorithm_name]
    
    detected_steps1 = sensor1_result['detected_steps']
    detected_steps2 = sensor2_result['detected_steps']
    
    metrics1 = sensor1_result['metrics']
    metrics2 = sensor2_result['metrics']
    
    # Set up the figure
    plt.figure(figsize=(14, 10))
    plt.suptitle(f"Sensor Comparison - {algorithm_name}")
    
    # Plot Sensor 1 data
    plt.subplot(4, 1, 1)
    plt.plot(time, dataset['sensor1']['accel_x'], 'r-', label='X', alpha=0.5)
    plt.plot(time, dataset['sensor1']['accel_y'], 'g-', label='Y', alpha=0.5)
    plt.plot(time, dataset['sensor1']['accel_z'], 'b-', label='Z', alpha=0.5)
    plt.title('Sensor 1 (Waveshare) - Accelerometer Data')
    plt.ylabel('Accel. (m/s²)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Plot Sensor 2 data
    plt.subplot(4, 1, 2)
    plt.plot(time, dataset['sensor2']['accel_x'], 'r-', label='X', alpha=0.5)
    plt.plot(time, dataset['sensor2']['accel_y'], 'g-', label='Y', alpha=0.5)
    plt.plot(time, dataset['sensor2']['accel_z'], 'b-', label='Z', alpha=0.5)
    plt.title('Sensor 2 (Adafruit) - Accelerometer Data')
    plt.ylabel('Accel. (m/s²)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Plot Sensor 1 results
    plt.subplot(4, 1, 3)
    plt.vlines(ground_truth_steps, 0, 0.8, color='g', label='Ground Truth')
    plt.vlines(detected_steps1, 0.2, 1.0, color='r', label='Detected')
    plt.title(f"Sensor 1 Results (F1: {metrics1['f1_score']:.2f}, Count Error: {metrics1['step_count_error']})")
    plt.yticks([])
    plt.grid(True, alpha=0.3)
    plt.legend(loc='upper right')
    
    # Plot Sensor 2 results
    plt.subplot(4, 1, 4)
    plt.vlines(ground_truth_steps, 0, 0.8, color='g', label='Ground Truth')
    plt.vlines(detected_steps2, 0.2, 1.0, color='r', label='Detected')
    plt.title(f"Sensor 2 Results (F1: {metrics2['f1_score']:.2f}, Count Error: {metrics2['step_count_error']})")
    plt.xlabel('Time (s)')
    plt.yticks([])
    plt.grid(True, alpha=0.3)
    plt.legend(loc='upper right')
    
    plt.tight_layout()
    plt.subplots_adjust(top=0.92)
    
    return plt.gcf()

def plot_summary_metrics(all_results):
    """
    Plot summary metrics for all algorithms and scenarios.
    
    Parameters:
    - all_results: Dictionary of results for all scenarios
    """
    # Prepare data structures
    scenarios = list(all_results.keys())
    algorithms = ['peak_detection', 'zero_crossing', 'spectral_analysis', 'adaptive_threshold', 'shoe']
    sensors = ['sensor1', 'sensor2']
    
    metrics = {
        'f1_score': np.zeros((len(scenarios), len(algorithms), len(sensors))),
        'precision': np.zeros((len(scenarios), len(algorithms), len(sensors))),
        'recall': np.zeros((len(scenarios), len(algorithms), len(sensors))),
        'step_count_error_percent': np.zeros((len(scenarios), len(algorithms), len(sensors)))
    }
    
    # Fill in the metrics
    for i, scenario in enumerate(scenarios):
        for j, algorithm in enumerate(algorithms):
            for k, sensor in enumerate(sensors):
                metrics['f1_score'][i, j, k] = all_results[scenario][sensor][algorithm]['metrics']['f1_score']
                metrics['precision'][i, j, k] = all_results[scenario][sensor][algorithm]['metrics']['precision']
                metrics['recall'][i, j, k] = all_results[scenario][sensor][algorithm]['metrics']['recall']
                metrics['step_count_error_percent'][i, j, k] = all_results[scenario][sensor][algorithm]['metrics']['step_count_error_percent']
    
    # Create plots
    fig, axes = plt.subplots(2, 2, figsize=(25, 12))
    fig.suptitle('Algorithm Performance Comparison Across Scenarios')
    
    # Helper function to create bar plots
    def create_grouped_bars(ax, data, title, ylabel):
        x = np.arange(len(scenarios))
        width = 0.1  # Width of each bar
        
        for j, algorithm in enumerate(algorithms):
            # Sensor 1
            ax.bar(x - width*2 + j*width, data[:, j, 0], width, label=f"{algorithm}-S1" if j == 0 else "_nolegend_", 
                   alpha=0.7, color=f"C{j}")
            # Sensor 2
            ax.bar(x + width*3 + j*width, data[:, j, 1], width, label=f"{algorithm}-S2" if j == 0 else "_nolegend_", 
                   alpha=0.7, color=f"C{j}", hatch='/')
        
        ax.set_title(title)
        ax.set_ylabel(ylabel)
        ax.set_xticks(x + width/2)
        ax.set_xticklabels(scenarios)
        ax.set_ylim(0, 1.0 if 'error' not in ylabel.lower() else None)
        ax.grid(True, alpha=0.3, axis='y')
        
        # Custom legend
        legend_elements = []
        for j, algorithm in enumerate(algorithms):
            legend_elements.append(plt.Line2D([0], [0], color=f"C{j}", lw=4, label=algorithm))
        
        legend_elements.append(Patch(facecolor='gray', label='Sensor 1 (Waveshare)'))
        legend_elements.append(Patch(facecolor='gray', label='Sensor 2 (Adafruit)', hatch='/'))

        
        ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1, 1))
    
    # Create the four plots
    create_grouped_bars(axes[0, 0], metrics['f1_score'], 'F1 Score', 'F1 Score (higher is better)')
    create_grouped_bars(axes[0, 1], metrics['precision'], 'Precision', 'Precision (higher is better)')
    create_grouped_bars(axes[1, 0], metrics['recall'], 'Recall', 'Recall (higher is better)')
    create_grouped_bars(axes[1, 1], metrics['step_count_error_percent'], 'Step Count Error', 'Error % (lower is better)')
    
    plt.tight_layout()
    plt.subplots_adjust(top=0.95, right=0.85)
    
    return fig

def plot_algorithm_rankings(all_results):
    """
    Plot rankings of algorithms based on F1 score.
    
    Parameters:
    - all_results: Dictionary of results for all scenarios
    """
    # Prepare data structures
    scenarios = list(all_results.keys())
    algorithms = ['peak_detection', 'zero_crossing', 'spectral_analysis', 'adaptive_threshold', 'shoe']
    sensors = ['sensor1', 'sensor2']
    
    # Average F1 scores across scenarios
    avg_f1_scores = np.zeros((len(algorithms), len(sensors)))
    
    for j, algorithm in enumerate(algorithms):
        for k, sensor in enumerate(sensors):
            scores = []
            for scenario in scenarios:
                scores.append(all_results[scenario][sensor][algorithm]['metrics']['f1_score'])
            avg_f1_scores[j, k] = np.mean(scores)
    
    # Create ranking plot with increased height
    plt.figure(figsize=(10, 7))  # Increase height from 6 to 7
    
    # Sort algorithms by average F1 score
    sorted_indices = np.argsort(np.mean(avg_f1_scores, axis=1))[::-1]
    sorted_algorithms = [algorithms[i] for i in sorted_indices]
    sorted_scores = avg_f1_scores[sorted_indices]
    
    x = np.arange(len(sorted_algorithms))
    width = 0.35
    
    plt.bar(x - width/2, sorted_scores[:, 0], width, label='Sensor 1 (Waveshare)', alpha=0.8)
    plt.bar(x + width/2, sorted_scores[:, 1], width, label='Sensor 2 (Adafruit)', alpha=0.8, hatch='/')
    
    # Add title with increased padding (y=1.05 instead of default)
    plt.title('Algorithm Ranking by Average F1 Score', pad=20, y=1.05)
    
    plt.xlabel('Algorithm')
    plt.ylabel('Average F1 Score')
    plt.xticks(x, sorted_algorithms)
    plt.ylim(0, 1.0)
    plt.grid(True, alpha=0.3, axis='y')
    plt.legend()
    
    # Add score values on top of bars
    # Increase gap from top of bar (0.02 -> 0.04)
    for i, score in enumerate(sorted_scores[:, 0]):
        plt.text(i - width/2, score + 0.04, f"{score:.2f}", ha='center')
    for i, score in enumerate(sorted_scores[:, 1]):
        plt.text(i + width/2, score + 0.04, f"{score:.2f}", ha='center')
    
    # Adjust layout with increased padding on top
    plt.tight_layout(pad=2.0, rect=[0, 0, 1, 0.95])  # rect=[left, bottom, right, top]
    
    return plt.gcf()

# --------------------------------
# Main Function
# --------------------------------

def main():
    """
    Main function to generate data, run algorithms, and create visualizations.
    """
    # Generate sample datasets
    print("Generating datasets...")
    datasets = generate_datasets()
    
    # Save datasets to files
    print("Saving datasets to 'data' directory...")
    save_datasets(datasets)
    
    # Run algorithms on each dataset
    print("Running algorithms on datasets...")
    all_results = {}
    for scenario_name, dataset in datasets.items():
        print(f"Processing {scenario_name}...")
        all_results[scenario_name] = run_all_algorithms(dataset)
    
    # Create organized directory structure for plots
    print("Creating visualizations...")
    base_output_dir = './plots'
    if not os.path.exists(base_output_dir):
        os.makedirs(base_output_dir)
    
    # Create subdirectories
    dirs = {
        'by_scenario': {},
        'by_algorithm': {},
        'by_sensor': {
            'sensor1_waveshare': {},
            'sensor2_adafruit': {}
        },
        'comparisons': {
            'algorithm_comparisons': {},
            'sensor_comparisons': {}
        },
        'summary': {}
    }
    
    # Create directory structure
    for main_dir, subdirs in dirs.items():
        main_path = os.path.join(base_output_dir, main_dir)
        if not os.path.exists(main_path):
            os.makedirs(main_path)
        
        for subdir in subdirs:
            subdir_path = os.path.join(main_path, subdir)
            if not os.path.exists(subdir_path):
                os.makedirs(subdir_path)
    
    # Create scenario directories
    for scenario_name in datasets.keys():
        scenario_dir = os.path.join(base_output_dir, 'by_scenario', scenario_name)
        if not os.path.exists(scenario_dir):
            os.makedirs(scenario_dir)
    
    # Create algorithm directories
    algorithms = ['peak_detection', 'zero_crossing', 'spectral_analysis', 'adaptive_threshold', 'shoe']
    for algorithm in algorithms:
        alg_dir = os.path.join(base_output_dir, 'by_algorithm', algorithm)
        if not os.path.exists(alg_dir):
            os.makedirs(alg_dir)
    
    # Generate visualizations
    for scenario_name in datasets.keys():
        dataset = datasets[scenario_name]
        results = all_results[scenario_name]
        
        # Plot individual algorithm results
        for algorithm in algorithms:
            for sensor_idx, sensor in enumerate(['sensor1', 'sensor2']):
                sensor_name = 'sensor1_waveshare' if sensor_idx == 0 else 'sensor2_adafruit'
                
                fig = plot_algorithm_results(dataset, results, algorithm, sensor)
                
                # Save in multiple relevant directories
                # 1. By scenario
                fig.savefig(os.path.join(base_output_dir, 'by_scenario', scenario_name, 
                                       f"{algorithm}_{sensor}.png"))
                
                # 2. By algorithm
                fig.savefig(os.path.join(base_output_dir, 'by_algorithm', algorithm, 
                                       f"{scenario_name}_{sensor}.png"))
                
                # 3. By sensor
                fig.savefig(os.path.join(base_output_dir, 'by_sensor', sensor_name, 
                                       f"{scenario_name}_{algorithm}.png"))
                
                plt.close(fig)
        
        # Plot algorithm comparisons
        for sensor_idx, sensor in enumerate(['sensor1', 'sensor2']):
            sensor_name = 'sensor1_waveshare' if sensor_idx == 0 else 'sensor2_adafruit'
            
            fig = compare_algorithms(dataset, results, sensor)
            
            # Save in comparisons directory
            fig.savefig(os.path.join(base_output_dir, 'comparisons', 'algorithm_comparisons', 
                                   f"{scenario_name}_{sensor}.png"))
            
            # Also save in scenario directory
            fig.savefig(os.path.join(base_output_dir, 'by_scenario', scenario_name, 
                                   f"algorithm_comparison_{sensor}.png"))
            
            # Also save in sensor directory
            fig.savefig(os.path.join(base_output_dir, 'by_sensor', sensor_name, 
                                   f"{scenario_name}_algorithm_comparison.png"))
            
            plt.close(fig)
        
        # Plot sensor comparisons
        for algorithm in ['peak_detection', 'adaptive_threshold', 'shoe']:
            fig = compare_sensors(dataset, results, algorithm)
            
            # Save in comparisons directory
            fig.savefig(os.path.join(base_output_dir, 'comparisons', 'sensor_comparisons', 
                                   f"{scenario_name}_{algorithm}.png"))
            
            # Also save in scenario directory
            fig.savefig(os.path.join(base_output_dir, 'by_scenario', scenario_name, 
                                   f"sensor_comparison_{algorithm}.png"))
            
            # Also save in algorithm directory
            fig.savefig(os.path.join(base_output_dir, 'by_algorithm', algorithm, 
                                   f"{scenario_name}_sensor_comparison.png"))
            
            plt.close(fig)
    
    # Plot summary metrics
    fig = plot_summary_metrics(all_results)
    fig.savefig(os.path.join(base_output_dir, 'summary', "summary_metrics.png"))
    # Also save at root for backward compatibility
    fig.savefig(os.path.join(base_output_dir, "summary_metrics.png"))
    plt.close(fig)
    
    # Plot algorithm rankings
    fig = plot_algorithm_rankings(all_results)
    fig.savefig(os.path.join(base_output_dir, 'summary', "algorithm_rankings.png"))
    # Also save at root for backward compatibility
    fig.savefig(os.path.join(base_output_dir, "algorithm_rankings.png"))
    plt.close(fig)
    
    print("Done! Visualizations saved to 'plots' directory with organized subdirectories.")

if __name__ == "__main__":
    main()