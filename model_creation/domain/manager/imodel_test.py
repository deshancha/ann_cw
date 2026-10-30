# Author: Chamika Deshan
# Model Test Interface

from abc import ABC, abstractmethod
from typing import Tuple, Dict, Any
import torch
from torch.utils.data import DataLoader


class IModelTest(ABC):
    @abstractmethod
    def evaluate(
        self,
        model: torch.nn.Module,
        test_loader: DataLoader,
        device: str,
        output_dir: str = "",
    ) -> Tuple[float, float, Dict[str, Any]]:
        # Ret : test_iou, test_dice, extremes_dict (best & worst iou + image path)
        pass
