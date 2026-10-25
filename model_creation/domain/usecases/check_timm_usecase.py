import timm
import torch
from core.util.logger import ILogger

# check tim has pretrained mobilenetv1
class CheckTimmUseCase:

    def __init__(self, logger: ILogger):
        self.logger = logger

    def execute(self) -> list:
        models = timm.list_models("mobilenetv1*", pretrained=True)
        self.logger.info(f"Pretrained MobileNetV1 models aviable are: {models}")

        if models:
            first_model = models[0]
            self.logger.info(f"Cehck feature maps of {first_model} (features_only=True)")
            model = timm.create_model(first_model, pretrained=True, features_only=True)
            dummy_input = torch.randn(1, 3, 224, 224)
            features = model(dummy_input)

            for i, feat in enumerate(features):
                self.logger.info(f" Level {i} feature map: {tuple(feat.shape)}")

            mean = model.pretrained_cfg.get("mean")
            std = model.pretrained_cfg.get("std")
            self.logger.info(f"Normalization config - Mean: {mean}, Std: {std}")
        else:
            self.logger.warn("No pretrained MobileNetV1 models found in timm.")
        return models
