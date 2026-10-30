# Author: Chamika Deshan
# Model Test Implementation

import os
from typing import Tuple, Dict, Any
import numpy as np
from PIL import Image
import torch
from torch.utils.data import DataLoader

from core.util.logger import ILogger
from domain.manager.imodel_test import IModelTest
from domain.model.loss import calculate_iou_and_dice


# Test Dataset Eval
class ModelTestImp(IModelTest):

    def __init__(self, logger: ILogger):
        self.logger = logger

    def evaluate(
        self,
        model: torch.nn.Module,
        test_loader: DataLoader,
        device: str,
        output_dir: str = "",
    ) -> Tuple[float, float, Dict[str, Any]]:
        model.eval()

        total_iou = 0.0
        total_dice = 0.0
        batches = 0

        idx = 0
        best_idx = 0
        worst_idx = 0
        max_iou = -1.0
        min_iou = 2.0
        best_sample = None
        worst_sample = None

        with torch.no_grad():
            for images, masks in test_loader:
                images, masks = images.to(device), masks.to(device)
                raw_mask_scores = model(images)

                iou, dice = calculate_iou_and_dice(raw_mask_scores, masks)
                total_iou += iou
                total_dice += dice
                batches += 1

                # Track min and max IoU directly with batch index
                if iou > max_iou:
                    max_iou = iou
                    best_idx = idx
                    orig_np = ((images[0].cpu().numpy().transpose(1, 2, 0) * 0.5 + 0.5).clip(0, 1) * 255).astype(np.uint8)
                    pred_np = ((torch.sigmoid(raw_mask_scores[0, 0]) > 0.5).float().cpu().numpy() * 255).astype(np.uint8)
                    best_sample = (orig_np, pred_np)

                if iou < min_iou:
                    min_iou = iou
                    worst_idx = idx
                    orig_np = ((images[0].cpu().numpy().transpose(1, 2, 0) * 0.5 + 0.5).clip(0, 1) * 255).astype(np.uint8)
                    pred_np = ((torch.sigmoid(raw_mask_scores[0, 0]) > 0.5).float().cpu().numpy() * 255).astype(np.uint8)
                    worst_sample = (orig_np, pred_np)

                idx += 1

        avg_iou = total_iou / max(1, batches)
        avg_dice = total_dice / max(1, batches)

        self.logger.info(
            f"Test Result: "
            f"Mean IoU={avg_iou:.4f} ({avg_iou*100:.2f}%), "
            f"Dice={avg_dice:.4f} ({avg_dice*100:.2f}%) "
            f"across {batches} batches"
        )

        extremes_dict: Dict[str, Any] = {
            "best": {
                "index": best_idx,
                "iou": float(max_iou),
                "orig_path": "",
                "pred_path": "",
            },
            "worst": {
                "index": worst_idx,
                "iou": float(min_iou),
                "orig_path": "",
                "pred_path": "",
            },
        }

        # save best and worst (original + predicted mask)
        if output_dir and best_sample is not None and worst_sample is not None:
            os.makedirs(output_dir, exist_ok=True)

            best_orig, best_pred = best_sample
            best_orig_path = os.path.join(output_dir, f"test_best_orig_{best_idx}.png")
            best_pred_path = os.path.join(output_dir, f"test_best_pred_{best_idx}.png")
            Image.fromarray(best_orig).save(best_orig_path)
            Image.fromarray(best_pred).save(best_pred_path)
            extremes_dict["best"]["orig_path"] = best_orig_path
            extremes_dict["best"]["pred_path"] = best_pred_path

            worst_orig, worst_pred = worst_sample
            worst_orig_path = os.path.join(output_dir, f"test_worst_orig_{worst_idx}.png")
            worst_pred_path = os.path.join(output_dir, f"test_worst_pred_{worst_idx}.png")
            Image.fromarray(worst_orig).save(worst_orig_path)
            Image.fromarray(worst_pred).save(worst_pred_path)
            extremes_dict["worst"]["orig_path"] = worst_orig_path
            extremes_dict["worst"]["pred_path"] = worst_pred_path

        return float(avg_iou), float(avg_dice), extremes_dict
