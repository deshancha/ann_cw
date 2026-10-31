# Author: Chamika Deshan
# Model Creation Implementation

import os
from typing import Tuple
import numpy as np
from PIL import Image, ImageFilter
import torch
from torch.utils.data import DataLoader

from core.util.logger import ILogger
from domain.manager.imodel_creation import IModelCreation
from domain.model.loss import calculate_iou_and_dice

import onnx2tf
import onnx2tf.onnx2tf as otf
import onnx2tf.utils.common_functions as cf
import coremltools as ct
import glob
import shutil

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
            raw_mask_scores = model(images)
            loss = loss_fn(raw_mask_scores, masks)
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
                raw_mask_scores = model(images)
                loss = loss_fn(raw_mask_scores, masks)
                total_loss += loss.item()

                iou, dice = calculate_iou_and_dice(raw_mask_scores, masks)
                total_iou += iou
                total_dice += dice
                batches += 1

        return (
            total_loss / max(1, batches),
            total_iou / max(1, batches),
            total_dice / max(1, batches),
        )

    def save_checkpoint(self, model: torch.nn.Module, filepath: str) -> None:
        torch.save(model.state_dict(), filepath)
        self.logger.info(f"Model checkpoint saved: {filepath}")

    def export_coreml(self, model: torch.nn.Module, filepath: str, img_size: int) -> None:
        class CoreMLWrapper(torch.nn.Module):
            def __init__(self, unet: torch.nn.Module):
                super().__init__()
                self.unet = unet

            def forward(self, x: torch.Tensor) -> torch.Tensor:
                raw_mask_scores = self.unet(x)
                return torch.clamp(torch.sigmoid(raw_mask_scores) * 255.0, 0.0, 255.0)

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

        mlmodel.save(filepath)
        self.logger.info(f"Apple CoreML model saved: {filepath}")

    def export_tflite(
        self,
        model: torch.nn.Module,
        filepath: str,
        img_size: int = 256,
        in_nhwc: bool = True,
    ) -> None:
        class TFLiteWrapper(torch.nn.Module):
            def __init__(self, unet: torch.nn.Module):
                super().__init__()
                self.unet = unet

            def forward(self, x: torch.Tensor) -> torch.Tensor:
                # C++ ISegmentProcessTFL  NHWC [1, H, W, 3] in [0.0, 1.0]
                x = x.permute(0, 3, 1, 2)  # NHWC -> NCHW
                x = x * 2.0 - 1.0  # [0, 1] -> [-1, 1] MobileNet normalization
                raw_mask_scores = self.unet(x)
                probs = torch.sigmoid(raw_mask_scores)
                probs = probs.permute(0, 2, 3, 1)  # NCHW -> NHWC [1, H, W, 1]
                return probs

        wrapped_model = TFLiteWrapper(model).eval().cpu()
        dummy_input = torch.rand(1, img_size, img_size, 3)

        # 1 Export temporary ONNX
        temp_dir = os.path.join(os.path.dirname(os.path.abspath(filepath)), "_tflite_temp")
        os.makedirs(temp_dir, exist_ok=True)
        temp_onnx = os.path.join(temp_dir, "model.onnx")

        torch.onnx.export(
            wrapped_model,
            dummy_input,
            temp_onnx,
            input_names=["input_image"],
            output_names=["output_mask"],
            opset_version=13,
        )

        # 2 Patch onnx2tf dummy test image and convert
        mock_fn = lambda: np.zeros((img_size, img_size, 3), dtype=np.float32)
        otf.download_test_image_data = mock_fn
        cf.download_test_image_data = mock_fn

        onnx2tf_out = os.path.join(temp_dir, "onnx2tf_out")
        onnx2tf.convert(
            input_onnx_file_path=temp_onnx,
            output_folder_path=onnx2tf_out,
            keep_shape_absolutely_input_names=["input_image"],
            non_verbose=True,
        )

        # 3 Locate converted float32 tflite file and copy to target
        tflite_candidates = glob.glob(os.path.join(onnx2tf_out, "*_float32.tflite"))
        if not tflite_candidates:
            tflite_candidates = glob.glob(os.path.join(onnx2tf_out, "*.tflite"))

        assert tflite_candidates, f"No .tflite files found in {onnx2tf_out}"
        generated_tflite = tflite_candidates[0]

        shutil.copyfile(generated_tflite, filepath)

        # Cleanup temporary conversion artifacts
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

        self.logger.info(f"TFLite model successfully exported and saved: {filepath}")

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
            raw_mask_scores = model(images)
            pred_probs = torch.sigmoid(raw_mask_scores)

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

        out_path = os.path.join(output_dir, "full_training_validation_result.png")
        Image.fromarray(comparison).save(out_path)
        return out_path
