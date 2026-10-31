# Author: Chamika Deshan
# Explainable AI (XAI) Imp

import os
from typing import Dict, Any, Tuple, List, Optional
import numpy as np
from PIL import Image, ImageDraw
import cv2
import torch
import torch.nn as nn

from core.util.logger import ILogger
from domain.manager.iexplainable_ai import IExplainableAI
from domain.model.loss import calculate_binary_mask_iou_and_dice

# Grad- Cam Imp
class ExplainableAIImp(IExplainableAI):

    def __init__(self, logger: ILogger):
        self.logger = logger
        self.activations: List[torch.Tensor] = []
        self.gradients: List[torch.Tensor] = []

    # From Unet we only need mobilenet part which is the feature extraction and we need final layer which best extracted the feature
    def _get_mobilenet_feature_layer(self, model: nn.Module) -> Tuple[nn.Module, str]:
        return model.encoder.blocks[-1], "encoder.blocks[-1] (MobileNet Feature Bottleneck)"

    # Hooks are registered becasue Pytorch not store intermediate activations and gradients
    # But Grad Cam needs this
    def _register_hooks(self, target_layer: nn.Module):
        self.activations.clear()
        self.gradients.clear()
        # Forward Hook: What features did this layer detect
        f_h = target_layer.register_forward_hook(lambda m, i, o: self.activations.append(o))
        # Backward Hook: How important was each feature to the output
        b_h = target_layer.register_full_backward_hook(lambda m, gi, go: self.gradients.append(go[0]))
        return f_h, b_h

    def _compute_gradcam(
        self, model: nn.Module, input_tensor: torch.Tensor, device: str
    ) -> Tuple[np.ndarray, np.ndarray, float]:
        model.zero_grad()
        self.activations.clear()
        self.gradients.clear()

        x = input_tensor.to(device).requires_grad_(True)
        probs = torch.sigmoid(model(x))
        score = probs.sum()
        score.backward(retain_graph=True)

        weights = torch.mean(self.gradients[-1], dim=(2, 3), keepdim=True)
        cam = torch.relu(torch.sum(weights * self.activations[-1], dim=1, keepdim=True))
        cam_min, cam_max = cam.min(), cam.max()
        cam = (cam - cam_min) / (cam_max - cam_min + 1e-8) if cam_max > cam_min else torch.zeros_like(cam)

        return cam.squeeze().detach().cpu().numpy(), probs.squeeze().detach().cpu().numpy(), float(score.item())

    def _create_heatmap_overlay(self, orig_rgb: np.ndarray, cam: np.ndarray, alpha: float = 0.5) -> np.ndarray:
        h, w = orig_rgb.shape[:2]
        cam_u8 = np.uint8(255.0 * cv2.resize(cam, (w, h), interpolation=cv2.INTER_LINEAR))
        heat_rgb = cv2.cvtColor(cv2.applyColorMap(cam_u8, cv2.COLORMAP_JET), cv2.COLOR_BGR2RGB)
        return (alpha * orig_rgb + (1.0 - alpha) * heat_rgb).astype(np.uint8)

    # Image creation, no need to look into
    def _render_composite_panel(
        self,
        image: np.ndarray,
        ground_truth: np.ndarray,
        prediction: np.ndarray,
        heatmap: np.ndarray,
        title: str,
    ) -> Image.Image:
        h, w = image.shape[:2]
        ground_truth_3ch = np.stack([ground_truth] * 3, axis=-1)
        prediction_3ch = np.stack([prediction] * 3, axis=-1)
        row = np.hstack([image, ground_truth_3ch, prediction_3ch, heatmap])

        canvas = Image.new("RGB", (row.shape[1], row.shape[0] + 40), color=(24, 26, 32))
        canvas.paste(Image.fromarray(row), (0, 40))

        draw = ImageDraw.Draw(canvas)
        draw.text((15, 12), title, fill=(255, 255, 255))
        return canvas

    # IMPORTANT: Watched https://www.youtube.com/watch?v=_QiebC9WxOc
    def _explain_prediction(
        self,
        model: torch.nn.Module,
        img_tensor: torch.Tensor,
        image_u8: np.ndarray,
        ground_truth_u8: np.ndarray,
        device: str,
        title: str,
    ) -> Tuple[Image.Image, Dict[str, Any]]:
        feature_layer, layer_name = self._get_mobilenet_feature_layer(model)
        self.logger.info(f"Grad-CAM hooked into feature layer: {layer_name}")
        f_h, b_h = self._register_hooks(feature_layer)

        cam, pred_mask, score = self._compute_gradcam(model, img_tensor, device)

        # relese hooked memeory
        f_h.remove()
        b_h.remove()

        prediction_u8 = ((pred_mask > 0.5) * 255).astype(np.uint8)
        iou, dice = calculate_binary_mask_iou_and_dice(pred_mask, (ground_truth_u8 > 127).astype(np.float32))
        overlay = self._create_heatmap_overlay(image_u8, cam)
        full_title = f"{title}, IoU: {iou}, dice: {dice}, score: {score}"
        panel = self._render_composite_panel(image_u8, ground_truth_u8, prediction_u8, overlay, full_title)

        return panel, {
            "iou": iou,
            "dice": dice,
            "foreground_score": score,
            "pred_mask": pred_mask,
            "cam": cam,
        }


    # Just a helper to open from files
    def explain_from_paths(
        self,
        model: torch.nn.Module,
        image_path: str,
        ground_truth_path: str,
        device: str,
        img_size: int = 224,
        title: str = "",
    ) -> Tuple[Image.Image, Dict[str, Any]]:
        with Image.open(image_path) as raw_image:
            rgb_image = raw_image.convert("RGB").resize((img_size, img_size), Image.BILINEAR)
            image_u8 = np.array(rgb_image)

        # Convert to tensor [-1.0, 1.0] for model forward pass
        img_tensor = torch.from_numpy(image_u8).float().permute(2, 0, 1) / 255.0
        img_tensor = ((img_tensor - 0.5) / 0.5).unsqueeze(0)

        # Ground truth mask
        with Image.open(ground_truth_path) as raw_mask:
            grayscale_mask = raw_mask.convert("L").resize((img_size, img_size), Image.NEAREST)
            ground_truth_u8 = (np.array(grayscale_mask) > 127).astype(np.uint8) * 255

        panel, info = self._explain_prediction(
            model=model,
            img_tensor=img_tensor,
            image_u8=image_u8,
            ground_truth_u8=ground_truth_u8,
            device=device,
            title=title,
        )
        info["image_path"] = image_path
        info["ground_truth_path"] = ground_truth_path
        return panel, info


    # Just a helper to save the image
    def save_compare_img(self, panels: List[Image.Image], output_path: str) -> str:
        gallery_h = sum(p.height for p in panels) + 10 * (len(panels) - 1)
        gallery_w = max(p.width for p in panels)
        gallery = Image.new("RGB", (gallery_w, gallery_h), color=(15, 17, 21))

        y_offset = 0
        for p in panels:
            gallery.paste(p, (0, y_offset))
            y_offset += p.height + 10

        gallery.save(output_path)
        self.logger.info(f"Result at: {output_path}")
        return output_path
