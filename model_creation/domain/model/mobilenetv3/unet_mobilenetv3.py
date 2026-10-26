# Author: Chamika Deshan
# UNet with Pretrained MobileNetV3 from timm and Lightweight Decoder
# This is transfer learning mobilenetv3 trained with ImageNet-1k with over 1M images

from typing import List, Optional
import torch
import torch.nn as nn
import timm

# Upsampling block (Concat with skip connection, chanel merging, upsampling with bilinear method))
class LightweightDecoderBlock(nn.Module):

    def __init__(self, in_channels: int, skip_channels: int, out_channels: int):
        super().__init__()
        self.upsample = nn.Upsample(scale_factor=2, mode="bilinear", align_corners=False)
        total_in = in_channels + skip_channels
        
        # Depthwise Separable Convolution (groups=3x3 depthwise + 1x1 pointwise)
        self.conv = nn.Sequential(
            nn.Conv2d(total_in, total_in, kernel_size=3, padding=1, groups=total_in, bias=False),
            nn.BatchNorm2d(total_in),
            nn.ReLU(inplace=True),
            nn.Conv2d(total_in, out_channels, kernel_size=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
        )

    def forward(self, x: torch.Tensor, skip: torch.Tensor) -> torch.Tensor:
        x = self.upsample(x)
        if x.shape[2:] != skip.shape[2:]:
            # this could be nearerwst neighbour, or transpose convolution
            # instread we use bilinear interpolation for 0 extra params
            x = nn.functional.interpolate(x, size=skip.shape[2:], mode="bilinear", align_corners=False)
        x = torch.cat([x, skip], dim=1)
        return self.conv(x)


class UNetMobileNetV3(nn.Module):
    """U-Net architecture with pretrained MobileNetV3 backbone from timm."""

    def __init__(
        self,
        backbone_name: str = "mobilenetv3_small_100.lamb_in1k",
        pretrained: bool = True,
        out_channels: int = 1,
    ):
        super().__init__()
        # 1 Feature extractor from timm -> mobilenetV3
        self.encoder = timm.create_model(backbone_name, pretrained=pretrained, features_only=True)
        channels = self.encoder.feature_info.channels()
        c0, c1, c2, c3, c4 = channels  # Stride 2, 4, 8, 16, 32 channels

        # 2 Depthwise-Separable Decoder
        self.up1 = LightweightDecoderBlock(c4, c3, 64)
        self.up2 = LightweightDecoderBlock(64, c2, 32)
        self.up3 = LightweightDecoderBlock(32, c1, 24)
        self.up4 = LightweightDecoderBlock(24, c0, 16)

        # 3 final upsample (stride 2 -> stride 1) and 1x1 conv head
        self.final_upsample = nn.Upsample(scale_factor=2, mode="bilinear", align_corners=False)
        self.head = nn.Conv2d(16, out_channels, kernel_size=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        features = self.encoder(x)
        f0, f1, f2, f3, f4 = features

        x = self.up1(f4, f3)        # Stride 16
        x = self.up2(x, f2)         # Stride 8
        x = self.up3(x, f1)         # Stride 4
        x = self.up4(x, f0)         # Stride 2
        x = self.final_upsample(x)  # Stride 1
        logits = self.head(x)
        return logits
