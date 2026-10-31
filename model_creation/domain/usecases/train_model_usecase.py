# Author: Chamika Deshan
# Train Model Use Case

import os
import time
from typing import Dict, Any, Optional
import torch

from core.util.logger import ILogger
from domain.manager.isegmentation_loader import ISegmentationLoader
from domain.manager.imodel_creation import IModelCreation
from domain.model.model_factory import build_segmentation_model
from domain.model.loss import BCEDiceLoss

# Train UNetMobileNetV1 and save checkpoint
class TrainModelUseCase:
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
        model_type: str = "mobilenetv3",
        epochs: int = 3,
        batch_size: int = 16,
        learning_rate: float = 0.001,
        img_size: int = 224,
        width: float = 1.0,
        seed: int = 42,
        device: str = "mps",
        checkpoints_dir: str = "checkpoints",
        max_train_samples: int = 0,
        max_val_samples: int = 0,
    ) -> Dict[str, Any]:
        torch.manual_seed(seed)

        # 1 Load
        self.logger.info(
            f"Loading dataset (img_size={img_size}, batch_size={batch_size}, "
            f"sample_size={max_train_samples}, val_sample_size={max_val_samples})"
        )
        train_loader, val_loader = self.data_loader.get_dataloaders(
            img_size=img_size,
            batch_size=batch_size,
            val_split=0.2,
            max_train_samples=max_train_samples,
            max_val_samples=max_val_samples,
        )

        # 2 Build Model
        self.logger.info(f"Create segmentation model: {model_type}, width: {width}, input_size: {img_size}x{img_size}")
        model = build_segmentation_model(
            model_type=model_type,
            width=width,
            pretrained=True,
            out_channels=1,
        ).to(device)
        optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-5)
        loss_fn = BCEDiceLoss(bce_weight=0.5, dice_weight=0.5)

        best_val_iou = 0.0
        best_pt_path = os.path.join(checkpoints_dir, f"unet_{model_type}_best.pt")
        history = {"train_loss": [], "val_loss": [], "val_iou": [], "val_dice": []}

        # 3 Training
        self.logger.info(f"Epochs: {epochs}, Device {device}...")
        for epoch in range(1, epochs + 1):
            t0 = time.time()

            train_loss = self.model_creation.train_epoch(
                model=model,
                train_loader=train_loader,
                optimizer=optimizer,
                loss_fn=loss_fn,
                device=device,
            )
            scheduler.step()

            val_loss, val_iou, val_dice = self.model_creation.validate(
                model=model,
                val_loader=val_loader,
                loss_fn=loss_fn,
                device=device,
            )
            elapsed = time.time() - t0

            self.logger.info(
                f"Epoch {epoch}, Train Loss: {train_loss}, "
                f"Validation Loss: {val_loss}, Validation IoU: {val_iou}, "
                f"Validation Dice: {val_dice}, Time: {elapsed:.1f}s"
            )


            history["train_loss"].append(train_loss)
            history["val_loss"].append(val_loss)
            history["val_iou"].append(val_iou)
            history["val_dice"].append(val_dice)

            if val_iou > best_val_iou:
                best_val_iou = val_iou
                self.model_creation.save_checkpoint(model, best_pt_path)
                self.logger.info(f"So far best model - Validation IoU: {val_iou})")

        # 4 Save Last Weights
        final_pt_path = os.path.join(checkpoints_dir, f"unet_{model_type}_final.pt")
        self.model_creation.save_checkpoint(model, final_pt_path)

        return {
            "best_pt": best_pt_path,
            "final_pt": final_pt_path,
            "best_val_iou": best_val_iou,
            "history": history,
        }
