# Author: Chamika Deshan
# Benchmark Manager Interface

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple
import numpy as np
import torch

class IBenchmarkManager(ABC):
    @abstractmethod
    def benchmark_grabcut(
        self, images_np: List[np.ndarray], masks_np: List[np.ndarray]
    ) -> Dict[str, Any]:
        """GrabCut on image set -> ret (mean_iou, mean_dice)"""
        pass

    @abstractmethod
    def benchmark_unet(
        self,
        model: torch.nn.Module,
        test_loader: Any,
        device: str,
    ) -> Dict[str, Any]:
        """Runs U-Net, ret (mean_iou, mean_dice)"""
        pass

    @abstractmethod
    def visualize_comparison(
        self,
        samples: List[Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, float, float]],
        output_path: str,
    ) -> None:
        """Saves visual comparison Original, Ground Truth, GrabCut and UNet"""
        pass
