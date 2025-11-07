# Quick Start - Table Generation Scripts

## What you get

3 scripts that generate LaTeX tables from your experimental data:

1. **generate_table_28_rows.py** - Big table (28 rows): 4 mounting points × 7 scenarios
2. **generate_table_mounting_points.py** - Small table (4 rows): averages by mounting point  
3. **generate_table_scenarios.py** - Small table (7 rows): averages by scenario

## How to run

### Step 1: Go to your project directory

```bash
cd /path/to/your/project
```

Your structure should have:
```
../analysis/experiments/
├── 1_mount_thigh_pocket/
├── 2_mount_wrist/
├── 3_mount_arm_shoulder/
└── 4_mount_ankle/
```

### Step 2: Run the scripts

```bash
# Generate 28-row table
python generate_table_28_rows.py

# Generate 4-row table (mounting points)
python generate_table_mounting_points.py

# Generate 7-row table (scenarios)
python generate_table_scenarios.py
```

### Step 3: Copy results to your thesis

Each script creates a `.tex` file:
- `table_28_rows.tex`
- `table_mounting_points.tex`
- `table_scenarios.tex`

Open these files and copy their content to your `04.tex` file.

## Requirements

```bash
pip install pyyaml numpy
```

That's it!

## What the scripts do

**28-row table:**
- Finds all 84 recordings
- Averages 3 trials for each combination (mounting point + scenario)
- Results: 28 rows with F1 scores for 5 algorithms
- Uses `\begin{table*}` for wide table (full page width)

**4-row table:**
- Averages all scenarios for each mounting point
- Results: 4 rows (ankle, arm, wrist, pocket) with overall averages

**7-row table:**
- Averages all mounting points for each scenario
- Results: 7 rows (TUG, walks, stairs) with overall averages

## Troubleshooting

**ERROR: No data found!**
- Check if you're in the right directory
- Verify `./analysis/experiments/` exists
- Make sure YAML files are named `detection_results.yaml`

**WARNING: Missing file:**
- Some trials might be missing - script continues with available data

**Import errors:**
```bash
pip install pyyaml numpy
```

## Output example

Script shows:
1. Progress messages
2. Statistics (min/max/mean F1)
3. Preview of generated table
4. Output file name

Then just copy the `.tex` file content to your thesis!
