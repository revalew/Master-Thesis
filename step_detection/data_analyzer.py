from parser import SimpleAnalyzer

if __name__ == "__main__":
    analyzer = SimpleAnalyzer()
    # Find all dirs (84 lmao) for each scenario and mounting point combination.
    # Given path is treated as the root - if you want the target to be more specific
    # change the path to something like
    # ./analysis/experiments/1_mount_thigh_pocket/1_TUG
    # to target ONLY the TUG scenario OR even more specific
    # ./analysis/experiments/1_mount_thigh_pocket/1_TUG/tug_thigh_1
    # though at this point you might just use the GUI (works exactly the same way)
    analyzer.analyze_directory("./analysis/experiments")