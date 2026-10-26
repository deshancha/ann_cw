# Author: Chamika Deshan
# TFLite Export Use Case

import os
from typing import Optional
import torch

from core.util.logger import ILogger
from domain.manager.imodel_creation import IModelCreation
from domain.model.model_factory import build_segmentation_model


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
        model_type: str = "mobilenetv3",
        img_size: int = 256,
        width: float = 1.0,
        in_nhwc: bool = True,
    ) -> str:
        model = build_segmentation_model(
            model_type=model_type,
            width=width,
            pretrained=False,
            out_channels=1,
        )
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
