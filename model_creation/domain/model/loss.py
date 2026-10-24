# Author: Chamika Deshan
# Segmentation losses and eval matrixes (Dice Loss & iou)

import torch
import torch.nn as nn

class DiceLoss(nn.Module):
    """Dice Loss for binary segmentation."""

    def __init__(self, smooth: float = 1e-6):
        super().__init__()
        self.smooth = smooth

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        probs = torch.sigmoid(logits)
        probs_flat = probs.view(-1)
        targets_flat = targets.view(-1)

        intersection = (probs_flat * targets_flat).sum()
        dice = (2.0 * intersection + self.smooth) / (probs_flat.sum() + targets_flat.sum() + self.smooth)
        return 1.0 - dice


class BCEDiceLoss(nn.Module):
    """Binary Cross Entropy + Logits and Dice Loss"""

    def __init__(self, bce_weight: float = 0.5, dice_weight: float = 0.5):
        super().__init__()
        self.bce = nn.BCEWithLogitsLoss()
        self.dice = DiceLoss()
        self.bce_weight = bce_weight
        self.dice_weight = dice_weight

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        bce_loss = self.bce(logits, targets)
        dice_loss = self.dice(logits, targets)
        return self.bce_weight * bce_loss + self.dice_weight * dice_loss


# Intersection over union/Jaccard index part
def calculate_iou_and_dice(
    logits: torch.Tensor, targets: torch.Tensor, threshold: float = 0.5
) -> tuple[float, float]:
    """Calculates batch mean IoU and Dice score"""
    with torch.no_grad():
        preds = (torch.sigmoid(logits) > threshold).float()
        preds_flat = preds.view(-1)
        targets_flat = targets.view(-1)

        intersection = (preds_flat * targets_flat).sum().item()
        total_union = (preds_flat + targets_flat).clamp(0, 1).sum().item()

        iou = (intersection + 1e-6) / (total_union + 1e-6)
        dice = (2.0 * intersection + 1e-6) / (preds_flat.sum().item() + targets_flat.sum().item() + 1e-6)

        return iou, dice
