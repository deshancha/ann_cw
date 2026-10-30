#!/bin/bash
set -e

REPO="https://huggingface.co/deshanc/unet-mobilenet-portrait-segmentation/resolve/main"
TARGET="$(cd "$(dirname "$0")/../.." && pwd)/model_creation/output/all_trained"
mkdir -p "$TARGET"

get() {
    [ -f "$TARGET/$3" ] || curl -L --progress-bar "$REPO/$1/$2" -o "$TARGET/$3"
}

get "v1.0" "unet_mobilenetv1_full_best.pt" "v1.0_mobilenetv1_w1.0_best.pt"
get "v1.1" "unet_mobilenetv1_full_best.pt" "v1.1_mobilenetv1_w1.0_best.pt"
get "v1.2" "unet_mobilenetv3_best.pt"      "v1.2_mobilenetv3_best.pt"
get "v1.3" "unet_mobilenetv1_best.pt"      "v1.3_mobilenetv1_w0.5_best.pt"

echo "Done! Checkpoints saved to $TARGET"
