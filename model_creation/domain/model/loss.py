# Author: Chamika Deshan
# Segmentation losses and eval matrixes (Dice Loss & iou)

import numpy as np
import torch
import torch.nn as nn

# we use Dice loss for binary segmentation - it can tell how well shares are overlap, refer my notes
class DiceLoss(nn.Module):

    def __init__(self, smooth: float = 1e-6):
        super().__init__()
        self.smooth = smooth

    def forward(self, raw_mask_scores: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        # Note - dice calc here same as whats in calculate_iou_and_dice, but purpose is for training the model
        probs = torch.sigmoid(raw_mask_scores)
        probs_flat = probs.view(-1)
        targets_flat = targets.view(-1)

        intersection = (probs_flat * targets_flat).sum()

        # dice calc - tell how well 2 shapes overlap, accuracy is not good to use here, refer dice notes
        dice = (2.0 * intersection + self.smooth) / (probs_flat.sum() + targets_flat.sum() + self.smooth)
        return 1.0 - dice


# This is a hybrid Binary Cross Entropy + Dice Loss"
# Note - 2 classes so we can pick BCE
class BCEDiceLoss(nn.Module):

    def __init__(self, bce_weight: float = 0.5, dice_weight: float = 0.5):
        super().__init__()
        self.bce = nn.BCEWithLogitsLoss()
        self.dice = DiceLoss()
        self.bce_weight = bce_weight
        self.dice_weight = dice_weight

    def forward(self, raw_mask_scores: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        bce_loss = self.bce(raw_mask_scores, targets)
        dice_loss = self.dice(raw_mask_scores, targets)
        return self.bce_weight * bce_loss + self.dice_weight * dice_loss


# Intersection over union/Jaccard index and dice for validation
def calculate_iou_and_dice(
    raw_mask_scores: torch.Tensor, targets: torch.Tensor, threshold: float = 0.5
) -> tuple[float, float]:
    with torch.no_grad():
        
        pred_binary_masks = (torch.sigmoid(raw_mask_scores) > threshold).float()
        pred_binary_masks_flat = pred_binary_masks.view(-1)
        targets_flat = targets.view(-1)

        intersection = (pred_binary_masks_flat * targets_flat).sum().item()
        total_union = (pred_binary_masks_flat + targets_flat).clamp(0, 1).sum().item()

        iou = (intersection + 1e-6) / (total_union + 1e-6)
        dice = (2.0 * intersection + 1e-6) / (pred_binary_masks_flat.sum().item() + targets_flat.sum().item() + 1e-6)

        return iou, dice


# same as above, but it taked binary pred_mask and numpy array, for grab cut need this``
def calculate_binary_mask_iou_and_dice(
    pred_mask: np.ndarray, gt_mask: np.ndarray, threshold: float = 0.5
) -> tuple[float, float]:
    """Calculates IoU and Dice between numpy binary/probabilistic masks."""
    pred_bin = (pred_mask > threshold).astype(np.float32)
    gt_bin = (gt_mask > threshold).astype(np.float32)

    intersection = np.sum(pred_bin * gt_bin)
    union = np.sum(pred_bin) + np.sum(gt_bin) - intersection
    total_area = np.sum(pred_bin) + np.sum(gt_bin)

    iou = (intersection + 1e-6) / (union + 1e-6)
    dice = (2.0 * intersection + 1e-6) / (total_area + 1e-6)
    return float(iou), float(dice)
