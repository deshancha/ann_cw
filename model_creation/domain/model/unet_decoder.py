"""U-Net Decoder for segmentation (alphja texture)
Takes feature map from encder (MobilenetV1)
Upsample -> concat to create mask
"""
from typing import List
import torch
import torch.nn as nn


class DecoderBlock(nn.Module):
    """Upsample block: [2x bilinear upsample] -> [channel concat] -> [2x Conv-BN-ReLU]"""

    def __init__(self, in_channels: int, skip_channels: int, out_channels: int):
        super().__init__()
        self.upsample = nn.Upsample(scale_factor=2, mode="bilinear", align_corners=False)
        total_in = in_channels + skip_channels
        self.conv = nn.Sequential(
            nn.Conv2d(total_in, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
        )

    def forward(self, x: torch.Tensor, skip: torch.Tensor) -> torch.Tensor:
        x = self.upsample(x)
        # Ensure dimensions match
        if x.shape[2:] != skip.shape[2:]:
            x = nn.functional.interpolate(x, size=skip.shape[2:], mode="bilinear", align_corners=False)
        x = torch.cat([x, skip], dim=1)
        return self.conv(x)


class UNetDecoder(nn.Module):
    """U-Net Decoder that accepts multi-scale encoder features.

    Expects encoder_channels = [c_stride2, c_stride4, c_stride8, c_stride16, c_stride32]
    e.g. for MobileNetV1 width=1.0: [64, 128, 256, 512, 1024]
    """

    def __init__(self, encoder_channels: List[int], out_channels: int = 1):
        super().__init__()
        c0, c1, c2, c3, c4 = encoder_channels

        # Up 1: stride 32 -> stride 16 (concat with c3)
        self.up1 = DecoderBlock(in_channels=c4, skip_channels=c3, out_channels=256)
        # Up 2: stride 16 -> stride 8 (concat with c2)
        self.up2 = DecoderBlock(in_channels=256, skip_channels=c2, out_channels=128)
        # Up 3: stride 8 -> stride 4 (concat with c1)
        self.up3 = DecoderBlock(in_channels=128, skip_channels=c1, out_channels=64)
        # Up 4: stride 4 -> stride 2 (concat with c0)
        self.up4 = DecoderBlock(in_channels=64, skip_channels=c0, out_channels=32)

        # Final Up: stride 2 -> full resolution (stride 1)
        self.final_upsample = nn.Upsample(scale_factor=2, mode="bilinear", align_corners=False)
        self.final_conv = nn.Sequential(
            nn.Conv2d(32, 32, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, out_channels, kernel_size=1)
        )

    def forward(self, features: List[torch.Tensor]) -> torch.Tensor:
        """Decode encoder features -> to mask

        features: [f0 (stride 2), f1 (stride 4), f2 (stride 8), f3 (stride 16), f4 (stride 32)]
        """
        f0, f1, f2, f3, f4 = features

        x = self.up1(f4, f3)  # stride 16
        x = self.up2(x, f2)   # stride 8
        x = self.up3(x, f1)   # stride 4
        x = self.up4(x, f0)   # stride 2
        x = self.final_upsample(x)  # stride 1 (original size)
        logits = self.final_conv(x)
        return logits
