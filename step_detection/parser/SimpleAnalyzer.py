import pandas as pd
import numpy as np
import json
from pathlib import Path
from typing import Any
from datetime import datetime
from tqdm import tqdm
import sys

from utils import process_sensor_algorithms, load_params


class SimpleAnalyzer:
    """
    Simple analyzer for GUI-compatible sensor data files.
    Recursively processes directories and updates detection_results.yaml files.
    """

    def __init__(self, detection_params_file: str = "detection_params.json") -> None:
        """
        Initialize Simple Analyzer.

        Args:
            detection_params_file (str): Path to detection parameters file
        """
        try:
            self.detection_params = load_params(detection_params_file)

        except FileNotFoundError:
            # Try alternative path in parser directory
            parser_params_path = Path("parser") / detection_params_file
            self.detection_params = load_params(str(parser_params_path))

        self.tolerance = self.detection_params["tolerance"]
        self.param_sets_sensor_1 = self.detection_params["param_sets_sensor_1"]
        self.param_sets_sensor_2 = self.detection_params["param_sets_sensor_2"]

        # Convert step_freq_range from list to tuple for spectral_analysis
        for sensor_params in [self.param_sets_sensor_1, self.param_sets_sensor_2]:
            if "spectral_analysis" in sensor_params:
                sensor_params["spectral_analysis"]["step_freq_range"] = tuple(
                    sensor_params["spectral_analysis"]["step_freq_range"]
                )

    def _find_sensor_directories(self, root_path: Path) -> list[Path]:
        """
        Find all directories containing GUI-compatible sensor files.

        Args:
            root_path (Path): Root directory to search

        Returns:
            list[Path]: List of directories containing sensor data
        """
        sensor_dirs = []
        required_files = [
            "sensor1_waveshare.csv",
            "sensor2_adafruit.csv",
            "ground_truth.csv",
        ]

        for path in root_path.rglob("*"):
            if path.is_dir():
                # Check if all required files exist
                if all((path / file).exists() for file in required_files):
                    sensor_dirs.append(path)

        return sorted(sensor_dirs)

    def _load_sensor_data(
        self, data_dir: Path
    ) -> tuple[pd.DataFrame, pd.DataFrame, np.ndarray, float] | None:
        """
        Load sensor data from GUI-compatible files.

        Args:
            data_dir (Path): Directory containing sensor files

        Returns:
            tuple: (sensor1_df, sensor2_df, ground_truth_steps, sampling_frequency) or None if error
        """
        try:
            sensor1_df = pd.read_csv(data_dir / "sensor1_waveshare.csv")
            sensor2_df = pd.read_csv(data_dir / "sensor2_adafruit.csv")
            ground_truth_df = pd.read_csv(data_dir / "ground_truth.csv")

            # Load metadata for sampling frequency
            metadata_file = data_dir / "metadata.json"
            if metadata_file.exists():
                with open(metadata_file, "r") as f:
                    metadata = json.load(f)
                sampling_frequency = metadata.get("sampling_frequency", 100.0)

            else:
                # Estimate from time data
                if len(sensor1_df) > 1:
                    sampling_frequency = len(sensor1_df) / sensor1_df["time"].iloc[-1]
                else:
                    sampling_frequency = 100.0

            # Convert ground truth to numpy array
            ground_truth_steps = ground_truth_df["step_times"].values

            return sensor1_df, sensor2_df, ground_truth_steps, sampling_frequency  # type: ignore

        except Exception as e:
            tqdm.write(f"Error loading data from {data_dir}: {e}")
            return None

    def _run_analysis(
        self,
        sensor1_df: pd.DataFrame,
        sensor2_df: pd.DataFrame,
        ground_truth_steps: np.ndarray,
        sampling_frequency: float,
    ) -> dict[str, Any]:
        """
        Run step detection analysis on sensor data.

        Args:
            sensor1_df (pd.DataFrame): First sensor data
            sensor2_df (pd.DataFrame): Second sensor data
            ground_truth_steps (np.ndarray): Ground truth step times
            sampling_frequency (float): Sampling frequency in Hz

        Returns:
            dict[str, Any]: Analysis results for both sensors
        """
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

        results = {
            "sensor1": process_sensor_algorithms(
                accel_data1,  # type: ignore
                gyro_data1,  # type: ignore
                self.param_sets_sensor_1,
                ground_truth_steps,
                sampling_frequency,
                self.tolerance,
            ),
            "sensor2": process_sensor_algorithms(
                accel_data2,  # type: ignore
                gyro_data2,  # type: ignore
                self.param_sets_sensor_2,
                ground_truth_steps,
                sampling_frequency,
                self.tolerance,
            ),
        }

        return results

    def _save_results(
        self,
        results: dict[str, Any],
        output_file: Path,
        recording_name: str,
    ) -> None:
        """
        Save analysis results to YAML file in GUI format.

        Args:
            results (dict[str, Any]): Analysis results
            output_file (Path): Output YAML file path
            recording_name (str): Recording name for header
        """
        with open(output_file, "w") as f:
            f.write("# Step Detection Results\n")
            f.write(f"# {recording_name}\n\n\n")

            for sensor, algorithms in results.items():
                f.write("##############################################\n")
                f.write(f"# {sensor.upper()}\n")
                f.write("##############################################\n")
                f.write(f"{sensor.upper()}:\n")

                for alg, res in algorithms.items():
                    f.write(f"\n  {alg.replace('_', ' ').title()}:\n")
                    f.write(f"    Execution Time: {res['execution_time']:.4f} s\n")
                    f.write(f"    Detected Steps: {len(res['detected_steps'])}\n")
                    f.write("    Metrics:\n")
                    f.write(
                        json.dumps(res["metrics"], indent=6) # type: ignore
                        .replace("{", "    {")
                        .replace("}", "    }\n\n")
                    )

    def analyze_directory(
        self,
        root_directory: str | Path,
        force_reanalyze: bool = True
    ) -> None:
        """
        Analyze all sensor data directories recursively.

        Args:
            root_directory (str | Path): Root directory to search for sensor data
            force_reanalyze (bool): If True, reanalyze even if detection_results.yaml exists
        """
        root_path = Path(root_directory).resolve()

        if not root_path.exists():
            print(f"Error: Directory {root_path} does not exist")
            return

        sensor_dirs = self._find_sensor_directories(root_path)

        if not sensor_dirs:
            print(f"No sensor data directories found in {root_path}")
            return

        # print(f"Found {len(sensor_dirs)} sensor data directories")

        # Filter directories that need analysis (always force reanalyze, I don't care)
        dirs_to_analyze = []
        for sensor_dir in sensor_dirs:
            results_file = sensor_dir / "detection_results.yaml"
            if force_reanalyze or not results_file.exists():
                dirs_to_analyze.append(sensor_dir)

        if not dirs_to_analyze:
            print(
                "All directories already have analysis results. Use force_reanalyze=True to reprocess."
            )
            return

        # print(f"Analyzing {len(dirs_to_analyze)} directories...")

        successful = 0
        failed = 0

        for sensor_dir in tqdm(
            dirs_to_analyze,
            desc="Analyzing directories...",
            unit="dir",
            colour="green",
            file=sys.stdout,
        ):

            data_result = self._load_sensor_data(sensor_dir)
            if data_result is None:
                failed += 1
                continue

            sensor1_df, sensor2_df, ground_truth_steps, sampling_frequency = data_result

            try:
                results = self._run_analysis(
                    sensor1_df, sensor2_df, ground_truth_steps, sampling_frequency
                )

                results_file = sensor_dir / "detection_results.yaml"
                recording_name = sensor_dir.name
                self._save_results(results, results_file, recording_name)

                successful += 1

            except Exception as e:
                tqdm.write(f"Analysis failed for {sensor_dir}: {e}")
                failed += 1

        # print(f"\nAnalysis complete!")
        # print(f"Successful: {successful}")
        # print(f"Failed: {failed}")
        # print(f"Total processed: {successful + failed}")

    def get_analysis_summary(self, root_directory: str | Path) -> dict[str, Any]:
        """
        Get summary of analysis results across all directories.

        Args:
            root_directory (str | Path): Root directory to analyze

        Returns:
            dict[str, Any]: Summary statistics
        """
        root_path = Path(root_directory).resolve()
        sensor_dirs = self._find_sensor_directories(root_path)

        summary = {
            "total_directories": len(sensor_dirs),
            "analyzed_directories": 0,
            "unanalyzed_directories": 0,
            "directories_with_analysis": [],
            "directories_without_analysis": [],
        }

        for sensor_dir in sensor_dirs:
            results_file = sensor_dir / "detection_results.yaml"
            if results_file.exists():
                summary["analyzed_directories"] += 1
                summary["directories_with_analysis"].append(
                    str(sensor_dir.relative_to(root_path))
                )
            else:
                summary["unanalyzed_directories"] += 1
                summary["directories_without_analysis"].append(
                    str(sensor_dir.relative_to(root_path))
                )

        return summary


