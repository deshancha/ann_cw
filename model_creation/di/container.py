# Author: Chamika Deshan
# Dependency Injection Container

from dependency_injector import containers, providers

from core.util.logger import LoggerFactory, ILogger
from domain.manager.isegmentation_loader import ISegmentationLoader
from domain.manager.imodel_creation import IModelCreation
from domain.manager.imodel_test import IModelTest
from data.manager.person_segmentation_loader_imp import PersonSegmentationLoaderImp
from data.manager.matting_human_loader_imp import MattingHumanLoaderImp
from data.manager.model_creation_imp import ModelCreationImp
from data.manager.model_test_imp import ModelTestImp

from domain.usecases.check_timm_usecase import CheckTimmUseCase
from domain.usecases.train_model_usecase import TrainModelUseCase
from domain.usecases.validate_model_usecase import ValidateModelUseCase
from domain.usecases.test_model_usecase import TestModelUseCase
from domain.usecases.visualize_validation_result_usecase import VisualizeValidationResultUseCase
from domain.usecases.export_coreml_usecase import ExportCoreMLUseCase
from domain.usecases.export_tflite_usecase import ExportTFLiteUseCase


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

    model_test: providers.Provider[IModelTest] = providers.Singleton(
        ModelTestImp,
        logger=logger,
    )

    check_timm_usecase = providers.Factory(
        CheckTimmUseCase,
        logger=logger,
    )

    # Step 1: Train model & save checkpoints
    train_model_usecase = providers.Factory(
        TrainModelUseCase,
        data_loader=matting_human_loader,
        model_creation=model_creation,
        logger=logger,
    )

    # Step 2: Validate checkpoint & save metrics.json
    validate_model_usecase = providers.Factory(
        ValidateModelUseCase,
        data_loader=matting_human_loader,
        model_creation=model_creation,
        logger=logger,
    )

    # Step 2b: Test model on held-out test dataset
    test_model_usecase = providers.Factory(
        TestModelUseCase,
        data_loader=matting_human_loader,
        model_test=model_test,
        logger=logger,
    )

    # Step 3: Visualize validation result
    visualize_validation_result_usecase = providers.Factory(
        VisualizeValidationResultUseCase,
        data_loader=matting_human_loader,
        model_creation=model_creation,
        logger=logger,
    )

    # Step 4: Export Apple CoreML (.mlpackage)
    export_coreml_usecase = providers.Factory(
        ExportCoreMLUseCase,
        model_creation=model_creation,
        logger=logger,
    )

    # Step 5: Export TensorFlow Lite (.tflite)
    export_tflite_usecase = providers.Factory(
        ExportTFLiteUseCase,
        model_creation=model_creation,
        logger=logger,
    )
