# Author: Chamika Deshan
# Dependency Injection Container

from dependency_injector import containers, providers

from core.util.logger import LoggerFactory, ILogger
from domain.manager.isegmentation_loader import ISegmentationLoader
from domain.manager.imodel_creation import IModelCreation
from data.manager.person_segmentation_loader_imp import PersonSegmentationLoaderImp
from data.manager.matting_human_loader_imp import MattingHumanLoaderImp
from data.manager.model_creation_imp import ModelCreationImp

from domain.usecases.check_timm_usecase import CheckTimmUseCase
from domain.usecases.train_unet_usecase import TrainUNetUseCase
from domain.usecases.quick_validation_usecase import QuickValidationUseCase
from domain.usecases.train_and_validate_full_usecase import TrainAndValidateFullUseCase


class AppContainer(containers.DeclarativeContainer):
    """DI Container"""

    config = providers.Configuration()

    logger: providers.Provider[ILogger] = providers.Singleton(
        LoggerFactory.create,
        logger_type="console",
        name="ANN_CW",
    )

    segmentation_loader: providers.Provider[ISegmentationLoader] = providers.Singleton(
        PersonSegmentationLoaderImp,
        data_dir=config.training.segmentation_data_dir,
        logger=logger,
        seed=config.training.seed,
    )

    matting_human_loader: providers.Provider[ISegmentationLoader] = providers.Singleton(
        MattingHumanLoaderImp,
        data_dir=config.training.matting_data_dir,
        logger=logger,
    )

    model_creation: providers.Provider[IModelCreation] = providers.Singleton(
        ModelCreationImp,
        logger=logger,
    )

    check_timm_usecase = providers.Factory(
        CheckTimmUseCase,
        logger=logger,
    )

    train_unet_usecase = providers.Factory(
        TrainUNetUseCase,
        data_loader=matting_human_loader,
        logger=logger,
    )

    quick_validation_usecase = providers.Factory(
        QuickValidationUseCase,
        data_loader=matting_human_loader,
        logger=logger,
    )

    train_and_validate_full_usecase = providers.Factory(
        TrainAndValidateFullUseCase,
        data_loader=matting_human_loader,
        model_creation=model_creation,
        logger=logger,
    )
