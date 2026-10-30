# Author: Chamika Deshan
# Test Model Use Case

import os
import json
from typing import Dict, Any
import torch

from core.util.logger import ILogger
from domain.manager.isegmentation_loader import ISegmentationLoader
from domain.manager.imodel_test import IModelTest
from domain.model.model_factory import build_segmentation_model


# Evaluate model on held-out test dataset
class TestModelUseCase:

    def __init__(
        self,
        data_loader: ISegmentationLoader,
        model_test: IModelTest,
        logger: ILogger,
    ):
        self.data_loader = data_loader
        self.model_test = model_test
        self.logger = logger

    def execute(
        self,
        checkpoint_path: str,
        model_type: str = "mobilenetv3",
        img_size: int = 224,
        width: float = 1.0,
        device: str = "mps",
        output_dir: str = "output/metrics",
        max_test_samples: int = 0,
    ) -> Dict[str, Any]:
        os.makedirs(output_dir, exist_ok=True)

        # load data
        test_loader = self.data_loader.get_test_loader(
            img_size=img_size,
            batch_size=1,
            max_test_samples=max_test_samples,
        )

        # load Model
        self.logger.info(f"Loading {model_type} model from: {checkpoint_path}")
        model = build_segmentation_model(
            model_type=model_type,
            width=width,
            pretrained=False,
            out_channels=1,
        ).to(device)
        state_dict = torch.load(checkpoint_path, map_location=device, weights_only=True)
        model.load_state_dict(state_dict)
        model.eval()

        # Test eval
        test_iou, test_dice, extremes = self.model_test.evaluate(
            model=model,
            test_loader=test_loader,
            device=device,
            output_dir=output_dir,
        )

        results = {
            "test_iou": round(float(test_iou), 4),
            "test_dice": round(float(test_dice), 4),
            "checkpoint": os.path.basename(checkpoint_path),
            "extremes": extremes,
        }

        # save test metrics JSON
        metrics_file = os.path.join(output_dir, f"metrics_test_{model_type}.json")
        with open(metrics_file, "w") as f:
            json.dump(results, f, indent=2)

        return results