def main() -> None:
    """
    Main function for command line usage.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Simple Step Detection Analyzer")
    parser.add_argument("directory", help="Root directory to analyze")
    parser.add_argument(
        "--force", "-f", action="store_true", help="Force reanalysis of all directories"
    )
    parser.add_argument(
        "--summary", "-s", action="store_true", help="Show analysis summary only"
    )
    parser.add_argument(
        "--params",
        "-p",
        default="detection_params.json",
        help="Detection parameters file (default: detection_params.json)",
    )

    args = parser.parse_args()

    try:
        analyzer = SimpleAnalyzer(args.params)

        if args.summary:
            summary = analyzer.get_analysis_summary(args.directory)
            print(f"Analysis Summary for {args.directory}:")
            print(f"Total directories: {summary['total_directories']}")
            print(f"Analyzed: {summary['analyzed_directories']}")
            print(f"Unanalyzed: {summary['unanalyzed_directories']}")

            if summary["directories_without_analysis"]:
                print("\nDirectories without analysis:")
                for dir_path in summary["directories_without_analysis"][
                    :10
                ]:  # Show first 10
                    print(f"  - {dir_path}")
                if len(summary["directories_without_analysis"]) > 10:
                    print(
                        f"  ... and {len(summary['directories_without_analysis']) - 10} more"
                    )
        else:
            analyzer.analyze_directory(args.directory, force_reanalyze=args.force)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
