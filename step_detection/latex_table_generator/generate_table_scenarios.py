#!/usr/bin/env python3
"""
Generate LaTeX table for scenarios (7 rows).
Averages results across all mounting points and 3 trials for each scenario.
"""

import yaml
import numpy as np
from pathlib import Path
from collections import defaultdict

# Configuration
BASE_DIR = Path("../analysis/experiments")

# Scenarios mapping
SCENARIOS = {
    "1_TUG": "TUG",
    "2_walk_normal": "Chód naturalny",
    "3_walk_fast": "Chód przyspieszony",
    "4_walk_jog": "Trucht",
    "5_stairs_up": "Schody w górę",
    "6_stairs_down": "Schody w dół",
    "7_stairs_both": "Schody góra+dół",
}

# Algorithms
ALGORITHMS = [
    "Peak Detection",
    "Zero Crossing",
    "Spectral Analysis",
    "Adaptive Threshold",
    "Shoe",
]


def load_results(yaml_path):
    """Load YAML with error handling for inline dict syntax."""
    try:
        with open(yaml_path, "r") as f:
            content = f.read()

        # Fix common YAML errors: convert inline dicts to proper YAML
        if "Metrics:\n    {" in content or "Metrics:\n    {\n" in content:
            import re

            content = re.sub(
                r"Metrics:\s*\n\s*\{\s*\n(.*?)\n\s*\}",
                lambda m: "Metrics:\n"
                + "\n".join(
                    "      " + line.strip().rstrip(",")
                    for line in m.group(1).split("\n")
                    if line.strip() and line.strip() != "}"
                ),
                content,
                flags=re.DOTALL,
            )

        return yaml.safe_load(content)

    except yaml.YAMLError as e:
        print(f"WARNING: YAML parse error at {yaml_path}, trying alternative")
        try:
            import ast

            with open(yaml_path, "r") as f:
                lines = f.readlines()

            result = {"SENSOR1": {}, "SENSOR2": {}}
            current_sensor = None
            current_algo = None

            for line in lines:
                if "SENSOR1:" in line:
                    current_sensor = "SENSOR1"
                elif "SENSOR2:" in line:
                    current_sensor = "SENSOR2"
                elif any(algo in line for algo in ALGORITHMS):
                    for algo in ALGORITHMS:
                        if algo in line and line.strip().endswith(":"):
                            current_algo = algo
                            result[current_sensor][current_algo] = {"Metrics": {}}
                            break
                elif '"f1_score"' in line and current_algo:
                    import re

                    match = re.search(r'"f1_score":\s*([\d.]+)', line)
                    if match:
                        result[current_sensor][current_algo]["Metrics"]["f1_score"] = (
                            float(match.group(1))
                        )

            return result

        except Exception as e2:
            print(f"ERROR: Alternative parser also failed: {e2}")
            raise e


def calculate_avg_f1(results):
    avg_f1 = {}
    for algo in ALGORITHMS:
        f1_s1 = results["SENSOR1"][algo]["Metrics"]["f1_score"]
        f1_s2 = results["SENSOR2"][algo]["Metrics"]["f1_score"]
        avg_f1[algo] = (f1_s1 + f1_s2) / 2
    return avg_f1


def collect_data_by_scenario():
    data = defaultdict(lambda: defaultdict(list))

    for mount_dir in sorted(BASE_DIR.iterdir()):
        if not mount_dir.is_dir():
            continue

        for scenario_dir in sorted(mount_dir.iterdir()):
            if not scenario_dir.is_dir():
                continue

            scenario_name = scenario_dir.name
            if scenario_name not in SCENARIOS:
                continue

            for trial_dir in sorted(scenario_dir.iterdir()):
                if not trial_dir.is_dir():
                    continue

                yaml_path = trial_dir / "detection_results.yaml"
                if not yaml_path.exists():
                    print(f"WARNING: Missing file: {yaml_path}")
                    continue

                try:
                    results = load_results(yaml_path)
                    avg_f1 = calculate_avg_f1(results)

                    for algo, f1 in avg_f1.items():
                        data[scenario_name][algo].append(f1)

                except Exception as e:
                    print(f"ERROR at {yaml_path}: {e}")
                    continue

    return data


