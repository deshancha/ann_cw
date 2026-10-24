# Author: Chamika Deshan
# Model Creation Implementation

import os
from typing import Tuple
import numpy as np
import coremltools as ct
from PIL import Image, ImageFilter
import torch
from torch.utils.data import DataLoader

from core.util.logger import ILogger
from domain.manager.imodel_creation import IModelCreation
from domain.model.loss import calculate_iou_and_dice


class ModelCreationImp(IModelCreation):
    
    def __init__(self, logger: ILogger):
        self.logger = logger

    def train_epoch(
        self,
        model: torch.nn.Module,
        train_loader: DataLoader,
        optimizer: torch.optim.Optimizer,
        loss_fn: torch.nn.Module,
        device: str,
    ) -> float:
        model.train()
        running_loss = 0.0
        total_samples = 0

        for images, masks in train_loader:
            images, masks = images.to(device), masks.to(device)
            optimizer.zero_grad()
            logits = model(images)
            loss = loss_fn(logits, masks)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * len(images)
            total_samples += len(images)

        return running_loss / max(1, total_samples)

    def validate(
        self,
        model: torch.nn.Module,
        val_loader: DataLoader,
        loss_fn: torch.nn.Module,
        device: str,
    ) -> Tuple[float, float, float]:
        model.eval()
        total_loss = 0.0
        total_iou = 0.0
        total_dice = 0.0
        batches = 0

        with torch.no_grad():
            for images, masks in val_loader:
                images, masks = images.to(device), masks.to(device)
                logits = model(images)
                loss = loss_fn(logits, masks)
                total_loss += loss.item()

                iou, dice = calculate_iou_and_dice(logits, masks)
                total_iou += iou
                total_dice += dice
                batches += 1

        return (
            total_loss / max(1, batches),
            total_iou / max(1, batches),
            total_dice / max(1, batches),
        )

    def save_checkpoint(self, model: torch.nn.Module, filepath: str) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        torch.save(model.state_dict(), filepath)
        self.logger.info(f"Model checkpoint saved: {filepath}")

    def export_coreml(self, model: torch.nn.Module, filepath: str, img_size: int) -> None:
        class CoreMLWrapper(torch.nn.Module):
            def __init__(self, unet: torch.nn.Module):
                super().__init__()
                self.unet = unet

            def forward(self, x: torch.Tensor) -> torch.Tensor:
                logits = self.unet(x)
                return torch.clamp(torch.sigmoid(logits) * 255.0, 0.0, 255.0)

        wrapped_model = CoreMLWrapper(model).eval().cpu()
        example_input = torch.rand(1, 3, img_size, img_size)
        traced_model = torch.jit.trace(wrapped_model, example_input)

        mlmodel = ct.convert(
            traced_model,
            inputs=[
                ct.ImageType(
                    name="image",
                    shape=example_input.shape,
                    scale=1.0 / 127.5,
                    bias=[-1.0, -1.0, -1.0],
                    color_layout=ct.colorlayout.RGB,
                )
            ],
            outputs=[
                ct.ImageType(
                    name="mask",
                    color_layout=ct.colorlayout.GRAYSCALE,
                )
            ],
            convert_to="mlprogram",
            minimum_deployment_target=ct.target.iOS16,
        )

        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        mlmodel.save(filepath)
        self.logger.info(f"Apple CoreML model package saved successfully: {filepath}")

    def generate_validation_image(
        self,
        model: torch.nn.Module,
        val_loader: DataLoader,
        device: str,
        output_dir: str,
    ) -> str:
        model = model.to(device).eval()
        with torch.no_grad():
            images, masks = next(iter(val_loader))
            images, masks = images.to(device), masks.to(device)
            logits = model(images)
            pred_probs = torch.sigmoid(logits)

            img_tensor = images[0].cpu().numpy().transpose(1, 2, 0)
            gt_mask_tensor = masks[0, 0].cpu().numpy()
            pred_mask_tensor = pred_probs[0, 0].cpu().numpy()

        # original
        orig_img = (img_tensor * 0.5 + 0.5).clip(0, 1)
        orig_uint8 = (orig_img * 255).astype(np.uint8)

        gt_uint8 = (gt_mask_tensor * 255).astype(np.uint8)
        pred_binary = (pred_mask_tensor > 0.5).astype(np.float32)
        pred_uint8 = (pred_binary * 255).astype(np.uint8)

        # background blur effect
        orig_pil = Image.fromarray(orig_uint8)
        blurred_bg = np.array(orig_pil.filter(ImageFilter.GaussianBlur(radius=12)))
        mask_3ch = np.repeat(pred_binary[:, :, np.newaxis], 3, axis=2)
        composite = (orig_uint8 * mask_3ch + blurred_bg * (1.0 - mask_3ch)).astype(np.uint8)

        # Original, Original Mask, Predicted Mask, Background Blur
        gt_3ch = np.stack([gt_uint8] * 3, axis=-1)
        pred_3ch = np.stack([pred_uint8] * 3, axis=-1)
        comparison = np.hstack([orig_uint8, gt_3ch, pred_3ch, composite])

        os.makedirs(output_dir, exist_ok=True)
        out_path = os.path.join(output_dir, "full_training_validation_result.png")
        Image.fromarray(comparison).save(out_path)
        return out_path
