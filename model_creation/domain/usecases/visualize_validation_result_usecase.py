# Author: Chamika Deshan
# Visualize Validation Result Use Case

import os
from typing import Optional
import torch

from core.util.logger import ILogger
from domain.manager.isegmentation_loader import ISegmentationLoader
from domain.manager.imodel_creation import IModelCreation
from domain.model.model_factory import build_segmentation_model

# crearte image with original | mask | gen mask | Blurred fro mtrained model
class VisualizeValidationResultUseCase:
    
    def __init__(
        self,
        data_loader: ISegmentationLoader,
        model_creation: IModelCreation,
        logger: ILogger,
    ):
        self.data_loader = data_loader
        self.model_creation = model_creation
        self.logger = logger

    def execute(
        self,
        checkpoint_path: str,
        model_type: str = "mobilenetv3",
        img_size: int = 224,
        width: float = 1.0,
        device: str = "mps",
        output_dir: str = "outputs",
    ) -> str:
        _, val_loader = self.data_loader.get_dataloaders(
            img_size=img_size,
            batch_size=16,
            val_split=0.2,
            max_train_samples=1,
            max_val_samples=20,
        )

        model = build_segmentation_model(
            model_type=model_type,
            width=width,
            pretrained=False,
            out_channels=1,
        ).to(device)
        state_dict = torch.load(checkpoint_path, map_location=device, weights_only=True)
        model.load_state_dict(state_dict)
        model.eval()

        vis_path = self.model_creation.generate_validation_image(
            model=model,
            val_loader=val_loader,
            device=device,
            output_dir=output_dir,
        )

        return vis_path
