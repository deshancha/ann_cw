# Author: Chamika Deshan
# Dataset Loading ImageNet

import os
from typing import Tuple
import torch
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

from core.util.logger import ILogger
from domain.manager.idata_loader import IDataLoader


class ImagenetteLoaderImp(IDataLoader):
    """Concrete implementation of IDataLoader for Imagenette dataset."""

    def __init__(self, data_dir: str, logger: ILogger):
        self.data_dir = data_dir
        self.logger = logger
        os.makedirs(self.data_dir, exist_ok=True)

    def get_dataloaders(self, img_size: int, batch_size: int) -> Tuple[DataLoader, DataLoader]:
        self.logger.info(f"Imagenette Loader init (img_size={img_size}, batch_size={batch_size})")

        # Normalization mean 0.5, std 0.5 (scaling to [-1, 1] MobileNet need)
        norm = transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))

        train_tf = transforms.Compose([
            transforms.RandomResizedCrop(img_size, scale=(0.5, 1.0)),
            transforms.RandomHorizontalFlip(),
            transforms.ToTensor(),
            norm,
        ])

        val_tf = transforms.Compose([
            transforms.Resize(img_size + 16),
            transforms.CenterCrop(img_size),
            transforms.ToTensor(),
            norm,
        ])

        train_ds = datasets.Imagenette(
            self.data_dir, split="train", size="160px", download=True, transform=train_tf
        )
        val_ds = datasets.Imagenette(
            self.data_dir, split="val", size="160px", download=False, transform=val_tf
        )

        self.logger.info(f"Loaded: train={len(train_ds)}, val={len(val_ds)}, classes={len(train_ds.classes)}")

        # num_workers=0 -> mac os issue
        train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=0)
        val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=0)

        return train_loader, val_loader
