#!/bin/bash
set -e

VERSION="${1:?Usage: sh ./app/config/hf_push.sh <version>}"
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
DIR="$REPO/model_creation/output/checkpoints"

# Zip any .mlpackage for iOS
for p in "$DIR"/*.mlpackage; do [ -d "$p" ] && (cd "$DIR" && zip -rq -o "$(basename "$p").zip" "$(basename "$p")"); done

TOKEN=$(grep -E "^HF_TOKEN=" "$REPO/.env.secret" 2>/dev/null | cut -d '=' -f2 | tr -d ' "')
echo "Uploading ${VERSION} to Hugging Face..."
"$REPO/.venv/bin/hf" upload deshanc/unet-mobilenet-portrait-segmentation "$DIR" "$VERSION" ${TOKEN:+--token "$TOKEN"}

echo "Done!"
