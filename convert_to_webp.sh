#!/bin/bash

# Default quality setting
QUALITY=80

# Check if a directory argument is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <directory> [quality]"
    echo "Example: $0 /path/to/images 90"
    echo "Quality range: 0-100 (default: 80)"
    exit 1
fi

# Get the directory from the first argument
DIR="$1"

# Get quality from second argument if provided
if [ $# -ge 2 ]; then
    QUALITY="$2"
    # Validate quality range
    if [ "$QUALITY" -lt 0 ] || [ "$QUALITY" -gt 100 ]; then
        echo "Error: Quality must be between 0 and 100"
        exit 1
    fi
fi

# Check if the directory exists
if [ ! -d "$DIR" ]; then
    echo "Error: Directory '$DIR' does not exist"
    exit 1
fi

# Path to cwebp
CWEBP="../Downloads/libwebp/bin/cwebp"

# Check if cwebp exists
if [ ! -f "$CWEBP" ]; then
    echo "Error: cwebp not found at $CWEBP"
    exit 1
fi

echo "Converting images with quality setting: $QUALITY"
echo "----------------------------------------"

# Counter for converted images
count=0

# Process all .jpg and .png files in the directory
for file in "$DIR"/*.{jpg,png,JPG,PNG}; do
    # Skip if no files match the pattern
    [ -e "$file" ] || continue
    
    # Get the filename without extension
    filename=$(basename "$file")
    name="${filename%.*}"
    
    # Output path (in the same directory as source)
    output="$DIR/$name.webp"
    
    # Convert to webp with quality setting
    echo "Converting: $filename -> $name.webp"
    "$CWEBP" "$file" -q "$QUALITY" -o "$output"
    
    ((count++))
done

echo "----------------------------------------"
echo "Conversion complete! Converted $count images at quality $QUALITY."
