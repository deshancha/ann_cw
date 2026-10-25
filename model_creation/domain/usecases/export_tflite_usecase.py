# Author: Chamika Deshan
# TFLite Export Use Case

import os
from typing import Optional
import torch

from core.util.logger import ILogger
from domain.manager.imodel_creation import IModelCreation
from domain.model.unet_mobilenet import UNetMobileNetV1


class ExportTFLiteUseCase:
    def __init__(
        self,
        model_creation: IModelCreation,
        logger: ILogger,
    ):
        self.model_creation = model_creation
        self.logger = logger

    def execute(
        self,
        checkpoint_path: str,
        output_path: str,
        img_size: int = 256,
        width: float = 1.0,
        in_nhwc: bool = True,
    ) -> str:
        model = UNetMobileNetV1(width=width, out_channels=1)
        state_dict = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
        model.load_state_dict(state_dict)
        model.eval()

        self.model_creation.export_tflite(
            model=model,
            filepath=output_path,
            img_size=img_size,
            in_nhwc=in_nhwc,
        )

        return output_path
