#!/bin/bash

# Create the copy directory if it doesn't exist
mkdir -p ./copy

# Function to get relative path without leading ./
get_relative_path() {
    echo "$1" | sed 's|^\./||'
}

# Find all files in current directory and subdirectories, excluding the copy directory
find . -type f ! -path "./copy/*" | while read -r file; do
    # Get the filename without path
    filename=$(basename "$file")
    # Get the directory path without leading ./
    dirpath=$(dirname "$file")
    dirpath=$(get_relative_path "$dirpath")
    
    # Check if file already exists in copy directory
    if [ -f "./copy/$filename" ]; then
        # File exists, rename it using directory structure
        # Replace / with _ in directory path
        new_filename="${dirpath//\//_}_${filename}"
        cp "$file" "./copy/$new_filename"
    else
        # File doesn't exist, simple copy
        cp "$file" "./copy/$filename"
    fi
done
