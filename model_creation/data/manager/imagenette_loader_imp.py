# Author: Chamika Deshan
# Dataset Loading ImageNet

import os
from typing import Tuple
import torch
from torch.utils.data import DataLoader


from core.util.logger import ILogger
from domain.manager.idata_loader import IDataLoader


class ImagenetteLoaderImp(IDataLoader):
    
    def __init__(self, data_dir: str, logger: ILogger):
        self.data_dir = data_dir
        self.logger = logger
        os.makedirs(self.data_dir, exist_ok=True)

    def get_dataloaders(self, img_size: int, batch_size: int) -> Tuple[DataLoader, DataLoader]:
        pass
