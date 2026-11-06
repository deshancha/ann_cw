# Author: Chamika Deshan
# MobileSam Manager Interface

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple
import numpy as np

# Run mobile sam
class IFoundationModelManager(ABC):
    @abstractmethod
    def benchmark_mobilesam(
        self,
        images_np: List[np.ndarray],
        masks_np: List[np.ndarray],
        checkpoint_path: str,
        device: str,
        box_margin: float = 0.05,
    ) -> Dict[str, Any]:
        pass

    # save GT, UNET, MobSam side by side
    @abstractmethod
    def visualize_foundation_comparison(
        self,
        samples: List[Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, float, float]],
        output_path: str,
    ) -> None:
        pass

