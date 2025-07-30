import numpy as np
import pandas as pd
from scipy import signal
from scipy.fft import fft, fftfreq
import os
from datetime import datetime
import json


##############################################
# Savitzky-Golay Filter
##############################################
def safe_savgol_filter(data, window_size_seconds, fs, polyorder=2):
    """
    Safely apply Savitzky-Golay filter with proper parameter validation.
    This prevents the "polyorder must be less than window_length" error.

    Parameters:
    - data: Input signal data
    - window_size_seconds: Window size in seconds
    - fs: Sampling frequency in Hz
    - polyorder: Polynomial order for the filter

    Returns:
    - filtered_signal: Filtered signal data
    """
    # Convert window_size from seconds to samples
    window_len = max(5, int(window_size_seconds * fs))

    # Ensure window_len is odd and at least 3
    if window_len % 2 == 0:
        window_len += 1

    # Ensure window_len is not larger than data length
    if window_len >= len(data):
        window_len = max(3, len(data) // 2)
        if window_len % 2 == 0:
            window_len -= 1

    # Ensure polyorder is less than window_len and at least 1
    polyorder = max(1, min(polyorder, window_len - 1))

    try:
        filtered_signal = signal.savgol_filter(data, window_len, polyorder)
        return filtered_signal
    except ValueError as e:
        print(f"Savgol filter error: {e}, using moving average fallback")
        # Fallback to simple moving average
        kernel_size = min(5, len(data))
        if kernel_size > 0:
            kernel = np.ones(kernel_size) / kernel_size
            return np.convolve(data, kernel, mode="same")
        else:
            return data.copy()


##############################################
# Step Detection Algorithms
##############################################
def peak_detection_algorithm(
    accel_data, fs, window_size=0.1, threshold=1.0, min_time_between_steps=0.3
):
    """
    Step detection using peak detection with fixed threshold

    Parameters:
    - accel_data: Accelerometer data (3D array [x, y, z])
    - fs: Sampling frequency in Hz
    - window_size: Size of the moving average window in seconds
    - threshold: Threshold for peak detection
    - min_time_between_steps: Minimum time between consecutive steps in seconds

    Returns:
    - detected_steps: Array of detected step times
    - filtered_signal: Filtered acceleration magnitude signal
    """
    # Calculate the magnitude of acceleration (removing gravity)
    accel_mag = np.sqrt(
        accel_data[0] ** 2 + accel_data[1] ** 2 + (accel_data[2] - 9.81) ** 2
    )

    # Apply safe moving average filter
    filtered_signal = safe_savgol_filter(accel_mag, window_size, fs, polyorder=2)

    # Find peaks
    min_distance = max(1, int(min_time_between_steps * fs))
    try:
        peaks, _ = signal.find_peaks(
            filtered_signal, height=threshold, distance=min_distance
        )
        # Convert peak indices to times
        detected_steps = peaks / fs
    except Exception as e:
        print(f"Peak detection error: {e}")
        detected_steps = np.array([])

    return detected_steps, filtered_signal


def zero_crossing_algorithm(
    accel_data, fs, window_size=0.1, min_time_between_steps=0.3
):
    """
    Step detection using zero-crossing method

    Parameters:
    - accel_data: Accelerometer data (3D array [x, y, z])
    - fs: Sampling frequency in Hz
    - window_size: Size of the moving average window in seconds
    - min_time_between_steps: Minimum time between consecutive steps in seconds

    Returns:
    - detected_steps: Array of detected step times
    - filtered_signal: Filtered acceleration signal
    """
    # Use acceleration magnitude instead of just Z-axis
    accel_mag = np.sqrt(accel_data[0] ** 2 + accel_data[1] ** 2 + accel_data[2] ** 2)

    # Remove mean to center around zero
    accel_centered = accel_mag - np.mean(accel_mag)

    # Apply safe moving average filter
    filtered_signal = safe_savgol_filter(accel_centered, window_size, fs, polyorder=2)

    # Find ALL zero crossings (both positive and negative slope)
    sign_changes = np.diff(np.signbit(filtered_signal))
    zero_crossings = np.where(sign_changes)[0]

    # print(f"Zero crossings found: {len(zero_crossings)} total crossings")

    if len(zero_crossings) == 0:
        return np.array([]), filtered_signal

    # Keep only positive slope zero crossings (signal going from negative to positive)
    pos_slope_crossings = []
    for crossing in zero_crossings:
        if crossing + 1 < len(filtered_signal):
            if filtered_signal[crossing] <= 0 and filtered_signal[crossing + 1] > 0:
                pos_slope_crossings.append(crossing)

    # print(f"Positive slope crossings: {len(pos_slope_crossings)}")

    # Apply minimum time between steps
    min_samples = max(1, int(min_time_between_steps * fs))

    # Filter out crossings that are too close
    filtered_crossings = []
    if len(pos_slope_crossings) > 0:
        filtered_crossings = [pos_slope_crossings[0]]
        for crossing in pos_slope_crossings[1:]:
            if crossing - filtered_crossings[-1] >= min_samples:
                filtered_crossings.append(crossing)

    # print(f"Final filtered crossings: {len(filtered_crossings)}")

    # Convert to numpy array and to times
    detected_steps = np.array(filtered_crossings) / fs

    return detected_steps, filtered_signal


def spectral_analysis_algorithm(
    accel_data, fs, window_size=5.0, overlap=0.5, step_freq_range=(1.0, 2.5)
):
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
    - step_freqs: Array of step frequencies
    """
    # Calculate the magnitude of acceleration (removing gravity)
    accel_mag = np.sqrt(
        accel_data[0] ** 2 + accel_data[1] ** 2 + (accel_data[2] - 9.81) ** 2
    )

    # Parameters for the STFT
    nperseg = int(window_size * fs)
    noverlap = int(nperseg * overlap)

    # Ensure valid parameters
    if nperseg >= len(accel_mag):
        nperseg = len(accel_mag) // 2
    if noverlap >= nperseg:
        noverlap = nperseg // 2

    try:
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
            dom_freq_idx = freq_min_idx + np.argmax(
                power_spectrum[freq_min_idx : freq_max_idx + 1]
            )
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
            detected_steps = np.arange(step_interval / 2, time_duration, step_interval)
        else:
            detected_steps = np.array([])

        return detected_steps, np.array(step_freqs)

    except Exception as e:
        print(f"Spectral analysis error: {e}")
        return np.array([]), np.array([])


def adaptive_threshold_algorithm(
    accel_data, fs, window_size=0.1, sensitivity=0.6, min_time_between_steps=0.3
):
    """
    Step detection using adaptive thresholding

    Parameters:
    - accel_data: Accelerometer data (3D array [x, y, z])
    - fs: Sampling frequency in Hz
    - window_size: Size of the moving average window in seconds
    - sensitivity: Sensitivity parameter (0-1) controlling the adaptive threshold
    - min_time_between_steps: Minimum time between consecutive steps in seconds

    Returns:
    - detected_steps: Array of detected step times
    - filtered_signal: Filtered acceleration magnitude signal
    - adaptive_threshold: Array of adaptive threshold values
    """
    # Calculate the magnitude of acceleration (removing gravity)
    accel_mag = np.sqrt(
        accel_data[0] ** 2 + accel_data[1] ** 2 + (accel_data[2] - 9.81) ** 2
    )

    # Apply safe moving average filter
    filtered_signal = safe_savgol_filter(accel_mag, window_size, fs, polyorder=2)

    # Calculate the adaptive threshold using a longer window
    long_window = max(int(2.0 * fs), 10)  # 2-second window, minimum 10 samples

    # Compute the running mean and standard deviation
    running_mean = np.zeros_like(filtered_signal)
    running_std = np.zeros_like(filtered_signal)

    for i in range(len(filtered_signal)):
        start_idx = max(0, i - long_window)
        window_data = filtered_signal[start_idx : i + 1]
        if len(window_data) > 0:
            running_mean[i] = np.mean(window_data)
            running_std[i] = np.std(window_data)
        else:
            running_mean[i] = np.mean(filtered_signal)
            running_std[i] = np.std(filtered_signal)

    # Adaptive threshold = mean + sensitivity * std
    adaptive_threshold = running_mean + sensitivity * running_std

    # Find peaks above the adaptive threshold
    min_distance = max(1, int(min_time_between_steps * fs))
    try:
        peaks, _ = signal.find_peaks(
            filtered_signal, height=adaptive_threshold, distance=min_distance
        )
        # Convert peak indices to times
        detected_steps = peaks / fs
    except Exception as e:
        print(f"Adaptive threshold error: {e}")
        detected_steps = np.array([])

    return detected_steps, filtered_signal, adaptive_threshold


def shoe_algorithm(
    accel_data,
    gyro_data,
    fs,
    window_size=0.1,
    threshold=0.5,
    min_time_between_steps=0.3,
):
    """
    Step detection using SHOE (Step Heading Offset Estimator) approach - IMPROVED VERSION.
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
    - combined_signal: Combined and normalized signal
    """
    # Calculate the magnitude of acceleration (removing gravity)
    accel_mag = np.sqrt(
        accel_data[0] ** 2 + accel_data[1] ** 2 + (accel_data[2] - 9.81) ** 2
    )

    # Calculate the magnitude of angular velocity
    gyro_mag = np.sqrt(gyro_data[0] ** 2 + gyro_data[1] ** 2 + gyro_data[2] ** 2)

    # Apply safe moving average filter to both signals
    filtered_accel = safe_savgol_filter(accel_mag, window_size, fs, polyorder=2)
    filtered_gyro = safe_savgol_filter(gyro_mag, window_size, fs, polyorder=2)

    # Normalize both signals to 0-1 range
    if np.max(filtered_accel) > np.min(filtered_accel):
        norm_accel = (filtered_accel - np.min(filtered_accel)) / (
            np.max(filtered_accel) - np.min(filtered_accel)
        )
    else:
        norm_accel = np.ones_like(filtered_accel) * 0.5  # Flat signal gets 0.5

    if np.max(filtered_gyro) > np.min(filtered_gyro):
        norm_gyro = (filtered_gyro - np.min(filtered_gyro)) / (
            np.max(filtered_gyro) - np.min(filtered_gyro)
        )
    else:
        norm_gyro = np.ones_like(filtered_gyro) * 0.5  # Flat signal gets 0.5

    # Combine the signals (simple weighted sum)
    combined_signal = 0.7 * norm_accel + 0.3 * norm_gyro

    # adaptive_threshold = threshold # * 0.5  # Use 0.4 instead of 0.8
    adaptive_threshold = threshold if threshold < 0.4 else 0.4

    # print(f"SHOE: Combined signal range: {np.min(combined_signal):.3f} to {np.max(combined_signal):.3f}")
    # print(f"SHOE: Using threshold: {adaptive_threshold:.3f}")
    # print(f"SHOE: Values above threshold: {np.sum(combined_signal > adaptive_threshold)}")

    # Find peaks in the combined signal
    min_distance = max(1, int(min_time_between_steps * fs))
    try:
        peaks, properties = signal.find_peaks(
            combined_signal, height=adaptive_threshold, distance=min_distance
        )

        # print(f"SHOE: Found {len(peaks)} peaks")

        # Convert peak indices to times
        detected_steps = peaks / fs
    except Exception as e:
        print(f"SHOE algorithm error: {e}")
        detected_steps = np.array([])

    return detected_steps, combined_signal


##############################################
# Evaluation
##############################################
def calculate_mse(detected_steps, ground_truth_steps, tolerance=0.3):
    """
    Calculate Mean Squared Error between detected and ground truth steps.
    For each ground truth step, finds the closest detected step and applies
    penalty for steps outside tolerance range.
    """
    if len(ground_truth_steps) == 0:
        return 0.0

    if len(detected_steps) == 0:
        return tolerance**2

    squared_errors = []
    for gt_step in ground_truth_steps:
        min_error = min(abs(gt_step - detected) for detected in detected_steps)
        squared_errors.append(min_error**2 if min_error <= tolerance else tolerance**2)

    return np.mean(squared_errors)


def evaluate_algorithm(detected_steps, ground_truth_steps, tolerance=0.3):
    """
    Evaluate the performance of a step detection algorithm.

    Parameters:
    - detected_steps: Array of detected step times
    - ground_truth_steps: Array of ground truth step times
    - tolerance: Time tolerance in seconds for matching steps

    Returns:
    - metrics: Dictionary of evaluation metrics
    """
    # Handle edge cases
    if len(ground_truth_steps) == 0:
        return {
            "true_positives": 0,
            "false_positives": len(detected_steps),
            "false_negatives": 0,
            "precision": 0.0,
            "recall": 0.0,
            "f1_score": 0.0,
            "step_count": len(detected_steps),
            "ground_truth_count": 0,
            "step_count_error": len(detected_steps),
            "step_count_error_percent": 100.0 if len(detected_steps) > 0 else 0.0,
            "mse": float("inf"),
            "count_mse": float("inf"),
        }

    if len(detected_steps) == 0:
        return {
            "true_positives": 0,
            "false_positives": 0,
            "false_negatives": len(ground_truth_steps),
            "precision": 0.0,
            "recall": 0.0,
            "f1_score": 0.0,
            "step_count": 0,
            "ground_truth_count": len(ground_truth_steps),
            "step_count_error": len(ground_truth_steps),
            "step_count_error_percent": 100.0,
            "mse": float("inf"),
            "count_mse": float("inf"),
        }

    # Count true positives, false positives, and false negatives
    true_positives = 0
    matched_ground_truth = set()

    for detected in detected_steps:
        # Check if this detected step matches any ground truth step
        for i, gt_step in enumerate(ground_truth_steps):
            if abs(detected - gt_step) <= tolerance and i not in matched_ground_truth:
                true_positives += 1
                matched_ground_truth.add(i)
                break

    false_positives = len(detected_steps) - true_positives
    false_negatives = len(ground_truth_steps) - true_positives

    # Calculate metrics
    precision = (
        true_positives / (true_positives + false_positives)
        if (true_positives + false_positives) > 0
        else 0
    )
    recall = (
        true_positives / (true_positives + false_negatives)
        if (true_positives + false_negatives) > 0
        else 0
    )
    f1_score = (
        2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    )

    # Mean absolute error in step count
    step_count_error = abs(len(detected_steps) - len(ground_truth_steps))
    step_count_error_percent = (
        100 * step_count_error / len(ground_truth_steps)
        if len(ground_truth_steps) > 0
        else 0
    )

    # MSE with penalty
    mse = calculate_mse(detected_steps, ground_truth_steps, tolerance)

    # Simple count MAE
    count_mse = (len(detected_steps) - len(ground_truth_steps)) ** 2
    # count_mae = abs(len(detected_steps) - len(ground_truth_steps))
    # count_rmse = abs(len(detected_steps) - len(ground_truth_steps))
    # count_mse_norm = ((len(detected_steps) - len(ground_truth_steps)) ** 2) / ((len(ground_truth_steps) ** 2) if len(ground_truth_steps) > 0 else 1)

    return {
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "precision": precision,
        "recall": recall,
        "f1_score": f1_score,
        "step_count": len(detected_steps),
        "ground_truth_count": len(ground_truth_steps),
        "step_count_error": step_count_error,
        "step_count_error_percent": step_count_error_percent,
        "mse": mse,
        "count_mse": count_mse,
    }
