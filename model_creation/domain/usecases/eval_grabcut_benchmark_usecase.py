# Author: Chamika Deshan
# GrabCut Benchmark vs Deep Learning U-Net Use Case

import os
from typing import Dict, Any, Optional
import numpy as np
import torch

from core.util.logger import ILogger
from domain.manager.isegmentation_loader import ISegmentationLoader
from domain.manager.ibenchmark_manager import IBenchmarkManager
from domain.model.model_factory import build_segmentation_model

# Be3nchmark Grabcut vs U-Net model from config/benchmark/.env
class EvalGrabcutBenchmarkUseCase:
    
    def __init__(
        self,
        data_loader: ISegmentationLoader,
        benchmark_manager: IBenchmarkManager,
        logger: Optional[ILogger] = None,
    ):
        self.data_loader = data_loader
        self.benchmark_manager = benchmark_manager
        self.logger = logger

    def execute(
        self,
        checkpoint_path: str,
        model_type: str = "mobilenetv1",
        width: float = 1.0,
        img_size: int = 224,
        device: str = "mps",
        num_samples: int = 50,
        output_dir: str = "model_creation/output/gen_images",
    ) -> Dict[str, Any]:
        msg = f"Benchmark: GrabCut vs U-Net ({model_type.upper()}, W={width})"
        self.logger.info(msg)

        # 1 get data
        test_loader = self.data_loader.get_test_loader(
            img_size=img_size,
            batch_size=1,
            max_test_samples=num_samples,
        )

        # 2 Extract RGB images and ground truth masks
        images_np = []
        masks_np = []
        for img_tensor, mask_tensor in test_loader:
            img_rgb = ((img_tensor * 0.5 + 0.5).clamp(0, 1).squeeze().permute(1, 2, 0).cpu().numpy() * 255).astype(np.uint8)
            gt_mask = mask_tensor.squeeze().cpu().numpy()
            images_np.append(img_rgb)
            masks_np.append(gt_mask)

        # 3 Run Grabcut
        gc_msg = f"Running GrabCut benchmark on {len(images_np)} images"
        self.logger.info(gc_msg)
        gc_res = self.benchmark_manager.benchmark_grabcut(images_np, masks_np)

        # 4 Benchmark U-Net Model
        load_msg = f"Loading model {model_type} (W={width}) from: {checkpoint_path}"
        self.logger.info(load_msg)

        unet_model = build_segmentation_model(model_type, width=width, pretrained=False).to(device)
        state_dict = torch.load(checkpoint_path, map_location=device, weights_only=True)
        unet_model.load_state_dict(state_dict)

        unet_res = self.benchmark_manager.benchmark_unet(
            model=unet_model,
            test_loader=test_loader,
            device=device,
        )

        # 5 visual comparison
        vis_samples = []
        num_vis = min(4, len(images_np))
        for idx in range(num_vis):
            img_np = images_np[idx]
            gt = masks_np[idx]
            gc_p = gc_res["predictions"][idx]
            gc_i = gc_res["ious"][idx]
            un_p = unet_res["predictions"][idx] if unet_res else None
            un_i = unet_res["ious"][idx] if unet_res else 0.0
            vis_samples.append((img_np, gt, gc_p, un_p, gc_i, un_i))

        save_path = os.path.join(output_dir, "grabcut_vs_unet_comparison.png")
        self.benchmark_manager.visualize_comparison(vis_samples, save_path)

        # 6 Summary
        summary = (
            "\n"
            + f"{'Method':<30} | {'Mean IoU':<10} | {'Mean Dice':<10}\n"
            + f"{'GrabCut (Iter=5)':<30} | {gc_res['mean_iou'] * 100:>8.2f}% | {gc_res['mean_dice'] * 100:>8.2f}%\n"
        )
        label = f"U-Net ({model_type.upper()} W={width})"
        summary += (
            f"{label:<30} | {unet_res['mean_iou'] * 100:>8.2f}% | {unet_res['mean_dice'] * 100:>8.2f}%\n"
        )

        self.logger.info(summary)

        return {
            "grabcut": gc_res,
            "unet": unet_res,
            "comparison_image": save_path,
        }
