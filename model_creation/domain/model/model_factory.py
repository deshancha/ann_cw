# Author: Chamika Deshan
# Model Factory for Segmentation Architectures

import torch.nn as nn
from domain.model.mobilenetv1 import UNetMobileNetV1
from domain.model.mobilenetv3 import UNetMobileNetV3

# helper method to get mobilenet v1 or v3
def build_segmentation_model(
    model_type: str = "mobilenetv3",
    width: float = 1.0,
    pretrained: bool = True,
    out_channels: int = 1,
) -> nn.Module:
    m_type = model_type.lower().strip()
    if "v3" in m_type:
        return UNetMobileNetV3(
            backbone_name="mobilenetv3_small_100.lamb_in1k",
            pretrained=pretrained,
            out_channels=out_channels,
        )
    elif "v1" in m_type:
        return UNetMobileNetV1(
            width=width,
            out_channels=out_channels,
        )
    else:
        raise ValueError(f"Unknown type: {model_type}")
