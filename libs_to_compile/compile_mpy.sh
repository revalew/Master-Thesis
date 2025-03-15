#!/bin/bash

# This script compiles all .py files in the $SRC_DIR directory to .mpy files in the $MPY_DIR directory
# and copies any existing .mpy files while maintaining the original directory structure.

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

# Input folder with .py and .mpy files
SRC_DIR="classes"

# Output folder for .mpy files
MPY_DIR="../lib/classes"

# Create the output directory
mkdir -p "$MPY_DIR"

echo -e "\n\nStarting compilation and copying...\n"

# Loop through all .py files in the $SRC_DIR directory, following symlinks
find -L "$SRC_DIR" -name "*.py" | while read PY_FILE; do
    # Create the directory structure in $MPY_DIR directory
    DEST_DIR="$MPY_DIR/$(dirname "$PY_FILE" | sed "s|$SRC_DIR||")"
    mkdir -p "$DEST_DIR"

    # Define destination file path
    DEST_FILE="$DEST_DIR/$(basename "$PY_FILE")"

    # If the file is __init__.py, don't compile it, just move it
    if [[ "$(basename "$PY_FILE")" == "__init__.py" ]]; then
        echo -e "\nSkipping compilation:"
        echo -e "Source: $PY_FILE"
        echo -e "Destination: $DEST_FILE\n"
        cp "$PY_FILE" "$DEST_FILE" -f # -f to overwrite existing files
    else
        # Compile the .py file to .mpy
        echo -e "\nCompiling:"
        echo -e "Source: $PY_FILE\n"
        "$MPY_CROSS_PATH" "$PY_FILE" -march="$ARCHITECTURE"

        # Move the .mpy file to the corresponding directory
        SRC_MPY_FILE="${PY_FILE%.py}.mpy"
        DEST_MPY_FILE="$DEST_DIR/$(basename "$SRC_MPY_FILE")"

        echo -e "Moving compiled file:"
        echo -e "From: $SRC_MPY_FILE"
        echo -e "To:   $DEST_MPY_FILE\n"

        mv "$SRC_MPY_FILE" "$DEST_MPY_FILE" -f # -f to overwrite existing files
    fi
done

# Copy all existing .mpy files while maintaining directory structure
find -L "$SRC_DIR" -name "*.mpy" | while read MPY_FILE; do
    DEST_DIR="$MPY_DIR/$(dirname "$MPY_FILE" | sed "s|$SRC_DIR||")"
    mkdir -p "$DEST_DIR"

    DEST_FILE="$DEST_DIR/$(basename "$MPY_FILE")"

    echo -e "\nCopying existing .mpy file:"
    echo -e "Source: $MPY_FILE"
    echo -e "Destination: $DEST_FILE\n"
    cp "$MPY_FILE" "$DEST_FILE" -f # -f to overwrite existing files
done

echo -e "\n\nCompilation and copying completed.\n"
