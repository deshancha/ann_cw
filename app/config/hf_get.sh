#!/bin/bash
set -e

VERSION="${1:-v1.3}"
case "$VERSION" in
    v1.0|v1.1) PKG="UNetMobileNetV1Full" ;;
    v1.2)      PKG="UNet_mobilenetv3" ;;
    *)         VERSION="v1.3"; PKG="UNet_mobilenetv1" ;;
esac

TARGET="$(cd "$(dirname "$0")/../.." && pwd)/app/core_ios/Model/UNetMobileNetFull.mlpackage"
URL="https://huggingface.co/deshanc/unet-mobilenet-portrait-segmentation/resolve/main/${VERSION}/${PKG}.mlpackage.zip"

echo "Fetching ${VERSION} into ${TARGET}..."
rm -rf "$TARGET" && mkdir -p "$TARGET"
curl -L --fail --progress-bar "$URL" -o /tmp/m.zip
unzip -qo /tmp/m.zip -d "$TARGET" && rm -f /tmp/m.zip

echo "Done!"
