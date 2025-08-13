import pandas as pd
import numpy as np
import json
# import os
from pathlib import Path
from typing import Any
# import time
from datetime import datetime
# import shutil
from tqdm import tqdm # progress bar
from sys import stdout

from utils import process_sensor_algorithms


class TUGDataParser:
    """
    Parser for TUG (Timed Up and Go) test CSV files.
    Converts sensor data files and runs step detection analysis with location-specific parameters.
    """


    def __init__(self, config_path: str = "tug_parser_config.json") -> None:
        """
        Initialize TUG data parser with configuration.

        Args:
            config_path (str): Path to configuration JSON file
        """
        self.duration = 0
        self.config = self._load_config(config_path)
        self.input_dir = Path(self.config["input_directory"]).absolute()
        self.output_dir = Path(self.config["output_directory"]).absolute()
        self.sampling_rate = self.config["sampling_rate_hz"]
        self.gui_compatibility = self.config["gui_compatibility"]

        # Load sensor location parameters
        self.location_params = self._load_location_params(
            self.config["sensor_location_params_file"]
        )
        self.tolerance = self.location_params["tolerance"]

        # Sensor location to parameter mapping
        self.location_param_map = {
            "left_ankle": "ankle_params",
            "right_ankle": "ankle_params",
            "left_wrist": "wrist_params",
            "right_wrist": "wrist_params",
            "sacrum_back": "back_params",
        }

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)


    def _load_config(self, config_filename: str) -> dict[str, Any]:
        """
        Load configuration from JSON file. This file will be searched in the same directory as the main script (or at least this will be the starting point).

        Args:
            config_filename (str): Path to configuration file

        Returns:
            dict[str, Any]: Configuration dictionary
        """
        script_dir = Path(__file__).parent
        config_path = script_dir / config_filename
        # print(f"{config_path = }")
        with open(config_path, "r") as f:
            return json.load(f)


    def _load_location_params(self, params_filename: str) -> dict[str, Any]:
        """
        Load sensor location parameters from JSON file. This file will be searched in the same directory as the main script (or at least this will be the starting point).

        Args:
            params_filename (str): Path to sensor location parameters file

        Returns:
            dict[str, Any]: Location parameters dictionary
        """
        script_dir = Path(__file__).parent
        params_path = script_dir / params_filename
        with open(params_path, "r") as f:
            return json.load(f)


    def _parse_filename(self, filename: str) -> tuple[str, str] | None:
        """
        Parse filename to extract recording ID and sensor location.

        Args:
            filename (str): Filename to parse (e.g., "001-left_ankle.csv")

        Returns:
            tuple[str, str] | None: (recording_id, sensor_location) or None if invalid
        """
        if not filename.endswith(".csv"):
            return None

        name_parts = filename.replace(".csv", "").split("-")
        if len(name_parts) != 2:
            return None

        recording_id = name_parts[0]
        sensor_location = name_parts[1]

        # Validate sensor location
        valid_locations = [
            "left_ankle",
            "right_ankle",
            "left_wrist",
            "right_wrist",
            "sacrum_back",
        ]
        if sensor_location not in valid_locations:
            return None

        return recording_id, sensor_location


    def _load_sensor_data(self, file_path: Path) -> pd.DataFrame | None:
        """
        Load sensor data from CSV file and convert to standard format.

        Args:
            file_path (Path): Path to CSV file

        Returns:
            pd.DataFrame | None: Converted sensor data or None if error
        """
        try:
            # Read CSV file
            df = pd.read_csv(file_path)

            # Check required columns
            required_cols = [
                "PacketCounter",
                "Acc_X",
                "Acc_Y",
                "Acc_Z",
                "Gyr_X",
                "Gyr_Y",
                "Gyr_Z",
            ]
            if not all(col in df.columns for col in required_cols):
                print(f"Warning: Missing required columns in {file_path}")
                return None

            # Generate timestamp based on packet counter and sampling rate
            df["time"] = df["PacketCounter"] / self.sampling_rate

            # Convert to standard format (accel in m/s², gyro in rad/s)
            converted_df = pd.DataFrame(
                {
                    "time": df["time"],
                    "accel_x": df["Acc_X"],
                    "accel_y": df["Acc_Y"],
                    "accel_z": df["Acc_Z"],
                    "gyro_x": df["Gyr_X"],
                    "gyro_y": df["Gyr_Y"],
                    "gyro_z": df["Gyr_Z"],
                    "mag_x": np.zeros(len(df)),  # No magnetometer data available
                    "mag_y": np.zeros(len(df)),
                    "mag_z": np.zeros(len(df)),
                }
            )

            return converted_df

        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return None


    def _get_params_for_location(self, sensor_location: str) -> dict[str, Any]:
        """
        Get detection parameters for specific sensor location.

        Args:
            sensor_location (str): Sensor location (left_ankle, right_wrist, etc.)

        Returns:
            dict[str, Any]: Detection parameters for the location
        """
        param_key = self.location_param_map.get(sensor_location, "back_params")
        return self.location_params[param_key]


    def _analyze_single_sensor(
        self, sensor_df: pd.DataFrame, sensor_location: str, output_file: Path
    ) -> None:
        """
        Run step detection analysis on single sensor.

        Args:
            sensor_df (pd.DataFrame): Sensor data
            sensor_location (str): Sensor location
            output_file (Path): Output file for results
        """
        if len(sensor_df) == 0:
            print(f"Skipping analysis for {sensor_location} - no valid sensor data")
            return

        try:
            # Convert to numpy arrays for algorithms
            accel_data = [
                sensor_df["accel_x"].values,
                sensor_df["accel_y"].values,
                sensor_df["accel_z"].values,
            ]
            gyro_data = [
                sensor_df["gyro_x"].values,
                sensor_df["gyro_y"].values,
                sensor_df["gyro_z"].values,
            ]

            # Empty ground truth for TUG data
            ground_truth_steps = np.array([])

            # Get parameters for this sensor location
            location_params = self._get_params_for_location(sensor_location)

            # Convert step_freq_range from list to tuple for spectral_analysis
            if "spectral_analysis" in location_params:
                location_params["spectral_analysis"]["step_freq_range"] = tuple(
                    location_params["spectral_analysis"]["step_freq_range"]
                )

            # Run analysis (use same params for both sensor1 and sensor2 since it's single sensor)
            results = process_sensor_algorithms(
                accel_data, # type: ignore
                gyro_data, # type: ignore
                location_params,
                ground_truth_steps,
                self.sampling_rate,
                self.tolerance,
            )

            # Save results to YAML file
            with open(output_file, "w") as f:
                f.write("# Step Detection Results\n")
                f.write(f"# Sensor Location: {sensor_location}\n")
                f.write("# Note: No ground truth available for TUG data\n\n")

                for alg, res in results.items():
                    f.write(f"{alg.replace('_', ' ').title()}:\n")
                    f.write(f"  Execution Time: {res['execution_time']:.4f} s\n")
                    f.write(f"  Detected Steps: {len(res['detected_steps'])}\n") # type: ignore
                    f.write(f"  Step Times: {res['detected_steps'].tolist()}\n") # type: ignore

                    # Write simplified metrics (no ground truth comparison)
                    f.write(f"  Step Count: {len(res['detected_steps'])}\n") # type: ignore
                    if len(res["detected_steps"]) > 0: # type: ignore
                        f.write(f"  First Step: {res['detected_steps'][0]:.3f} s\n") # type: ignore
                        f.write(f"  Last Step: {res['detected_steps'][-1]:.3f} s\n") # type: ignore
                        if len(res["detected_steps"]) > 1: # type: ignore
                            step_intervals = np.diff(res["detected_steps"]) # type: ignore
                            f.write(
                                f"  Mean Step Interval: {np.mean(step_intervals):.3f} s\n"
                            )
                            f.write(
                                f"  Step Rate: {len(res['detected_steps']) / sensor_df['time'].iloc[-1]:.2f} steps/s\n" # type: ignore
                            )
                    f.write("\n")

            # print(f"Analysis completed for {sensor_location}")

        except Exception as e:
            print(f"Error analyzing {sensor_location}: {e}")


    def _create_sensor_pair(
        self, sensor1_df: pd.DataFrame | None, sensor2_df: pd.DataFrame | None
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Create sensor pair, filling missing sensor with zeros if needed.
        (Used only in GUI compatibility mode)

        Args:
            sensor1_df (pd.DataFrame | None): First sensor data
            sensor2_df (pd.DataFrame | None): Second sensor data

        Returns:
            tuple[pd.DataFrame, pd.DataFrame]: Pair of sensor dataframes
        """
        # Determine reference dataframe for time axis
        ref_df = sensor1_df if sensor1_df is not None else sensor2_df

        if ref_df is None:
            # Both sensors missing - create dummy data
            time_axis = np.arange(
                0, 10, 1 / self.sampling_rate
            )  # 10 seconds of dummy data
            dummy_df = pd.DataFrame(
                {
                    "time": time_axis,
                    "accel_x": np.zeros(len(time_axis)),
                    "accel_y": np.zeros(len(time_axis)),
                    "accel_z": np.zeros(len(time_axis)),
                    "gyro_x": np.zeros(len(time_axis)),
                    "gyro_y": np.zeros(len(time_axis)),
                    "gyro_z": np.zeros(len(time_axis)),
                    "mag_x": np.zeros(len(time_axis)),
                    "mag_y": np.zeros(len(time_axis)),
                    "mag_z": np.zeros(len(time_axis)),
                }
            )
            return dummy_df.copy(), dummy_df.copy()

        # Create missing sensor with same time axis
        if sensor1_df is None:
            sensor1_df = pd.DataFrame(
                {
                    "time": ref_df["time"],
                    "accel_x": np.zeros(len(ref_df)),
                    "accel_y": np.zeros(len(ref_df)),
                    "accel_z": np.zeros(len(ref_df)),
                    "gyro_x": np.zeros(len(ref_df)),
                    "gyro_y": np.zeros(len(ref_df)),
                    "gyro_z": np.zeros(len(ref_df)),
                    "mag_x": np.zeros(len(ref_df)),
                    "mag_y": np.zeros(len(ref_df)),
                    "mag_z": np.zeros(len(ref_df)),
                }
            )

        if sensor2_df is None:
            sensor2_df = pd.DataFrame(
                {
                    "time": ref_df["time"],
                    "accel_x": np.zeros(len(ref_df)),
                    "accel_y": np.zeros(len(ref_df)),
                    "accel_z": np.zeros(len(ref_df)),
                    "gyro_x": np.zeros(len(ref_df)),
                    "gyro_y": np.zeros(len(ref_df)),
                    "gyro_z": np.zeros(len(ref_df)),
                    "mag_x": np.zeros(len(ref_df)),
                    "mag_y": np.zeros(len(ref_df)),
                    "mag_z": np.zeros(len(ref_df)),
                }
            )

        return sensor1_df, sensor2_df


    def _save_gui_compatible_data(
        self,
        recording_dir: Path,
        pair_name: str,
        sensor1_df: pd.DataFrame,
        sensor2_df: pd.DataFrame,
        recording_id: str,
    ) -> None:
        """
        Save sensor pair data in GUI-compatible format.

        Args:
            recording_dir (Path): Directory to save data
            pair_name (str): Name of sensor pair (ankle, wrist, sacrum)
            sensor1_df (pd.DataFrame): First sensor data
            sensor2_df (pd.DataFrame): Second sensor data
            recording_id (str): Recording identifier
        """
        pair_dir = recording_dir / f"{pair_name}_{recording_id}"
        pair_dir.mkdir(parents=True, exist_ok=True)

        # Save sensor data
        sensor1_df.to_csv(pair_dir / "sensor1_waveshare.csv", index=False)
        sensor2_df.to_csv(pair_dir / "sensor2_adafruit.csv", index=False)

        # Create empty ground truth (no manual step marking available)
        ground_truth_df = pd.DataFrame({"step_times": []})
        ground_truth_df.to_csv(pair_dir / "ground_truth.csv", index=False)

        # Create metadata
        duration = sensor1_df["time"].iloc[-1] if len(sensor1_df) > 0 else 0
        metadata = {
            "recording_name": f"{pair_name}_{recording_id}",
            "recording_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_duration": duration,
            "step_count": 0,  # No ground truth available
            "sampling_frequency": self.sampling_rate,
            "target_frequency": self.sampling_rate,
            "samples_collected": len(sensor1_df),
            "pair_type": pair_name,
            "original_recording_id": recording_id,
            "parsed_from_tug_format": True,
            "gui_compatible": True,
        }

        with open(pair_dir / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=4) # type: ignore


    def _analyze_gui_sensor_pair(
        self,
        pair_dir: Path,
        sensor1_df: pd.DataFrame,
        sensor2_df: pd.DataFrame,
        pair_name: str,
    ) -> None:
        """
        Run step detection analysis on sensor pair for GUI compatibility mode.

        Args:
            pair_dir (Path): Directory containing sensor data
            sensor1_df (pd.DataFrame): First sensor data
            sensor2_df (pd.DataFrame): Second sensor data
            pair_name (str): Pair name (ankle, wrist, sacrum)
        """
        if len(sensor1_df) == 0 or len(sensor2_df) == 0:
            print(f"Skipping analysis for {pair_dir} - no valid sensor data")
            return

        try:
            # Convert to numpy arrays for algorithms
            accel_data1 = [
                sensor1_df["accel_x"].values,
                sensor1_df["accel_y"].values,
                sensor1_df["accel_z"].values,
            ]
            gyro_data1 = [
                sensor1_df["gyro_x"].values,
                sensor1_df["gyro_y"].values,
                sensor1_df["gyro_z"].values,
            ]

            accel_data2 = [
                sensor2_df["accel_x"].values,
                sensor2_df["accel_y"].values,
                sensor2_df["accel_z"].values,
            ]
            gyro_data2 = [
                sensor2_df["gyro_x"].values,
                sensor2_df["gyro_y"].values,
                sensor2_df["gyro_z"].values,
            ]

            # Empty ground truth for TUG data
            ground_truth_steps = np.array([])

            # Get parameters based on pair type
            param_key = f"{pair_name}_params"
            if param_key == "sacrum_params":
                param_key = "back_params"  # sacrum uses back params

            location_params = self.location_params[param_key]

            # Convert step_freq_range from list to tuple for spectral_analysis
            if "spectral_analysis" in location_params:
                location_params["spectral_analysis"]["step_freq_range"] = tuple(
                    location_params["spectral_analysis"]["step_freq_range"]
                )

            # Run analysis
            results = {
                "sensor1": process_sensor_algorithms(
                    accel_data1, # type: ignore
                    gyro_data1, # type: ignore
                    location_params,
                    ground_truth_steps,
                    self.sampling_rate,
                    self.tolerance,
                ),
                "sensor2": process_sensor_algorithms(
                    accel_data2, # type: ignore
                    gyro_data2, # type: ignore
                    location_params,
                    ground_truth_steps,
                    self.sampling_rate,
                    self.tolerance,
                ),
            }

            # Save results to YAML file
            results_file = pair_dir / "detection_results.yaml"
            recording_name = pair_dir.name

            with open(results_file, "w") as f:
                f.write("# Step Detection Results\n")
                f.write(f"# {recording_name}\n")
                f.write("# Note: No ground truth available for TUG data\n\n\n")

                for sensor, algorithms in results.items():
                    f.write("##############################################\n")
                    f.write(f"# {sensor.upper()}\n")
                    f.write("##############################################\n")
                    f.write(f"{sensor.upper()}:\n")

                    for alg, res in algorithms.items():
                        f.write(f"\n  {alg.replace('_', ' ').title()}:\n")
                        f.write(f"    Execution Time: {res['execution_time']:.4f} s\n")
                        f.write(f"    Detected Steps: {len(res['detected_steps'])}\n") # type: ignore
                        f.write(f"    Step Times: {res['detected_steps'].tolist()}\n") # type: ignore

                        # Write simplified metrics (no ground truth comparison)
                        f.write(f"    Step Count: {len(res['detected_steps'])}\n") # type: ignore
                        if len(res["detected_steps"]) > 0: # type: ignore
                            f.write(
                                f"    First Step: {res['detected_steps'][0]:.3f} s\n" # type: ignore
                            )
                            f.write(
                                f"    Last Step: {res['detected_steps'][-1]:.3f} s\n" # type: ignore
                            )
                            if len(res["detected_steps"]) > 1: # type: ignore
                                step_intervals = np.diff(res["detected_steps"]) # type: ignore
                                f.write(
                                    f"    Mean Step Interval: {np.mean(step_intervals):.3f} s\n"
                                )
                                f.write(
                                    f"    Step Rate: {len(res['detected_steps']) / sensor1_df['time'].iloc[-1]:.2f} steps/s\n" # type: ignore
                                )
                        f.write("\n")

            # print(f"Analysis completed for {recording_name}")

        except Exception as e:
            print(f"Error analyzing {pair_dir}: {e}")


    def process_all_recordings(self) -> None:
        """
        Process all TUG recordings in input directory.
        Structure depends on gui_compatibility setting.
        """
        start_time = datetime.now()
        # print(f"Processing TUG recordings from: {self.input_dir}")
        # print(f"Output directory: {self.output_dir}")
        # print(f"GUI compatibility mode: {self.gui_compatibility}")

        # Group files by recording ID
        recordings: dict[str, dict[str, Path]] = {}

        for file_path in self.input_dir.glob("*.csv"):
            parse_result = self._parse_filename(file_path.name)
            if parse_result is None:
                print(f"Skipping invalid filename: {file_path.name}")
                continue

            recording_id, sensor_location = parse_result

            if recording_id not in recordings:
                recordings[recording_id] = {}

            recordings[recording_id][sensor_location] = file_path

        # print(f"Found {len(recordings)} recordings to process")

        # Process each recording
        for recording_id, sensor_files in tqdm(recordings.items(), desc="Processing images...", dynamic_ncols=True, bar_format="{l_bar}{bar}{r_bar}", colour="green", file=stdout, position=0):
            # print(f"\nProcessing recording {recording_id}...")

            # Create recording directory
            recording_dir = self.output_dir / recording_id
            recording_dir.mkdir(parents=True, exist_ok=True)

            if self.gui_compatibility:
                self._process_gui_compatible(recording_dir, recording_id, sensor_files)
            else:
                self._process_simple_format(recording_dir, recording_id, sensor_files)
                
        self.duration = (datetime.now() - start_time).total_seconds() # type: ignore

        # print(f"\nProcessing complete! Results saved to: {self.output_dir}")


    def _process_gui_compatible(
        self, recording_dir: Path, recording_id: str, sensor_files: dict[str, Path]
    ) -> None:
        """
        Process recording in GUI-compatible format with sensor pairs.

        Args:
            recording_dir (Path): Recording directory
            recording_id (str): Recording ID
            sensor_files (dict[str, Path]): Dictionary of sensor files
        """
        # Load sensor data
        sensor_data = {}
        for location, file_path in sensor_files.items():
            sensor_data[location] = self._load_sensor_data(file_path)
            # if sensor_data[location] is not None:
            #     print(f"  Loaded {location}: {len(sensor_data[location])} samples")
            # else:
            if sensor_data[location] is None:
                print(f"  Failed to load {location}")

        # Create sensor pairs and analyze
        pairs = [
            ("ankle", "left_ankle", "right_ankle"),
            ("wrist", "left_wrist", "right_wrist"),
            ("sacrum", "sacrum_back", "sacrum_back"),  # Use same sensor for both
        ]

        for pair_name, sensor1_key, sensor2_key in pairs:
            sensor1_df = sensor_data.get(sensor1_key)
            sensor2_df = (
                sensor_data.get(sensor2_key)
                if sensor2_key != sensor1_key
                else sensor1_df
            )

            # Create sensor pair (fill missing with zeros)
            sensor1_df, sensor2_df = self._create_sensor_pair(sensor1_df, sensor2_df)

            # Save data
            self._save_gui_compatible_data(
                recording_dir, pair_name, sensor1_df, sensor2_df, recording_id
            )

            # Run analysis if enabled
            if self.config["run_analysis"]:
                pair_dir = recording_dir / f"{pair_name}_{recording_id}"
                self._analyze_gui_sensor_pair(
                    pair_dir, sensor1_df, sensor2_df, pair_name
                )


    def _process_simple_format(
        self, recording_dir: Path, recording_id: str, sensor_files: dict[str, Path]
    ) -> None:
        """
        Process recording in simple format with individual sensor files.

        Args:
            recording_dir (Path): Recording directory
            recording_id (str): Recording ID
            sensor_files (dict[str, Path]): Dictionary of sensor files
        """
        processed_sensors = []

        for sensor_location, file_path in sensor_files.items():
            # Load sensor data
            sensor_df = self._load_sensor_data(file_path)
            if sensor_df is None:
                print(f"  Failed to load {sensor_location}")
                continue

            # print(f"  Loaded {sensor_location}: {len(sensor_df)} samples")

            # Save sensor data with original name
            output_csv = recording_dir / f"{sensor_location}.csv"
            sensor_df.to_csv(output_csv, index=False)

            # Run analysis if enabled
            if self.config["run_analysis"]:
                analysis_file = (
                    recording_dir / f"{sensor_location}_detection_results.yaml"
                )
                self._analyze_single_sensor(sensor_df, sensor_location, analysis_file)

            processed_sensors.append(
                {
                    "location": sensor_location,
                    "duration": sensor_df["time"].iloc[-1] if len(sensor_df) > 0 else 0,
                    "samples": len(sensor_df),
                }
            )

        # Create recording metadata
        metadata = {
            "recording_id": recording_id,
            "recording_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sampling_frequency": self.sampling_rate,
            "gui_compatible": False,
            "parsed_from_tug_format": True,
            "sensors": processed_sensors,
        }

        with open(recording_dir / "recording_metadata.json", "w") as f:
            json.dump(metadata, f, indent=4) # type: ignore


    def create_summary_report(self) -> None:
        """
        Create summary report of all processed recordings.
        """
        summary_file = self.output_dir / "processing_summary.json"

        summary = {
            "processing_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "duration_seconds": self.duration,
            "gui_compatibility_mode": self.gui_compatibility,
            "total_recordings": 0,
            "successful_analysis": 0,
            "failed_analysis": 0,
            "recordings": {},
        }

        for recording_dir in self.output_dir.iterdir():
            if not recording_dir.is_dir() or recording_dir.name.startswith("."):
                continue

            recording_id = recording_dir.name
            summary["total_recordings"] += 1
            summary["recordings"][recording_id] = {}

            if self.gui_compatibility:
                # Count pair analysis
                for pair_dir in recording_dir.iterdir():
                    if not pair_dir.is_dir():
                        continue

                    pair_name = pair_dir.name
                    results_file = pair_dir / "detection_results.yaml"

                    if results_file.exists():
                        summary["successful_analysis"] += 1
                        summary["recordings"][recording_id][pair_name] = "analyzed"
                    else:
                        summary["failed_analysis"] += 1
                        summary["recordings"][recording_id][pair_name] = "failed"
            else:
                # Count individual sensor analysis
                for file_path in recording_dir.glob("*_detection_results.yaml"):
                    sensor_name = file_path.name.replace("_detection_results.yaml", "")
                    summary["successful_analysis"] += 1
                    summary["recordings"][recording_id][sensor_name] = "analyzed"

        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=4) # type: ignore

        # print(f"Summary report saved to: {summary_file}")


def validate_environment() -> bool:
    """
    Validate that all required files are present.
    
    Returns:
        bool: True if environment is valid
    """
    required_files = [
        "./utils/step_detection_algorithms.py", 
        "./parser/tug_parser_config.json",
        "./parser/sensor_location_params.json"
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print("Missing required files:")
        for file in missing_files:
            print(f"  - {file}")
        return False
        
    return True


def main() -> None:
    """
    Main function to run TUG data parser.
    """
    try:
        # print("Validating environment...")
        if not validate_environment():
            print("Environment validation failed. Please check missing files.")
            return
        # print("Environment validation successful")
        
        # print("Initializing TUG data parser...")
        parser = TUGDataParser("tug_parser_config.json")
        print(f"\nParser initialized")
        print(f"   - Input:  {parser.input_dir}")
        print(f"   - Output: {parser.output_dir}")
        print(f"   - Sampling rate: {parser.sampling_rate} Hz")
        print(f"   - GUI compatibility: {parser.gui_compatibility}")
        
        if not parser.input_dir.exists():
            print(f"\n     Input directory does not exist: {parser.input_dir}")
            print("   Please create the directory and place your TUG CSV files there.")
            return
        
        csv_files = list(parser.input_dir.glob("*.csv"))
        if not csv_files:
            print(f"\n     No CSV files found in: {parser.input_dir}")
            print("   Please place your TUG CSV files in the input directory.")
            return
        print(f"\nFound {len(csv_files)} CSV files")
        
        print("\nProcessing recordings...")
        parser.process_all_recordings()
        
        print("\nCreating summary report...")
        parser.create_summary_report()
        
        print(f"\nResults saved to: {parser.output_dir}")

    except Exception as e:
        print(f"Error in main: {e}")
        raise


if __name__ == "__main__":
    main()
