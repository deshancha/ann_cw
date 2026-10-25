# Author: Chamika Deshan
# Model Creation Interface

from abc import ABC, abstractmethod
from typing import Tuple
import torch
from torch.utils.data import DataLoader


class IModelCreation(ABC):

    @abstractmethod
    def train_epoch(
        self,
        model: torch.nn.Module,
        train_loader: DataLoader,
        optimizer: torch.optim.Optimizer,
        loss_fn: torch.nn.Module,
        device: str,
    ) -> float:
        """one epoch train -> return average train loss"""
        pass

    @abstractmethod
    def validate(
        self,
        model: torch.nn.Module,
        val_loader: DataLoader,
        loss_fn: torch.nn.Module,
        device: str,
    ) -> Tuple[float, float, float]:
        """Evaluates model -> returns (val_loss, val_iou, val_dice)"""
        pass

    @abstractmethod
    def save_checkpoint(self, model: torch.nn.Module, filepath: str) -> None:
        """Saves model state dict"""
        pass

    @abstractmethod
    def export_coreml(self, model: torch.nn.Module, filepath: str, img_size: int) -> None:
        """PyTorch model -> Apple CoreML"""
        pass

    @abstractmethod
    def export_tflite(
        self,
        model: torch.nn.Module,
        filepath: str,
        img_size: int = 256,
        in_nhwc: bool = True,
    ) -> None:
        """PyTorch model -> TensorFlow Lite"""
        pass

    @abstractmethod
    def generate_validation_image(
        self,
        model: torch.nn.Module,
        val_loader: DataLoader,
        device: str,
        output_dir: str,
    ) -> str:
        """Generate comparison image"""
        pass
