# Author: Chamika Deshan
# Foundation Model Benchmark Use Case

import os
import json
from typing import Dict, Any, List, Tuple
import numpy as np
import torch

from core.util.logger import ILogger
from domain.manager.isegmentation_loader import ISegmentationLoader
from domain.manager.ibenchmark_manager import IBenchmarkManager
from domain.manager.ifoundation_model_manager import IFoundationModelManager
from domain.model.model_factory import build_segmentation_model

# Unet vs MobileSAM eval
class EvalFoundationBenchmarkUseCase:
    def __init__(
        self,
        data_loader: ISegmentationLoader,
        benchmark_manager: IBenchmarkManager,
        foundation_manager: IFoundationModelManager,
        logger: ILogger,
    ):
        self.data_loader = data_loader
        self.benchmark_manager = benchmark_manager
        self.foundation_manager = foundation_manager
        self.logger = logger

    def execute(
        self,
        unet_checkpoint_path: str,
        mobilesam_checkpoint_path: str,
        model_type: str = "mobilenetv3",
        width: float = 1.0,
        img_size: int = 224,
        device: str = "mps",
        num_samples: int = 50,
        box_margin: float = 0.05,
        output_dir: str = "model_creation/output/foundation",
    ) -> Dict[str, Any]:

        # Load test data set
        test_loader = self.data_loader.get_test_loader(
            img_size=img_size, batch_size=1, max_test_samples=num_samples
        )
        images_np, masks_np = self._extract_test_data(test_loader)
        n_samples = len(images_np)

        # 2. Benchmark Custom U-Net via existing BenchmarkManager
        self.logger.info(f"Benchmarking UNET ({model_type})")
        target_device = "mps" if (device == "mps" and torch.backends.mps.is_available()) else device
        unet_model = build_segmentation_model(model_type, width=width, pretrained=False).to(target_device)
        unet_model.load_state_dict(torch.load(unet_checkpoint_path, map_location=target_device, weights_only=True))

        unet_res = self.benchmark_manager.benchmark_unet(
            model=unet_model,
            test_loader=test_loader,
            device=target_device,
        )
        unet_res["file_size_mb"] = os.path.getsize(unet_checkpoint_path) / (1024 * 1024) if os.path.isfile(unet_checkpoint_path) else 0.0

        # Benchmark MobileSAM
        self.logger.info(f"Benchmarking MobileSAM")
        msam_res = self.foundation_manager.benchmark_mobilesam(
            images_np, masks_np, mobilesam_checkpoint_path, device, box_margin
        )

        # Save Visual Comparison Gallery
        vis_samples = [
            (images_np[i], masks_np[i], unet_res["predictions"][i], msam_res["predictions"][i], unet_res["ious"][i], msam_res["ious"][i])
            for i in range(min(6, n_samples))
        ]
        vis_path = os.path.join(output_dir, "foundation_vs_unet_comparison.png")
        self.foundation_manager.visualize_foundation_comparison(vis_samples, vis_path)
        self.logger.info(f"Visual gallery saved to: {vis_path}")

        # 5. Compile, Save JSON & Log Summary
        return self._save_and_log_results(
            output_dir, n_samples, device, box_margin, unet_res, msam_res,
            unet_checkpoint_path, mobilesam_checkpoint_path, model_type
        )

    def _extract_test_data(self, test_loader) -> Tuple[List[np.ndarray], List[np.ndarray]]:
        images_np, masks_np = [], []
        for img_tensor, mask_tensor in test_loader:
            img_rgb = ((img_tensor * 0.5 + 0.5).clamp(0, 1).squeeze().permute(1, 2, 0).cpu().numpy() * 255).astype(np.uint8)
            images_np.append(img_rgb)
            masks_np.append(mask_tensor.squeeze().cpu().numpy())
        return images_np, masks_np

    def _save_and_log_results(
        self, output_dir: str, n_samples: int, device: str, box_margin: float,
        unet_res: Dict[str, Any], msam_res: Dict[str, Any],
        unet_path: str, msam_path: str, model_type: str
    ) -> Dict[str, Any]:
        results = {
            "evaluation_samples": n_samples,
            "device": device,
            "prompt_protocol": f"Bounding box [margin={box_margin*100:.0f}%]",
            "custom_unet": {
                "architecture": f"U-Net {model_type}",
                "weights": unet_path,
                "parameters_m": unet_res["param_count_m"],
                "file_size_mb": unet_res["file_size_mb"],
                "mean_iou": unet_res["mean_iou"],
                "min_iou": unet_res["min_iou"],
                "max_iou": unet_res["max_iou"],
                "mean_dice": unet_res["mean_dice"],
                "mean_latency_ms": unet_res["mean_latency_ms"],
                "fps": unet_res["fps"],
            },
            "foundation_mobilesam": {
                "architecture": "MobileSAM (TinyViT distilled from SAM ViT-H)",
                "weights": msam_path,
                "parameters_m": msam_res["param_count_m"],
                "file_size_mb": msam_res["file_size_mb"],
                "mean_iou": msam_res["mean_iou"],
                "min_iou": msam_res["min_iou"],
                "max_iou": msam_res["max_iou"],
                "mean_dice": msam_res["mean_dice"],
                "mean_latency_ms": msam_res["mean_latency_ms"],
                "fps": msam_res["fps"],
            },
            "comparative_deltas": {
                "iou_delta": float(msam_res["mean_iou"] - unet_res["mean_iou"]),
                "safety_floor_min_iou_delta": float(msam_res["min_iou"] - unet_res["min_iou"]),
                "latency_slowdown_factor": float(msam_res["mean_latency_ms"] / max(unet_res["mean_latency_ms"], 1e-4)),
                "parameter_ratio": float(msam_res["param_count_m"] / max(unet_res["param_count_m"], 1e-4)),
            },
        }

        json_path = os.path.join(output_dir, "foundation_benchmark.json")
        with open(json_path, "w") as f:
            json.dump(results, f, indent=4)
        self.logger.info(f"Benchmark JSON saved to: {json_path}")

        return results
