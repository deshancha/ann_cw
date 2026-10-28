# Author: Chamika Deshan
# Model Test Implementation

import os
import time
from typing import Tuple, Dict, Any, List
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
    ) -> Tuple[float, float]:
        model.eval()

        total_iou = 0.0
        total_dice = 0.0
        batches = 0

        with torch.no_grad():
            for images, masks in test_loader:
                images, masks = images.to(device), masks.to(device)
                logits = model(images)

                iou, dice = calculate_iou_and_dice(logits, masks)
                total_iou += iou
                total_dice += dice
                batches += 1

        avg_iou = total_iou / max(1, batches)
        avg_dice = total_dice / max(1, batches)

        self.logger.info(
            f"Test Result: "
            f"Mean IoU={avg_iou:.4f} ({avg_iou*100:.2f}%), "
            f"Dice={avg_dice:.4f} ({avg_dice*100:.2f}%) "
            f"across {batches} batches"
        )
        return float(avg_iou), float(avg_dice)
