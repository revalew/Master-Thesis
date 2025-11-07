#!/usr/bin/env python3
"""
Generate LaTeX table with 28 rows (4 mounting points × 7 scenarios).
Each row: average F1 from 3 trials and both sensors.
"""

import yaml
import numpy as np
from pathlib import Path
from collections import defaultdict

# Configuration
BASE_DIR = Path("../analysis/experiments")

# Mounting points mapping
MOUNT_POINTS = {
    "1_mount_thigh_pocket": "Kieszeń (udo)",
    "2_mount_wrist": "Nadgarstek",
    "3_mount_arm_shoulder": "Ramię",
    "4_mount_ankle": "Kostka",
}

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
        # Replace "Metrics:\n    {" with "Metrics:"
        if "Metrics:\n    {" in content or "Metrics:\n    {\n" in content:
            import re

            # Remove the inline dict braces and fix indentation
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
        # Try alternative: parse as Python literal
        print(f"WARNING: YAML parse error, trying alternative parser")
        try:
            import ast

            with open(yaml_path, "r") as f:
                lines = f.readlines()

            # Build structure manually
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
                elif "Metrics:" in line:
                    # Next line should start dict
                    continue
                elif "{" in line and current_algo:
                    # Start collecting dict content
                    dict_lines = [line]
                    continue
                elif '"f1_score"' in line and current_algo:
                    # Extract f1_score value
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


def collect_all_data():
    data = defaultdict(lambda: defaultdict(list))

    for mount_dir in sorted(BASE_DIR.iterdir()):
        if not mount_dir.is_dir():
            continue

        mount_name = mount_dir.name
        if mount_name not in MOUNT_POINTS:
            continue

        for scenario_dir in sorted(mount_dir.iterdir()):
            if not scenario_dir.is_dir():
                continue

            scenario_name = scenario_dir.name
            if scenario_name not in SCENARIOS:
                continue

            trial_f1_scores = defaultdict(list)

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
                        trial_f1_scores[algo].append(f1)

                except Exception as e:
                    print(f"ERROR at {yaml_path}: {e}")
                    continue

            for algo, f1_list in trial_f1_scores.items():
                if len(f1_list) > 0:
                    avg = np.mean(f1_list)
                    data[(mount_name, scenario_name)][algo] = avg
                else:
                    data[(mount_name, scenario_name)][algo] = None

    return data


def generate_latex_table(data):
    lines = []
    lines.append("\\begin{table*}[htbp]")
    lines.append("\\centering")
    lines.append(
        "\\caption{Średnie wartości F1-score dla wszystkich kombinacji "
        "punkt montażu × scenariusz. Wartości uśrednione z~3~prób i~obu "
        "sensorów ($n = 3$ nagrania na~kombinację). Tabela prezentuje "
        "szczegółowe porównanie skuteczności algorytmów w~różnych "
        "warunkach testowych.}"
    )
    lines.append("\\label{tab:badania-wyniki-wszystkie}")
    lines.append("\\begin{tabular}{llccccc}")
    lines.append("\\toprule")
    lines.append(
        "    Punkt montażu & Scenariusz & Peak Det. & Zero Cross. & "
        "Spectral & Adaptive & SHOE \\\\"
    )
    lines.append("\\midrule")

    prev_mount = None
    for mount_key, scenario_key in sorted(data.keys()):
        mount_label = MOUNT_POINTS[mount_key]
        scenario_label = SCENARIOS[scenario_key]

        algo_data = data[(mount_key, scenario_key)]

        values = []
        for algo in ALGORITHMS:
            f1 = algo_data.get(algo)
            if f1 is not None:
                values.append(f"${f1:.2f}$")
            else:
                values.append("---")

        if prev_mount is not None and prev_mount != mount_key:
            lines.append("    \\cmidrule(r){1-7}")

        line = f"    {mount_label} & {scenario_label} & " + " & ".join(values) + " \\\\"
        lines.append(line)

        prev_mount = mount_key

    lines.append("\\bottomrule")
    lines.append("\\end{tabular}")
    lines.append("\\end{table*}")

    return "\n".join(lines)


def generate_summary_stats(data):
    stats = []

    total_combos = len(data)
    expected_combos = len(MOUNT_POINTS) * len(SCENARIOS)

    stats.append(f"\n{'='*60}")
    stats.append("SUMMARY STATISTICS")
    stats.append(f"{'='*60}")
    stats.append(f"Found combinations: {total_combos}/{expected_combos}")
    stats.append(f"Mounting points: {len(MOUNT_POINTS)}")
    stats.append(f"Scenarios: {len(SCENARIOS)}")
    stats.append(f"Algorithms: {len(ALGORITHMS)}")
    stats.append("")

    all_f1_scores = []
    for combo_data in data.values():
        for algo in ALGORITHMS:
            f1 = combo_data.get(algo)
            if f1 is not None:
                all_f1_scores.append(f1)

    if all_f1_scores:
        stats.append(f"Global F1-score:")
        stats.append(f"  Min:     {min(all_f1_scores):.4f}")
        stats.append(f"  Max:     {max(all_f1_scores):.4f}")
        stats.append(f"  Mean:    {np.mean(all_f1_scores):.4f}")
        stats.append(f"  Std:     {np.std(all_f1_scores):.4f}")

    stats.append(f"{'='*60}\n")

    return "\n".join(stats)


def main():
    print("Collecting data from experiments...")
    data = collect_all_data()

    if not data:
        print("ERROR: No data found!")
        return

    print(f"OK: Collected data for {len(data)} combinations")

    print("\nGenerating LaTeX table...")
    latex_table = generate_latex_table(data)

    output_file = "table_28_rows.tex"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(latex_table)

    print(f"OK: Table saved to: {output_file}")

    stats = generate_summary_stats(data)
    print(stats)

    print("\n" + "=" * 80)
    print("TABLE PREVIEW (first 10 rows)")
    print("=" * 80)
    lines = latex_table.split("\n")
    for line in lines[:20]:
        print(line)
    print("...")
    print("=" * 80)

    print(f"\nDONE! Copy content of {output_file} to 04.tex")


if __name__ == "__main__":
    main()
