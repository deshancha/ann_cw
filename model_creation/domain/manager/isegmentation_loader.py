from abc import ABC, abstractmethod
from typing import Tuple, Any


class ISegmentationLoader(ABC):
    """Human Segmentation Data Loader Interface"""

    @abstractmethod
    def get_dataloaders(
        self,
        img_size: int,
        batch_size: int,
        val_split: float = 0.2,
        max_train_samples: int = 0,
        max_val_samples: int = 0,
    ) -> Tuple[Any, Any]:
        # return -> train and validation loaders
        pass

