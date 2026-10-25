# Author: Chamika Deshan
# Person Segmentation Dataset Loader Implementation (Supervisely)

import os
import random
from typing import Tuple, List
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
import torchvision.transforms.functional as TF
from PIL import Image

from core.util.logger import ILogger
from domain.manager.isegmentation_loader import ISegmentationLoader


class PersonSegmentationDataset(Dataset):
    """Person Segmentation Dataset representation"""

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
            mask = TF.resize(mask, [self.img_size, self.img_size], interpolation=transforms.InterpolationMode.NEAREST)

            # augmentations for training
            if self.is_train:
                # Random horizontal flip
                if random.random() > 0.5:
                    img = TF.hflip(img)
                    mask = TF.hflip(mask)

            # normalize to [-1.0, 1.0] for MobileNet
            img_tensor = TF.to_tensor(img)
            img_tensor = self.norm(img_tensor)

            # binary mask normalized to [0.0, 1.0] float tensor (1, H, W)
            mask_np = np.array(mask, dtype=np.float32)
            mask_binary = (mask_np > 128.0).astype(np.float32)
            mask_tensor = torch.from_numpy(mask_binary).unsqueeze(0)

            return img_tensor, mask_tensor


class PersonSegmentationLoaderImp(ISegmentationLoader):
    """implementation of ISegmentationLoader for Person Segmentation dataset"""

    def __init__(self, data_dir: str, logger: ILogger, seed: int = 42):
        self.data_dir = data_dir
        self.logger = logger
        self.seed = seed
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
            f"Person Segmentation Loader init (img_size={img_size}, batch_size={batch_size}, "
            f"max_train={max_train_samples}, max_val={max_val_samples})"
        )


        # Normalization mean 0.5, std 0.5 (scaling to [-1, 1] MobileNet need)
        norm = transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))

        img_dir = os.path.join(self.data_dir, "images")
        mask_dir = os.path.join(self.data_dir, "masks")

        if not os.path.exists(img_dir) or not os.path.exists(mask_dir):
            raise FileNotFoundError(f"Missing images or masks folder in: {self.data_dir}")

        filenames = sorted(
            [f for f in os.listdir(img_dir) if f.lower().endswith((".png", ".jpg", ".jpeg"))]
        )

        # training and validation pairs
        image_paths = []
        mask_paths = []
        for name in filenames:
            m_path = os.path.join(mask_dir, name)
            if os.path.exists(m_path):
                image_paths.append(os.path.join(img_dir, name))
                mask_paths.append(m_path)

        assert len(image_paths) > 0, "No valid image-mask pairs found!"

        # Fixed deterministic split (seed=42 for reproducibility)
        indices = list(range(len(image_paths)))
        random.seed(self.seed)
        random.shuffle(indices)

        val_size = int(len(indices) * val_split)
        val_indices = set(indices[:val_size])
        train_indices = [i for i in indices if i not in val_indices]

        train_imgs = [image_paths[i] for i in train_indices]
        train_masks = [mask_paths[i] for i in train_indices]

        val_imgs = [image_paths[i] for i in val_indices]
        val_masks = [mask_paths[i] for i in val_indices]

        # Apply subset limits if specified (> 0)
        if max_train_samples and max_train_samples > 0:
            train_imgs = train_imgs[:max_train_samples]
            train_masks = train_masks[:max_train_samples]

        if max_val_samples and max_val_samples > 0:
            val_imgs = val_imgs[:max_val_samples]
            val_masks = val_masks[:max_val_samples]

        train_ds = PersonSegmentationDataset(

            image_paths=train_imgs,
            mask_paths=train_masks,
            img_size=img_size,
            is_train=True,
            norm=norm,
        )

        val_ds = PersonSegmentationDataset(
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
