# Author: Chamika Deshan
# MobileSAM Implementation

import os
import time
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import cv2
from PIL import Image
import torch

from core.util.logger import ILogger
from domain.manager.ifoundation_model_manager import IFoundationModelManager
from domain.model.loss import calculate_binary_mask_iou_and_dice
from mobile_sam import sam_model_registry, SamPredictor

class FoundationModelManagerImp(IFoundationModelManager):
    def __init__(self, logger: ILogger):
        self.logger = logger

    def benchmark_mobilesam(
        self,
        images_np: List[np.ndarray],
        masks_np: List[np.ndarray],
        checkpoint_path: str,
        device: str = "cpu",
        box_margin: float = 0.05,
    ) -> Dict[str, Any]:
        self.logger.info(f"Loading MobileSAM : {checkpoint_path}")

        sam = sam_model_registry["vit_t"](checkpoint=checkpoint_path)
        # this need handle MPS Metal indexing issues
        sam.eval()
        target_device = "mps" if (device == "mps" and torch.backends.mps.is_available()) else device
        sam.to(device=target_device)
        predictor = SamPredictor(sam)

        ious: List[float] = []
        dices: List[float] = []
        latencies_ms: List[float] = []
        predictions: List[np.ndarray] = []

        total = len(images_np)
        self.logger.info(f"MobileSAM: {total} images, {target_device.upper()} (Margin={box_margin*100:.0f}%)")

        # shader compilation trigger
        if total > 0 and target_device == "mps":
            predictor.set_image(images_np[0])
            _ = predictor.predict(box=np.array([[10, 10, 200, 200]]), multimask_output=False)
            torch.mps.synchronize()

        for idx, (img_rgb, gt_mask) in enumerate(zip(images_np, masks_np)):
            h, w = img_rgb.shape[:2]
            margin_x = int(w * box_margin)
            margin_y = int(h * box_margin)
            box_prompt = np.array([margin_x, margin_y, w - margin_x, h - margin_y])

            # Latency (encoding + prompt decoding)
            if target_device == "mps":
                torch.mps.synchronize()
            t0 = time.perf_counter()
            predictor.set_image(img_rgb)
            masks, scores, _ = predictor.predict(
                box=box_prompt[None, :],
                multimask_output=False,
            )
            if target_device == "mps":
                torch.mps.synchronize()
            lat_ms = (time.perf_counter() - t0) * 1000.0

            pred_mask = masks[0].astype(np.float32)
            iou, dice = calculate_binary_mask_iou_and_dice(pred_mask, gt_mask)

            ious.append(iou)
            dices.append(dice)
            latencies_ms.append(lat_ms)
            predictions.append(pred_mask)

        param_count = sum(p.numel() for p in sam.parameters())
        file_size_mb = os.path.getsize(checkpoint_path) / (1024 * 1024)

        return {
            "mean_iou": float(np.mean(ious)) if ious else 0.0,
            "min_iou": float(np.min(ious)) if ious else 0.0,
            "max_iou": float(np.max(ious)) if ious else 0.0,
            "mean_dice": float(np.mean(dices)) if dices else 0.0,
            "mean_latency_ms": float(np.mean(latencies_ms)) if latencies_ms else 0.0,
            "fps": float(1000.0 / np.mean(latencies_ms)) if latencies_ms and np.mean(latencies_ms) > 0 else 0.0,
            "param_count_m": float(param_count / 1e6),
            "file_size_mb": float(file_size_mb),
            "ious": ious,
            "dices": dices,
            "latencies_ms": latencies_ms,
            "predictions": predictions,
        }

    def visualize_foundation_comparison(self, samples: List[Any], output_path: str) -> None:
        rows = []
        for img, gt, unet, msam, u_iou, m_iou, label in samples:
            gt_rgb = np.repeat((gt * 255).astype(np.uint8)[:, :, None], 3, axis=2)
            u_rgb = np.repeat((unet * 255).astype(np.uint8)[:, :, None], 3, axis=2)
            m_rgb = np.repeat((msam * 255).astype(np.uint8)[:, :, None], 3, axis=2)

            img_draw = img.copy()
            cv2.putText(img_draw, label, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(u_rgb, f"IoU: {u_iou * 100:.1f}%", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.putText(m_rgb, f"IoU: {m_iou * 100:.1f}%", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

            rows.append(np.hstack([img_draw, gt_rgb, u_rgb, m_rgb]))

        if rows:
            Image.fromarray(np.vstack(rows)).save(output_path)
