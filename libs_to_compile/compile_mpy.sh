#!/bin/bash

# This script compiles all .py files in the $SRC_DIR directory to .mpy files in the $MPY_DIR directory

clear

# If you're using a different architecture, change it here
# Use "armv7emsp" for Pico 2 W
# Use "armv6m" for Pico W
# Find out your architecture with `~/.BACKUP/architecture_check.py`
ARCHITECTURE=armv7emsp

# Path to the `mpy-cross` command
MPY_CROSS_PATH="/run/media/maks/Dokumenty 2/0PROGRAMOWANIE Projekty/micropython/mpy-cross/build/mpy-cross"

# Check if mpy-cross is installed
# echo -e "$("$MPY_CROSS_PATH" -h)"
# exit 0

# Input folder with .py files
SRC_DIR="classes"

# Output folder for .mpy files
MPY_DIR="../lib/classes"

# Create the output directory
mkdir -p $MPY_DIR

echo -e "\n\nStarting compilation...\n"

# Loop through all .py files in the $SRC_DIR directory
find $SRC_DIR -name "*.py" | while read PY_FILE; do
    # Create the directory structure in $MPY_DIR directory
    DEST_DIR="$MPY_DIR/$(dirname "$PY_FILE" | sed "s|$SRC_DIR||")"
    mkdir -p "$DEST_DIR"

    # If the file is __init__.py, don't compile it, just move it
    if [[ "$(basename "$PY_FILE")" == "__init__.py" ]]; then
        echo -e "\nSkipping compilation of $PY_FILE, moving it as a .py file\n"
        cp "$PY_FILE" "$DEST_DIR/" -f # -f to overwrite existing files
    else
        # Compile the .py file to .mpy
        echo -e "\nCompiling $PY_FILE\n"
        "$MPY_CROSS_PATH" "$PY_FILE" -march="$ARCHITECTURE"
        
        # Move the .mpy file to the corresponding directory
        mv "${PY_FILE%.py}.mpy" "$DEST_DIR/" -f # -f to overwrite existing files
    fi
done

echo -e "\n\nCompilation completed.\n"
