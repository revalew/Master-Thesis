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

    The Savitzky-Golay filter is a digital smoothing filter that fits successive
    sub-sets of adjacent data points with a low-degree polynomial by the method
    of linear least squares. It preserves features of the signal (like peaks)
    better than simple moving averages while reducing noise.

    How it works:
        - Takes a sliding window of data points
        - Fits a polynomial (degree = polyorder) to points in each window
        - Uses the polynomial's center value as the filtered output
        - Moves window by one sample and repeats
        
    Key advantages over moving average:
        - Better preservation of signal features (peaks, slopes)
        - Reduces noise while maintaining signal characteristics
        - Polynomial fitting provides better local approximation

    Args:
        data: Input signal data (1D array)
        window_size_seconds: Window size in seconds (converted to samples)
        fs: Sampling frequency in Hz
        polyorder: Polynomial degree (2=quadratic, 3=cubic). Higher orders preserve
                 peaks better but may amplify noise. Range: 1 to window_length-1

    Returns:
        filtered_signal: Smoothed signal data preserving original length
    """
    # Convert window_size from seconds to samples
    window_len = max(3, int(window_size_seconds * fs))
    # window_len = max(5, int(window_size_seconds * fs))

    # Ensure window_len is odd (required by Savitzky-Golay)
    if window_len % 2 == 0:
        window_len += 1

    # Ensure window_len doesn't exceed data length
    if window_len > len(data):
        window_len = len(data)
        if window_len % 2 == 0:
            window_len -= 1
        # For very short data, use minimum odd window
        if window_len < 3:
            window_len = 3 if len(data) >= 3 else len(data)

    # Ensure polyorder is valid: must be less than window_len and at least 1
    polyorder = max(1, min(polyorder, window_len - 1))

    try:
        # Apply Savitzky-Golay filter
        filtered_signal = signal.savgol_filter(data, window_len, polyorder)
        return filtered_signal

    except (ValueError, np.linalg.LinAlgError) as e:
        print(f"Savgol filter error: {e}, using moving average fallback")

        # Fallback to simple moving average
        kernel_size = min(window_len, len(data))
        if kernel_size > len(data):
            return data.copy()

        # Ensure odd kernel size for consistency
        if kernel_size % 2 == 0:
            kernel_size -= 1
        if kernel_size < 1:
            kernel_size = 1

        kernel = np.ones(kernel_size) / kernel_size
        return np.convolve(data, kernel, mode="same")


##############################################
# Step Detection Algorithms
##############################################
def peak_detection_algorithm(
    accel_data, fs, window_size=0.1, threshold=1.0, min_time_between_steps=0.3
):
    """
    Step detection using peak detection with adaptive threshold

    Args:
        accel_data: Accelerometer data (3D array [x, y, z])
        fs: Sampling frequency in Hz
        window_size: Size of the moving average window in seconds
        threshold: Threshold for peak detection
        min_time_between_steps: Minimum time between consecutive steps in seconds

    Returns:
        tuple: Array of detected step times + Filtered acceleration magnitude signal
    """
    accel_mag = np.sqrt(accel_data[0] ** 2 + accel_data[1] ** 2 + accel_data[2] ** 2)

    filtered_signal = safe_savgol_filter(accel_mag, window_size, fs, polyorder=3)
    gravity_baseline = np.median(filtered_signal)
    centered_signal = filtered_signal - gravity_baseline

    window_samples = max(int(2.0 * fs), 20)

    try:
        running_std = (
            pd.Series(centered_signal).rolling(window_samples, min_periods=1).std()
        )

        if len(running_std) != len(centered_signal):
            print(
                f"Length mismatch: signal={len(centered_signal)}, std={len(running_std)}"
            )
            # Fallback to simple std
            adaptive_threshold = np.std(centered_signal) * threshold

        else:
            adaptive_threshold = running_std.values * threshold

    except Exception as e:
        print(f"Rolling std error: {e}, using fallback")
        adaptive_threshold = np.std(centered_signal) * threshold

    min_distance = max(1, int(min_time_between_steps * fs))

    try:
        peaks, _ = signal.find_peaks(
            centered_signal,
            height=adaptive_threshold,
            distance=min_distance,
            prominence=0.2,
        )
        detected_steps = peaks / fs

    except Exception as e:
        print(f"Peak detection error: {e}")
        detected_steps = np.array([])

    return detected_steps, filtered_signal


def zero_crossing_algorithm(
    accel_data, fs, window_size=0.1, min_time_between_steps=0.3, hysteresis_band=0.3
):
    """
    Step detection using zero-crossing method with hysteresis

    Args:
        accel_data: Accelerometer data (3D array [x, y, z])
        fs: Sampling frequency in Hz
        window_size: Size of the moving average window in seconds
        min_time_between_steps: Minimum time between consecutive steps in seconds
        hysteresis_band: Hysteresis band in Hz. Default is 0.3

    Returns:
        tuple: Array of detected step times + Filtered acceleration signal
    """
    accel_mag = np.sqrt(accel_data[0] ** 2 + accel_data[1] ** 2 + accel_data[2] ** 2)
    filtered_signal = safe_savgol_filter(accel_mag, window_size, fs, polyorder=3)

    gravity_reference = np.median(filtered_signal)
    signal_centered = filtered_signal - gravity_reference

    min_samples = max(1, int(min_time_between_steps * fs))
    inhibit_samples = max(5, int(0.1 * fs))

    crossings = []
    last_crossing = -min_samples
    above_threshold = False
    inhibit_counter = 0

    for i, value in enumerate(signal_centered):
        if inhibit_counter > 0:
            inhibit_counter -= 1
            continue

        if not above_threshold and value > hysteresis_band:
            above_threshold = True

        elif above_threshold and value < -hysteresis_band:
            above_threshold = False

            if (i - last_crossing) >= min_samples:
                crossings.append(i)
                last_crossing = i
                inhibit_counter = inhibit_samples

    detected_steps = np.array(crossings) / fs

    return detected_steps, filtered_signal


def spectral_analysis_algorithm(
    accel_data, fs, window_size=5.0, overlap=0.5, step_freq_range=(1.0, 2.5)
):
    """
    Step detection using STFT spectral analysis

    Args:
        accel_data: Accelerometer data (3D array [x, y, z])
        fs: Sampling frequency in Hz
        window_size: Size of FFT window in seconds
        overlap: Overlap between consecutive windows (0-1)
        step_freq_range: Range of expected step frequencies in Hz

    Returns:
        tuple: Array of detected step times + Array of step frequencies
    """
    accel_mag = np.sqrt(accel_data[0] ** 2 + accel_data[1] ** 2 + accel_data[2] ** 2)

    if len(accel_mag) < 3.0 * fs:
        return np.array([]), np.array([])

    # Parameters for the STFT
    nperseg = min(int(window_size * fs), len(accel_mag) // 2)
    noverlap = int(nperseg * overlap)

    if nperseg < 32:
        nperseg = 32
    if noverlap >= nperseg:
        noverlap = nperseg // 2

    try:
        f, t, Zxx = signal.stft(
            accel_mag, fs=fs, nperseg=nperseg, noverlap=noverlap, window="hann"
        )

        freq_mask = (f >= step_freq_range[0]) & (f <= step_freq_range[1])
        if not np.any(freq_mask):
            return np.array([]), np.array([])

        gait_spectrum = np.abs(Zxx[freq_mask, :])
        gait_freqs = f[freq_mask]

        dominant_freq_indices = np.argmax(gait_spectrum, axis=0)
        step_freqs = gait_freqs[dominant_freq_indices]

        median_step_frequency = np.median(step_freqs)
        signal_duration = len(accel_mag) / fs

        # The x2 multiplier assumes stride frequency = step frequency / 2
        # But this may not be true for 22Hz sampling or pocket mounting
        # total_steps = int(median_step_frequency * signal_duration * 2)
        # total_steps = int(median_step_frequency * signal_duration * 1.2)
        total_steps = int(median_step_frequency * signal_duration)

        if total_steps > 0:
            step_interval = signal_duration / total_steps
            detected_steps = np.arange(
                step_interval / 2, signal_duration, step_interval
            )

        else:
            detected_steps = np.array([])

        return detected_steps, step_freqs

    except Exception as e:
        print(f"Spectral analysis error: {e}")
        return np.array([]), np.array([])


def adaptive_threshold_algorithm(
    accel_data, fs, window_size=0.1, sensitivity=0.6, min_time_between_steps=0.3
):
    """
    Step detection using adaptive threshold with local minima detection

    Args:
        accel_data: Accelerometer data (3D array [x, y, z])
        fs: Sampling frequency in Hz
        window_size: Size of the moving average window in seconds
        sensitivity: Sensitivity parameter (0-1) controlling the adaptive threshold
        min_time_between_steps: Minimum time between consecutive steps in seconds

    Returns:
        tuple: Array of detected step times + Filtered acceleration magnitude signal + Array of adaptive threshold values
    """
    accel_mag = np.sqrt(accel_data[0] ** 2 + accel_data[1] ** 2 + accel_data[2] ** 2)
    filtered_signal = safe_savgol_filter(accel_mag, window_size, fs, polyorder=3)

    min_distance = max(1, int(min_time_between_steps * fs))

    try:
        all_peaks, _ = signal.find_peaks(filtered_signal, distance=min_distance)

        if len(all_peaks) == 0:
            return np.array([]), filtered_signal, np.zeros_like(filtered_signal)

        step_amplitudes = []
        window_samples = max(int(1.0 * fs), 20)

        for peak_idx in all_peaks:
            start_idx = max(0, peak_idx - window_samples // 2)
            end_idx = min(len(filtered_signal), peak_idx + window_samples // 2)
            local_baseline = np.min(filtered_signal[start_idx:end_idx])

            amplitude = filtered_signal[peak_idx] - local_baseline
            step_amplitudes.append(amplitude)

        if len(step_amplitudes) <= 10:
            threshold_value = (
                np.mean(step_amplitudes) * sensitivity if step_amplitudes else 1.0
            )

        else:
            recent_amplitudes = step_amplitudes[-window_samples // 2 :]
            threshold_value = np.mean(recent_amplitudes) * sensitivity

        adaptive_threshold = np.full_like(filtered_signal, threshold_value)

        valid_peaks = []
        for i, peak_idx in enumerate(all_peaks):
            if step_amplitudes[i] > threshold_value:
                valid_peaks.append(peak_idx)

        detected_steps = np.array(valid_peaks) / fs

        return detected_steps, filtered_signal, adaptive_threshold

    except Exception as e:
        print(f"Adaptive threshold error: {e}")
        return np.array([]), filtered_signal, np.zeros_like(filtered_signal)


def shoe_algorithm(
    accel_data,
    gyro_data,
    fs,
    window_size=0.1,
    threshold=0.5,
    min_time_between_steps=0.3,
):
    """
    Step detection using SHOE (Step Heading Offset Estimator) approach.
    This is a Multi-sensor algorithm that uses both acceleration and gyroscope data. The algorithm is using stance phase detection

    Args:
        accel_data: Accelerometer data (3D array [x, y, z])
        gyro_data: Gyroscope data (3D array [x, y, z])
        fs: Sampling frequency in Hz
        window_size: Size of the moving average window in seconds
        threshold: Threshold parameter for step detection
        min_time_between_steps: Minimum time between consecutive steps in seconds

    Returns:
        tuple: Array of detected step times + Combined and normalized signal
    """
    accel_mag = np.sqrt(accel_data[0] ** 2 + accel_data[1] ** 2 + accel_data[2] ** 2)
    gyro_mag = np.sqrt(gyro_data[0] ** 2 + gyro_data[1] ** 2 + gyro_data[2] ** 2)

    filtered_accel = safe_savgol_filter(accel_mag, window_size, fs, polyorder=3)
    filtered_gyro = safe_savgol_filter(gyro_mag, window_size, fs, polyorder=3)

    # Normalize both signals
    if np.max(filtered_accel) > np.min(filtered_accel):
        norm_accel = (filtered_accel - np.min(filtered_accel)) / (
            np.max(filtered_accel) - np.min(filtered_accel)
        )

    else:
        norm_accel = np.ones_like(filtered_accel) * 0.5

    if np.max(filtered_gyro) > np.min(filtered_gyro):
        norm_gyro = (filtered_gyro - np.min(filtered_gyro)) / (
            np.max(filtered_gyro) - np.min(filtered_gyro)
        )

    else:
        norm_gyro = np.ones_like(filtered_gyro) * 0.5

    combined_signal = 0.7 * norm_accel + 0.3 * norm_gyro

    window_samples = max(int(0.2 * fs), 5)
    stance_phases = []

    if len(combined_signal) < window_samples:
        # print(f"SHOE: Signal too short, using peak detection fallback")
        # Fallback to peak detection
        min_distance = max(1, int(min_time_between_steps * fs))
        try:
            peaks, _ = signal.find_peaks(
                combined_signal, height=0.5, distance=min_distance, prominence=0.1
            )
            detected_steps = peaks / fs

        except Exception as e:
            print(f"SHOE fallback error: {e}")
            detected_steps = np.array([])

        return detected_steps, combined_signal

    # Try stance phase detection first
    try:
        for i in range(
            0, len(combined_signal) - window_samples, max(1, window_samples // 2)
        ):
            accel_var = np.var(filtered_accel[i : i + window_samples])
            gyro_mean = np.mean(np.abs(filtered_gyro[i : i + window_samples]))

            if accel_var < (threshold * 0.5) and gyro_mean < (threshold * 0.3):
                stance_phases.append(i + window_samples // 2)

        min_distance = max(1, int(min_time_between_steps * fs))
        if len(stance_phases) > 0:
            filtered_stances = []
            last_stance = -min_distance

            for stance in stance_phases:
                if stance - last_stance >= min_distance:
                    filtered_stances.append(stance)
                    last_stance = stance

            detected_steps = np.array(filtered_stances) / fs
            # print(f"SHOE: Used stance phase detection, found {len(detected_steps)} steps")

        else:
            # print(f"SHOE: No stance phases found, using peak detection fallback")
            try:
                peaks, _ = signal.find_peaks(
                    combined_signal,
                    height=0.5,  # Fixed threshold for fallback
                    distance=min_distance,
                    prominence=0.1,
                )
                detected_steps = peaks / fs
                # print(f"SHOE: Peak detection fallback found {len(detected_steps)} steps")

            except Exception as e:
                print(f"SHOE fallback error: {e}")
                detected_steps = np.array([])

    except Exception as e:
        print(f"SHOE stance detection error: {e}, using fallback")
        # Emergency fallback
        min_distance = max(1, int(min_time_between_steps * fs))
        try:
            peaks, _ = signal.find_peaks(
                combined_signal, height=0.5, distance=min_distance, prominence=0.1
            )
            detected_steps = peaks / fs

        except Exception as e:
            print(f"SHOE emergency fallback error: {e}")
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
    
    Args:
        detected_steps: Array of detected step times
        ground_truth_steps: Array of ground truth step times
        tolerance: Time tolerance in seconds for matching steps

    Returns:
        float: Mean Squared Error between detected and ground truth steps
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

    Args:
        detected_steps: Array of detected step times
        ground_truth_steps: Array of ground truth step times
        tolerance: Time tolerance in seconds for matching steps

    Returns:
        dict: Dictionary of evaluation metrics
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
