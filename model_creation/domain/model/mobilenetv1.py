"""MobileNetV1 as the paper 2017
Serve as feature extraction part of the UNet
Takes input img (Batch size, channels, H, W) and returns 5 feature maps [f0, f1, f2, f3, f4]
strides [2, 4, 8, 16, 32] -> goeso to UNet skip connections
"""
from typing import List
import torch
import torch.nn as nn


# This is the standard convolution block, very fiorst part of the layer
# Paper => [F -> StdConv(3x3) -> Batch Norm -> RELU]
def conv_standard(inp: int, out: int, stride: int) -> nn.Sequential:
    return nn.Sequential(
        nn.Conv2d(inp, out, kernel_size=3, stride=stride, padding=1, bias=False),
        nn.BatchNorm2d(out),
        nn.ReLU(inplace=True),
    )


# This is the depthwise separable convolution block, as the paper
# Paper => [F -> StdConv -> Batch Norm -> RELU -> Conv 1x1 -> Batch Norm -> RELU]
def conv_depth_wise_seperable(inp: int, out: int, stride: int) -> nn.Sequential:
    return nn.Sequential(
        # 1. Depthwise: 3x3 spatial filter per input channel
        nn.Conv2d(inp, inp, kernel_size=3, stride=stride, padding=1, groups=inp, bias=False),
        nn.BatchNorm2d(inp),
        nn.ReLU(inplace=True),
        # 2. Pointwise: 1x1 channel-mixing convolution
        nn.Conv2d(inp, out, kernel_size=1, stride=1, padding=0, bias=False),
        nn.BatchNorm2d(out),
        nn.ReLU(inplace=True),
    )


# (in_channels, out_channels, stride)
CONFIG_FOR_13_DEPTHWISE_SEPERABLE_BLOCKS = [
    (32, 64, 1),
    (64, 128, 2),
    (128, 128, 1),
    (128, 256, 2),
    (256, 256, 1),
    (256, 512, 2),
    (512, 512, 1),
    (512, 512, 1),
    (512, 512, 1),
    (512, 512, 1),
    (512, 512, 1),
    (512, 1024, 2),
    (1024, 1024, 1),
]


class MobileNetV1Encoder(nn.Module):
    """MobileNetV1 Feature Extractor designed specifically for U-Net skip connections."""

    # width = 1.0 -> no shrinking and no reducing of num kernels
    def __init__(self, width: float = 1.0):
        """num_classes=0 -> no classifier (we need this for encoding only for unet)"""
        super().__init__()
        self.width = width
        c = lambda x: max(8, int(x * width))

        # Initial standard convolution (stride 2)
        self.stem = conv_standard(3, c(32), stride=2)

        # 13 Depthwise Separable Blocks
        self.blocks = nn.ModuleList([
            conv_depth_wise_seperable(c(i), c(o), s)
            for i, o, s in CONFIG_FOR_13_DEPTHWISE_SEPERABLE_BLOCKS
        ])

        # Channel counts -> 5 tap points (strides 2, 4, 8, 16, 32)
        # At width=1.0 : [64, 128, 256, 512, 1024]
        self.feature_channels = [c(64), c(128), c(256), c(512), c(1024)]

    def forward(self, x: torch.Tensor) -> List[torch.Tensor]:
        """Extracts and returns the 5 multi-scale feature maps for U-Net decoder."""
        feats = []
        x = self.stem(x)
        for i, blk in enumerate(self.blocks):
            x = blk(x)
            # tap points at end stages
            if i in (0, 2, 4, 10, 12):
                feats.append(x)
        return feats
