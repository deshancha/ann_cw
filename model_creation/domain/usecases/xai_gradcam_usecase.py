# Author: Chamika Deshan
# Explainable AI (XAI) - Segmentation Grad-CAM Use Case

import os
import json
from typing import Dict, Any, Optional
import torch

from core.util.logger import ILogger
from domain.manager.iexplainable_ai import IExplainableAI
from domain.model.model_factory import build_segmentation_model

# Explaianale AI
class XAIGradCamUseCase:
    def __init__(
        self,
        explainable_ai: IExplainableAI,
        logger: ILogger,
    ):
        self.explainable_ai = explainable_ai
        self.logger = logger

    def execute(
        self,
        checkpoint_path: str,
        best_orig_path: str,
        worst_orig_path: str,
        best_gt_path: str,
        worst_gt_path: str,
        model_type: str = "mobilenetv1",
        width: float = 1.0,
        img_size: int = 224,
        device: str = "cpu",
        output_dir: str = "model_creation/output/xai",
    ) -> Dict[str, Any]:

        # Load Model
        model = build_segmentation_model(
            model_type=model_type,
            width=width,
            pretrained=False,
            out_channels=1,
        ).to(device)

        state_dict = torch.load(checkpoint_path, map_location=device, weights_only=True)
        model.load_state_dict(state_dict)
        model.eval()

        # BEst Pred Image Eval
        self.logger.info("Evaluating Best Prediction")
        panel_case1, best_info = self.explainable_ai.explain_from_paths(
            model=model,
            image_path=best_orig_path,
            ground_truth_path=best_gt_path,
            device=device,
            img_size=img_size,
            title="Best",
        )

        # Worst Prd Image Eval
        self.logger.info("Evaluating Worst Prediction")
        panel_case2, worst_info = self.explainable_ai.explain_from_paths(
            model=model,
            image_path=worst_orig_path,
            ground_truth_path=worst_gt_path,
            device=device,
            img_size=img_size,
            title="Worst",
        )

        # save comparison image
        self.explainable_ai.save_compare_img(
            panels=[panel_case1, panel_case2],
            output_path=os.path.join(output_dir, "xai_gradcam_gallery.png"),
        )

        results = {
            "case1_best": {
                "orig_path": best_orig_path,
                "iou": best_info["iou"],
                "dice": best_info["dice"],
                "foreground_score": best_info["foreground_score"],
            },
            "case2_worst": {
                "orig_path": worst_orig_path,
                "iou": worst_info["iou"],
                "dice": worst_info["dice"],
                "foreground_score": worst_info["foreground_score"],
            }
        }

        # Save metrics JSON
        metrics_json_path = os.path.join(output_dir, "xai_metrics.json")
        with open(metrics_json_path, "w") as f:
            json.dump(results, f, indent=2)

        self.logger.info(f"XAI info added to: {metrics_json_path}")

        return results
