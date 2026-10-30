# Author: Chamika Deshan
# Benchmark Manager Implementation (OpenCV vs UNet)

import os
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import cv2
from PIL import Image
import torch

from core.util.logger import ILogger
from domain.manager.ibenchmark_manager import IBenchmarkManager
from domain.model.loss import calculate_binary_mask_iou_and_dice

# Benchmark Grabcut vs Unet
class BenchmarkManagerImp(IBenchmarkManager):
    
    def __init__(self, logger: Optional[ILogger] = None):
        self.logger = logger

    # private opencv grabcut executer
    def _run_grabcut(self, img_rgb: np.ndarray) -> np.ndarray:
        h, w = img_rgb.shape[:2]
        margin_x = int(w * 0.05)
        margin_y = int(h * 0.05)
        rect = (margin_x, margin_y, w - 2 * margin_x, h - 2 * margin_y)

        mask = np.zeros((h, w), np.uint8)
        bgd_model = np.zeros((1, 65), np.float64)
        fgd_model = np.zeros((1, 65), np.float64)

        img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
        cv2.grabCut(img_bgr, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)

        # GC_FGD = 1 and GC_PR_FGD = 3 -> definite and probable foreground
        binary_mask = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 1.0, 0.0).astype(np.float32)
        return binary_mask

    def benchmark_grabcut(
        self, images_np: List[np.ndarray], masks_np: List[np.ndarray]
    ) -> Dict[str, Any]:
        ious = []
        dices = []
        predictions = []

        total = len(images_np)
        for idx, (img_np, gt_mask) in enumerate(zip(images_np, masks_np)):
            gc_pred = self._run_grabcut(img_np)
            iou, dice = calculate_binary_mask_iou_and_dice(gc_pred, gt_mask)

            ious.append(iou)
            dices.append(dice)
            predictions.append(gc_pred)

            if (idx + 1) % 10 == 0 or (idx + 1) == total:
                self.logger.info(f"GrabCut - {idx + 1}/{total} samples - Mean IoU : {np.mean(ious) * 100:.2f}%")

        return {
            "mean_iou": float(np.mean(ious)) if ious else 0.0,
            "mean_dice": float(np.mean(dices)) if dices else 0.0,
            "ious": ious,
            "dices": dices,
            "predictions": predictions,
        }

    def benchmark_unet(
        self,
        model: torch.nn.Module,
        test_loader: Any,
        device: str,
    ) -> Dict[str, Any]:
        model.eval()
        model.to(device)

        ious = []
        dices = []
        predictions = []

        total = len(test_loader)
        for idx, (img_tensor, mask_tensor) in enumerate(test_loader):
            img_tensor = img_tensor.to(device)

            with torch.no_grad():
                raw_mask_scores = model(img_tensor)
                probs = torch.sigmoid(raw_mask_scores)

            unet_pred = probs.squeeze().cpu().numpy()
            gt_mask = mask_tensor.squeeze().cpu().numpy()
            iou, dice = calculate_binary_mask_iou_and_dice(unet_pred, gt_mask)

            ious.append(iou)
            dices.append(dice)
            predictions.append(unet_pred)

            if (idx + 1) % 10 == 0 or (idx + 1) == total:
                self.logger.info(f"U-Net - {idx + 1}/{total} samples - Mean IoU : {np.mean(ious) * 100:.2f}%")

        return {
            "mean_iou": float(np.mean(ious)) if ious else 0.0,
            "mean_dice": float(np.mean(dices)) if dices else 0.0,
            "ious": ious,
            "dices": dices,
            "predictions": predictions,
        }

    def visualize_comparison(
        self,
        samples: List[Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, float, float]],
        output_path: str,
    ) -> None:
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        row_imgs = []

        for img_np, gt, gc, un, gc_i, un_i in samples:
            gt_rgb = np.repeat((gt * 255).astype(np.uint8)[:, :, np.newaxis], 3, axis=2)
            gc_rgb = np.repeat((gc * 255).astype(np.uint8)[:, :, np.newaxis], 3, axis=2)
            if un is not None:
                un_rgb = np.repeat((un * 255).astype(np.uint8)[:, :, np.newaxis], 3, axis=2)
                row = np.hstack([img_np, gt_rgb, gc_rgb, un_rgb])
            else:
                row = np.hstack([img_np, gt_rgb, gc_rgb])
            row_imgs.append(row)

        combined = np.vstack(row_imgs)
        Image.fromarray(combined).save(output_path)
        self.logger.info(f"Visual comparison saved to: {output_path}")
