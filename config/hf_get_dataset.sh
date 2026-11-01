#!/bin/bash
set -e

URL="https://huggingface.co/deshanc/unet-mobilenet-portrait-segmentation/resolve/main/dataset/matting_human.zip"
TARGET="$(cd "$(dirname "$0")/.." && pwd)/data"
ZIP="$TARGET/matting_human.zip"

if [ -d "$TARGET/matting_human" ]; then
    echo "Dataset already exists at $TARGET/matting_human"
    exit 0
fi

mkdir -p "$TARGET"
echo "Downloading dataset..."
curl -L --progress-bar "$URL" -o "$ZIP"

echo "Extracting..."
unzip -q -o "$ZIP" -d "$TARGET"
rm -f "$ZIP"

echo "Done! Dataset saved to $TARGET/matting_human"
