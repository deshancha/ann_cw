# Author: Chamika Deshan
# Validate Model Use Case

import os
import json
from typing import Dict, Any, Optional
import torch

from core.util.logger import ILogger
from domain.manager.isegmentation_loader import ISegmentationLoader
from domain.manager.imodel_creation import IModelCreation
from domain.model.model_factory import build_segmentation_model
from domain.model.loss import BCEDiceLoss

# Evaluate the model ans asave dvc matrics
class ValidateModelUseCase:
    
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
        batch_size: int = 16,
        img_size: int = 224,
        width: float = 1.0,
        device: str = "mps",
        metrics_dir: str = "metrics",
        max_val_samples: int = 0,
    ) -> Dict[str, Any]:
        os.makedirs(metrics_dir, exist_ok=True)

        # 1 Load validation Data
        self.logger.info(f"Loading validation set (img_size={img_size}, max_val_samples={max_val_samples})...")
        _, val_loader = self.data_loader.get_dataloaders(
            img_size=img_size,
            batch_size=batch_size,
            val_split=0.2,
            max_train_samples=1,  # Minimal since train is not used
            max_val_samples=max_val_samples,
        )

        # 2 Load Model
        self.logger.info(f"Loading {model_type} model from: {checkpoint_path}")
        model = build_segmentation_model(
            model_type=model_type,
            width=width,
            pretrained=False,
            out_channels=1,
        ).to(device)
        state_dict = torch.load(checkpoint_path, map_location=device, weights_only=True)
        model.load_state_dict(state_dict)
        model.eval()

        loss_fn = BCEDiceLoss(bce_weight=0.5, dice_weight=0.5)

        # 3 Validate, this is mode lvalidation for saving matix data for dvc checkout
        val_loss, val_iou, val_dice = self.model_creation.validate(
            model=model,
            val_loader=val_loader,
            loss_fn=loss_fn,
            device=device,
        )

        metrics = {
            "val_loss": round(float(val_loss), 4),
            "val_iou": round(float(val_iou), 4),
            "val_dice": round(float(val_dice), 4),
            "checkpoint": os.path.basename(checkpoint_path),
        }

        # 4 Save metrics.json
        metrics_file = os.path.join(metrics_dir, "metrics.json")
        with open(metrics_file, "w") as f:
            json.dump(metrics, f, indent=2)

        self.logger.info(
            f"Done!, Validation Loss: {metrics['val_loss']}, "
            f"Validation IoU: {metrics['val_iou']}, "
            f"Validation Dice: {metrics['val_dice']}"
        )
        self.logger.info(f"Metrics saved to: {metrics_file}")
        return metrics
