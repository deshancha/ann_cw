# Author: Chamika Deshan
# Explainable AI (XAI) Interface

from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, List, Optional
from PIL import Image
import torch


class IExplainableAI(ABC):
    @abstractmethod
    def explain_from_paths(
        self,
        model: torch.nn.Module,
        image_path: str,
        ground_truth_path: str,
        device: str,
        img_size: int = 224,
        title: str = "",
    ) -> Tuple[Image.Image, Dict[str, Any]]:
        pass

    @abstractmethod
    def save_compare_img(
        self,
        panels: List[Image.Image],
        output_path: str,
    ) -> str:
        pass
