import numpy as np
import pandas as pd
# from scipy.interpolate import interp1d
import json

def generate_interpolated_test_data():
    """
    Generate interpolated test data with realistic step patterns
    for testing step detection algorithms at proper sampling rate
    """
    
    # Target parameters
    duration = 12.0  # seconds
    target_fs = 20.0  # 20 Hz sampling rate
    step_times_gt = [1.0, 2.2, 3.5, 4.8, 6.1, 7.3, 8.6, 9.8, 11.0]  # 9 steps
    
    # Create time arrays
    time_high_res = np.arange(0, duration, 1/target_fs)
    n_samples = len(time_high_res)
    
    print(f"Generated {n_samples} samples at {target_fs} Hz over {duration}s")
    
    # Generate base accelerometer signals with step patterns
    accel_x = np.random.normal(0.1, 0.05, n_samples)  # Base noise + bias
    accel_y = np.random.normal(-0.2, 0.08, n_samples)
    accel_z = np.random.normal(9.81, 0.1, n_samples)  # Gravity + noise
    
    # Add step patterns (simplified double-bump)
    for step_time in step_times_gt:
        step_idx = int(step_time * target_fs)
        if step_idx < n_samples - 20:  # Ensure we don't go out of bounds
            
            # Create step pattern (0.4s duration)
            pattern_length = int(0.4 * target_fs)  # 8 samples at 20Hz
            pattern_indices = np.arange(pattern_length)
            
            # Double bump pattern: heel strike + toe push-off
            heel_strike = -1.5 * np.exp(-((pattern_indices[:4] - 1) ** 2) / 2)
            toe_pushoff = 2.0 * np.exp(-((pattern_indices[4:] - 6) ** 2) / 4)
            pattern = np.concatenate([heel_strike, toe_pushoff])
            
            # Add to Z-axis (most prominent)
            accel_z[step_idx:step_idx + pattern_length] += pattern
            
            # Add smaller patterns to X and Y
            accel_x[step_idx:step_idx + pattern_length] += pattern * 0.3
            accel_y[step_idx:step_idx + pattern_length] += pattern * 0.2
    
    # Generate gyroscope data
    gyro_x = np.random.normal(0.02, 0.1, n_samples)
    gyro_y = np.random.normal(-0.01, 0.08, n_samples)
    gyro_z = np.random.normal(0.0, 0.05, n_samples)
    
    # Add gyro patterns during steps
    for step_time in step_times_gt:
        step_idx = int(step_time * target_fs)
        if step_idx < n_samples - 10:
            pattern_length = int(0.3 * target_fs)
            gyro_pattern = 0.5 * np.sin(np.linspace(0, 2*np.pi, pattern_length))
            
            gyro_x[step_idx:step_idx + pattern_length] += gyro_pattern * 0.8
            gyro_y[step_idx:step_idx + pattern_length] += gyro_pattern * 0.6
            gyro_z[step_idx:step_idx + pattern_length] += gyro_pattern * 0.3
    
    # Generate magnetometer data (slowly varying)
    mag_x = 25 + 2 * np.sin(2 * np.pi * 0.1 * time_high_res) + np.random.normal(0, 1, n_samples)
    mag_y = 40 + 3 * np.cos(2 * np.pi * 0.15 * time_high_res) + np.random.normal(0, 1, n_samples)
    mag_z = 30 + 1 * np.sin(2 * np.pi * 0.05 * time_high_res) + np.random.normal(0, 1, n_samples)
    
    # Create sensor2 data (slightly different characteristics)
    accel_x2 = accel_x + np.random.normal(0, 0.02, n_samples) + 0.05
    accel_y2 = accel_y + np.random.normal(0, 0.02, n_samples) - 0.03
    accel_z2 = accel_z + np.random.normal(0, 0.02, n_samples) + 0.1
    
    gyro_x2 = gyro_x + np.random.normal(0, 0.01, n_samples) + 0.01
    gyro_y2 = gyro_y + np.random.normal(0, 0.01, n_samples) - 0.02
    gyro_z2 = gyro_z + np.random.normal(0, 0.01, n_samples)
    
    mag_x2 = mag_x + np.random.normal(0, 0.5, n_samples) + 2
    mag_y2 = mag_y + np.random.normal(0, 0.5, n_samples) - 1
    mag_z2 = mag_z + np.random.normal(0, 0.5, n_samples) + 1
    
    # Create battery data (slowly decreasing)
    voltage = 3.7 - 0.1 * (time_high_res / duration) + np.random.normal(0, 0.01, n_samples)
    current = 0.15 + 0.05 * np.random.random(n_samples)
    percentage = 85 - 15 * (time_high_res / duration) + np.random.normal(0, 1, n_samples)
    
    # Create DataFrames
    sensor1_df = pd.DataFrame({
        'time': time_high_res,
        'accel_x': accel_x,
        'accel_y': accel_y,
        'accel_z': accel_z,
        'gyro_x': gyro_x,
        'gyro_y': gyro_y,
        'gyro_z': gyro_z,
        'mag_x': mag_x,
        'mag_y': mag_y,
        'mag_z': mag_z
    })
    
    sensor2_df = pd.DataFrame({
        'time': time_high_res,
        'accel_x': accel_x2,
        'accel_y': accel_y2,
        'accel_z': accel_z2,
        'gyro_x': gyro_x2,
        'gyro_y': gyro_y2,
        'gyro_z': gyro_z2,
        'mag_x': mag_x2,
        'mag_y': mag_y2,
        'mag_z': mag_z2
    })
    
    battery_df = pd.DataFrame({
        'time': time_high_res,
        'voltage': voltage,
        'current': current,
        'percentage': percentage
    })
    
    ground_truth_df = pd.DataFrame({
        'step_times': step_times_gt
    })
    
    # Create metadata
    metadata = {
        "recording_name": "test_interpolated_20hz",
        "recording_date": "2025-07-27 20:00:00",
        "total_duration": duration,
        "step_count": len(step_times_gt),
        "sampling_frequency": target_fs
    }
    
    return sensor1_df, sensor2_df, battery_df, ground_truth_df, metadata

def save_test_data():
    """Save test data to CSV files"""
    sensor1_df, sensor2_df, battery_df, ground_truth_df, metadata = generate_interpolated_test_data()
    
    # Save to CSV files
    sensor1_df.to_csv('sensor1_waveshare.csv', index=False)
    sensor2_df.to_csv('sensor2_adafruit.csv', index=False)
    battery_df.to_csv('battery.csv', index=False)
    ground_truth_df.to_csv('ground_truth.csv', index=False)
    
    # Save metadata
    with open('metadata.json', 'w') as f:
        json.dump(metadata, f, indent=4) # type: ignore
    
    print("Test data saved!")
    print(f"Samples: {len(sensor1_df)}")
    print(f"Duration: {metadata['total_duration']}s")
    print(f"Sampling rate: {metadata['sampling_frequency']} Hz")
    print(f"Steps: {metadata['step_count']}")
    print(f"Step times: {ground_truth_df['step_times'].tolist()}")

if __name__ == "__main__":
    save_test_data()