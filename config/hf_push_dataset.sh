#!/bin/bash
set -e

# This is for push the data set to hugging face - DO NOT RUN
REPO="$(cd "$(dirname "$0")/.." && pwd)"
DATA="${1:-$REPO/data_/matting_human}"
[ -d "$DATA" ] || DATA="$REPO/data/matting_human"
ZIP="$REPO/matting_human.zip"

echo "Zipping dataset from $DATA..."
(cd "$DATA/.." && zip -rq "$ZIP" "$(basename "$DATA")")

TOKEN=$(grep -E "^HF_TOKEN=" "$REPO/.env.secret" 2>/dev/null | cut -d '=' -f2 | tr -d ' "')

echo "Uploading to Hugging Face..."
"$REPO/.venv/bin/hf" upload deshanc/unet-mobilenet-portrait-segmentation "$ZIP" "dataset/matting_human.zip" ${TOKEN:+--token "$TOKEN"}

rm -f "$ZIP"
