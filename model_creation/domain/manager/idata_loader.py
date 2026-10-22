# Author: Chamika Deshan
# Dataset Loading

from abc import ABC, abstractmethod
from typing import Tuple, Any


class IDataLoader(ABC):
    @abstractmethod
    def get_dataloaders(self, img_size: int, batch_size: int) -> Tuple[Any, Any]:
        pass
