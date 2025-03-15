#!/bin/bash

# REMEMBER TO MAKE THIS SCRIPT EXECUTABLE
# chmod +x mpy_compile_all_libs.sh

# Then run it
# ./mpy_compile_all_libs.sh

# This script compiles all .py files in the $SRC_DIR directory to .mpy files in the $MPY_DIR directory
# while maintaining the original directory structure, and skips compiling __init__.py files

clear

# If you're using a different architecture, change it here
# Use "armv7emsp" for Pico 2 W
# Use "armv6m" for Pico W
# Find out your architecture with `~/.BACKUP/architecture_check.py`
ARCHITECTURE=armv7emsp

# Path to the `mpy-cross` command
MPY_CROSS_PATH="/run/media/maks/Dokumenty 2/0PROGRAMOWANIE Projekty/micropython/mpy-cross/build/mpy-cross"

# Input folder with .py files
SRC_DIR="./lib"

# Output folder for .mpy files
MPY_DIR="../lib"

# Create the output directory
mkdir -p "$MPY_DIR"

echo -e "\n\nStarting compilation...\n"

# Loop through all .py and .mpy files in the $SRC_DIR directory, **following symlinks**
find -L "$SRC_DIR" \( -name "*.py" -o -name "*.mpy" \) | while read FILE; do
    # Create the corresponding directory structure in the $MPY_DIR directory
    DEST_DIR="$MPY_DIR/$(dirname "$FILE" | sed "s|$SRC_DIR||")"
    mkdir -p "$DEST_DIR"

    # Define destination file path
    DEST_FILE="$DEST_DIR/$(basename "$FILE")"

    # If the file is __init__.py, don't compile it, just move it
    if [[ "$(basename "$FILE")" == "__init__.py" ]]; then
        echo -e "\nSkipping compilation of: $FILE"
        echo -e "Copying to: $DEST_FILE\n"
        cp "$FILE" "$DEST_FILE" -f # -f to overwrite existing files
    elif [[ "$(basename "$FILE")" == *.mpy ]]; then
        # If it's a .mpy file, just copy it 1:1
        echo -e "\nCopying existing .mpy file:"
        echo -e "From: $FILE"
        echo -e "To:   $DEST_FILE\n"
        cp "$FILE" "$DEST_FILE" -f # -f to overwrite existing files
    else
        # Compile the .py file to .mpy
        echo -e "\nCompiling $FILE to .mpy"
        "$MPY_CROSS_PATH" "$FILE" -march="$ARCHITECTURE"

        # Move the .mpy file to the corresponding directory
        SRC_MPY_FILE="${FILE%.py}.mpy"
        DEST_MPY_FILE="$DEST_DIR/$(basename "$SRC_MPY_FILE")"

        echo -e "Moving compiled file:"
        echo -e "From: $SRC_MPY_FILE"
        echo -e "To:   $DEST_MPY_FILE\n"

        mv "$SRC_MPY_FILE" "$DEST_MPY_FILE" -f # -f to overwrite existing files
    fi
done

echo -e "\n\nCompilation completed.\n"
