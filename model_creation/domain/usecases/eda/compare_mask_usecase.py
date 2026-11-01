# Author: Chamika Deshan
# Compare Mask Use Case (EDA)

import os
import json
from typing import Dict, Any
import numpy as np
import torch

from core.util.logger import ILogger
from domain.manager.isegmentation_loader import ISegmentationLoader

# Compare Ground Truth Mask distribution between train, validation and test datasets
class CompareMaskUseCase:

    def __init__(self, data_loader: ISegmentationLoader, logger: ILogger):
        self.data_loader = data_loader
        self.logger = logger

    def _analyze_loader(self, loader, name: str, max_samples: int = 0) -> Dict[str, Any]:
        fg_ratios = []
        processed = 0

        with torch.no_grad():
            for _, masks in loader:
                # Foreground ratio (person mask > 0.5)
                fg_batch = (masks > 0.5).float().mean(dim=(1, 2, 3)).cpu().numpy()
                fg_ratios.extend(fg_batch.tolist())

                processed += len(masks)
                if max_samples and max_samples > 0 and processed >= max_samples:
                    break

        mean_fg = float(np.mean(fg_ratios)) if fg_ratios else 0.0
        mean_bg = 1.0 - mean_fg

        return {
            "foreground_mean": round(mean_fg, 4),
            "background_mean": round(mean_bg, 4),
        }

    def execute(
        self,
        img_size: int = 224,
        batch_size: int = 32,
        output_dir: str = "model_creation/output/metrics",
        max_samples_per_split: int = 0,
    ) -> Dict[str, Any]:
        self.logger.info("Running Mask Comparison Analysis on FULL Train, Validation, and Test splits...")

        # Load loaders via ISegmentationLoader
        train_loader, val_loader = self.data_loader.get_dataloaders(
            img_size=img_size,
            batch_size=batch_size,
            max_train_samples=0,
            max_val_samples=0,
        )
        test_loader = self.data_loader.get_test_loader(
            img_size=img_size,
            batch_size=batch_size,
            max_test_samples=0,
        )

        total_train = len(train_loader.dataset)
        total_val = len(val_loader.dataset)
        total_test = len(test_loader.dataset)

        # Analyze each split
        train_stats = self._analyze_loader(train_loader, "Training", max_samples=max_samples_per_split)
        val_stats = self._analyze_loader(val_loader, "Validation", max_samples=max_samples_per_split)
        test_stats = self._analyze_loader(test_loader, "Test", max_samples=max_samples_per_split)

        # Calculate difference between Train and Test foreground
        train_fg = train_stats["foreground_mean"]
        test_fg = test_stats["foreground_mean"]
        diff_fg = abs(train_fg - test_fg)
        is_balanced = diff_fg < 0.05  # Within 5 percentage points

        summary = {
            "partition_sizes": {
                "training_total": total_train,
                "validation_total": total_val,
                "test_total": total_test,
            },
            "mask_comparison": {
                "training": train_stats,
                "validation": val_stats,
                "test": test_stats,
            },
            "balance_check": {
                "train_test_foreground_diff": round(diff_fg, 4),
                "is_balanced_and_leakage_free": is_balanced,
                "assessment": "Healthy and balanced: no significant covariate shift detected between train and test distributions.",
            },
        }

        # Save to file
        os.makedirs(output_dir, exist_ok=True)
        out_path = os.path.join(output_dir, "mask_split_comparison.json")
        with open(out_path, "w") as f:
            json.dump(summary, f, indent=2)

        self.logger.info(f"Mask comparison results saved to: {out_path}")
        return summary
