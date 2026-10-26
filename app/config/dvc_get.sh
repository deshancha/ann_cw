#!/bin/bash
set -e

# Resolve project and repo root
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_PATH="$(cd "$SCRIPT_DIR/../.." && pwd)"
TARGET_DIR="$REPO_PATH/app/core_ios/Model"
TARGET="$TARGET_DIR/UNetMobileNetFull.mlpackage"

# Find DVC binary
if command -v dvc &> /dev/null; then
    DVC_BIN="dvc"
elif [ -f "$REPO_PATH/.venv/bin/dvc" ]; then
    DVC_BIN="$REPO_PATH/.venv/bin/dvc"
else
    echo "ERROR: dvc command not found. Please activate your virtual environment."
    exit 1
fi

# Default version is v1.3 or passed as argument: sh ./app/config/dvc_get.sh v1.2
VERSION="${1:-v1.3}"

# 1. Detect which .mlpackage exists in this git revision (V1 vs V3)
echo "==> Checking available models in revision: ${VERSION}..."
CHECKPOINTS_DIR="model_creation/output/checkpoints"
ML_PACKAGE=$($DVC_BIN list "$REPO_PATH" "$CHECKPOINTS_DIR" --rev "${VERSION}" 2>/dev/null | grep -E "UNet.*\.mlpackage" | head -n 1 || true)

if [ -z "$ML_PACKAGE" ]; then
    # Fallback for older tags (v1.0, v1.1, v1.2) where checkpoints were at repo root
    CHECKPOINTS_DIR="checkpoints"
    ML_PACKAGE=$($DVC_BIN list "$REPO_PATH" "$CHECKPOINTS_DIR" --rev "${VERSION}" 2>/dev/null | grep -E "UNet.*\.mlpackage" | head -n 1 || true)
fi

if [ -z "$ML_PACKAGE" ]; then
    ML_PACKAGE="UNetMobileNetV1Full.mlpackage"
fi

echo "==> Found model: $CHECKPOINTS_DIR/$ML_PACKAGE"

# 2. Clean existing ml package
mkdir -p "$TARGET_DIR"
if [ -d "$TARGET" ]; then
    echo "==> Removing existing model : $TARGET"
    rm -rf "$TARGET"
fi

# Remove legacy package name if present
if [ -d "$TARGET_DIR/UNetMobileNetV1Full.mlpackage" ]; then
    rm -rf "$TARGET_DIR/UNetMobileNetV1Full.mlpackage"
fi

# 3. Fetch the .mlpackage directly into app/core_ios/Model/UNetMobileNetFull.mlpackage
echo "==> Fetching $CHECKPOINTS_DIR/$ML_PACKAGE to $TARGET..."
$DVC_BIN get "$REPO_PATH" \
    "$CHECKPOINTS_DIR/$ML_PACKAGE" \
    --rev "${VERSION}" \
    -o "$TARGET"

echo "==> Model successfully updated for core_ios build: $TARGET"