def calculate_scenario_averages(data):
    averages = {}

    for scenario_name, algo_data in data.items():
        averages[scenario_name] = {}

        for algo, f1_list in algo_data.items():
            if len(f1_list) > 0:
                averages[scenario_name][algo] = np.mean(f1_list)
            else:
                averages[scenario_name][algo] = None

        algo_avgs = [v for v in averages[scenario_name].values() if v is not None]
        if algo_avgs:
            averages[scenario_name]["_overall"] = np.mean(algo_avgs)
        else:
            averages[scenario_name]["_overall"] = None

    return averages


def generate_latex_table(averages):
    lines = []
    lines.append("\\begin{table}[htbp]")
    lines.append("\\centering")
    lines.append(
        "\\caption{Średnie wartości F1-score dla różnych scenariuszy testowych. "
        "Wartości uśrednione po~wszystkich punktach montażu i~trzech próbach "
        "($n = 12$ nagrań na~scenariusz). Przedstawiono średnią z~obu sensorów.}"
    )
    lines.append("\\label{tab:badania-wyniki-scenariusz}")
    lines.append("\\begin{tabular}{lcccccc}")
    lines.append("\\toprule")
    lines.append(
        "    Scenariusz & Peak Det. & Zero Cross. & Spectral & Adaptive & SHOE & Średnia \\\\"
    )
    lines.append("\\midrule")

    for scenario_key in sorted(SCENARIOS.keys()):
        if scenario_key not in averages:
            continue

        scenario_label = SCENARIOS[scenario_key]
        algo_data = averages[scenario_key]

        values = []
        for algo in ALGORITHMS:
            f1 = algo_data.get(algo)
            if f1 is not None:
                values.append(f"${f1:.2f}$")
            else:
                values.append("---")

        overall = algo_data.get("_overall")
        if overall is not None:
            values.append(f"${overall:.2f}$")
        else:
            values.append("---")

        line = f"    {scenario_label:25} & " + " & ".join(values) + " \\\\"
        lines.append(line)

    lines.append("\\bottomrule")
    lines.append("\\end{tabular}")
    lines.append("\\end{table}")

    return "\n".join(lines)


def generate_stats(data, averages):
    stats = []

    stats.append(f"\n{'='*60}")
    stats.append("STATISTICS - SCENARIOS")
    stats.append(f"{'='*60}")

    for scenario_key in sorted(SCENARIOS.keys()):
        scenario_label = SCENARIOS[scenario_key]

        if scenario_key not in data:
            stats.append(f"\n{scenario_label}: NO DATA")
            continue

        stats.append(f"\n{scenario_label}:")

        sample_algo = ALGORITHMS[0]
        n_recordings = len(data[scenario_key][sample_algo])
        stats.append(f"  Recordings: {n_recordings}")

        for algo in ALGORITHMS:
            f1 = averages[scenario_key].get(algo)
            if f1 is not None:
                stats.append(f"  {algo:25} F1 = {f1:.4f}")

        overall = averages[scenario_key].get("_overall")
        if overall is not None:
            stats.append(f"  {'OVERALL AVERAGE':25} F1 = {overall:.4f}")

    stats.append(f"\n{'='*60}\n")

    return "\n".join(stats)


def main():
    print("Collecting data by scenario...")
    data = collect_data_by_scenario()

    if not data:
        print("ERROR: No data found!")
        return

    print(f"OK: Collected data for {len(data)} scenarios")

    print("\nCalculating averages...")
    averages = calculate_scenario_averages(data)

    print("\nGenerating LaTeX table...")
    latex_table = generate_latex_table(averages)

    output_file = "table_scenarios.tex"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(latex_table)

    print(f"OK: Table saved to: {output_file}")

    stats = generate_stats(data, averages)
    print(stats)

    print("\n" + "=" * 80)
    print("TABLE PREVIEW")
    print("=" * 80)
    print(latex_table)
    print("=" * 80)

    print(f"\nDONE! Copy content of {output_file} to 04.tex")


if __name__ == "__main__":
    main()
