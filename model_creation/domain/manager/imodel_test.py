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
    ) -> Tuple[float, float]:
        # Ret : test_iou, test_dice
        pass
