# Author: Chamika Deshan
# Matting Human Dataset Loader Implementation (AISegment)

import os
import glob
import random
from typing import Tuple, List
import torch
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
import torchvision.transforms.functional as TF
from PIL import Image

from core.util.logger import ILogger
from domain.manager.isegmentation_loader import ISegmentationLoader


class MattingHumanDataset(Dataset):
    """ Matting Human Dataset representation"""

    def __init__(
        self,
        image_paths: List[str],
        mask_paths: List[str],
        img_size: int,
        is_train: bool = True,
        norm: transforms.Normalize = None,
    ):
        self.image_paths = image_paths
        self.mask_paths = mask_paths
        self.img_size = img_size
        self.is_train = is_train

        self.norm = norm if norm is not None else transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
        self.img_norm = self.norm

    def __len__(self) -> int:
        return len(self.image_paths)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        img_path = self.image_paths[idx]
        mask_path = self.mask_paths[idx]

        with Image.open(img_path) as img_pil, Image.open(mask_path) as mask_pil:
            img = img_pil.convert("RGB")

            # get alpha channel if rgba else to greyscale
            if mask_pil.mode == "RGBA":
                mask = mask_pil.split()[-1]
            else:
                mask = mask_pil.convert("L")

            # to model input size
            img = TF.resize(img, [self.img_size, self.img_size], interpolation=transforms.InterpolationMode.BILINEAR)
            mask = TF.resize(mask, [self.img_size, self.img_size], interpolation=transforms.InterpolationMode.BILINEAR)

            # augmentations for training
            if self.is_train:
                # Random horizontal flip
                if random.random() > 0.5:
                    img = TF.hflip(img)
                    mask = TF.hflip(mask)

                # Mild color jitter on RGB only (lighting variations)
                if random.random() > 0.5:
                    brightness = random.uniform(0.85, 1.15)
                    contrast = random.uniform(0.85, 1.15)
                    img = TF.adjust_brightness(img, brightness)
                    img = TF.adjust_contrast(img, contrast)

            # normalize to [-1.0, 1.0] for MobileNet
            img_tensor = TF.to_tensor(img)
            img_tensor = self.norm(img_tensor)

            # alpha mask normalized to [0.0, 1.0]
            mask_tensor = TF.to_tensor(mask)

            return img_tensor, mask_tensor


class MattingHumanLoaderImp(ISegmentationLoader):
    """implementation of ISegmentationLoader for Matting Human dataset"""

    def __init__(self, data_dir: str, logger: ILogger):
        self.data_dir = data_dir
        self.logger = logger
        os.makedirs(self.data_dir, exist_ok=True)

    def get_dataloaders(
        self,
        img_size: int,
        batch_size: int,
        val_split: float = 0.2,
        max_train_samples: int = 0,
        max_val_samples: int = 0,
    ) -> Tuple[DataLoader, DataLoader]:
        self.logger.info(
            f"Matting Human Loader init (img_size={img_size}, batch_size={batch_size}, "
            f"max_train={max_train_samples}, max_val={max_val_samples})"
        )

        # Normalization mean 0.5, std 0.5 (scaling to [-1, 1] MobileNet need)
        norm = transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))

        train_img_dir = os.path.join(self.data_dir, "training", "original")
        train_mask_dir = os.path.join(self.data_dir, "training", "matting")
        val_img_dir = os.path.join(self.data_dir, "validation", "original")
        val_mask_dir = os.path.join(self.data_dir, "validation", "matting")

        # training pairs
        train_imgs = sorted(glob.glob(os.path.join(train_img_dir, "*.*")))
        train_masks = sorted(glob.glob(os.path.join(train_mask_dir, "*.*")))

        # validation pairs
        val_imgs = sorted(glob.glob(os.path.join(val_img_dir, "*.*")))
        val_masks = sorted(glob.glob(os.path.join(val_mask_dir, "*.*")))

        assert len(train_imgs) == len(train_masks) and len(train_imgs) > 0, "No training samples found!"
        assert len(val_imgs) == len(val_masks) and len(val_imgs) > 0, "No validation samples found!"

        # Apply subset limits if specified (> 0)
        if max_train_samples and max_train_samples > 0:
            train_imgs = train_imgs[:max_train_samples]
            train_masks = train_masks[:max_train_samples]

        if max_val_samples and max_val_samples > 0:
            val_imgs = val_imgs[:max_val_samples]
            val_masks = val_masks[:max_val_samples]


        train_ds = MattingHumanDataset(
            image_paths=train_imgs,
            mask_paths=train_masks,
            img_size=img_size,
            is_train=True,
            norm=norm,
        )

        val_ds = MattingHumanDataset(
            image_paths=val_imgs,
            mask_paths=val_masks,
            img_size=img_size,
            is_train=False,
            norm=norm,
        )

        self.logger.info(f"Loaded: train={len(train_ds)}, val={len(val_ds)}")

        # num_workers=0 -> mac os issue
        train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=0)
        val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=0)

        return train_loader, val_loader
