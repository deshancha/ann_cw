"""UNet Segmentation with MobileNetV1 encoder
Notes
1. feature extractor is MobileNetV1Encoder and reconstruction with UNetDecoder
2. Encoder output -> input into the decoder
"""
import torch
import torch.nn as nn

from domain.model.mobilenetv1.mobilenetv1 import MobileNetV1Encoder
from domain.model.mobilenetv1.unet_decoder import UNetDecoder


class UNetMobileNetV1(nn.Module):
    def __init__(
        self,
        width: float = 1.0,
        out_channels: int = 1,
    ):
        super().__init__()
        self.encoder = MobileNetV1Encoder(width=width)
        self.decoder = UNetDecoder(
            encoder_channels=self.encoder.feature_channels, out_channels=out_channels
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        features = self.encoder(x)
        raw_mask_scores = self.decoder(features)
        return raw_mask_scores
