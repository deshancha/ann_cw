# Author: Chamika Deshan
# Dependency Injection Container

import os
from dotenv import load_dotenv
from dependency_injector import containers, providers

from core.util.logger import LoggerFactory, ILogger
from domain.manager.isegmentation_loader import ISegmentationLoader
from domain.manager.imodel_creation import IModelCreation
from domain.manager.imodel_test import IModelTest
from domain.manager.ibenchmark_manager import IBenchmarkManager
from data.manager.person_segmentation_loader_imp import PersonSegmentationLoaderImp
from data.manager.matting_human_loader_imp import MattingHumanLoaderImp
from data.manager.model_creation_imp import ModelCreationImp
from data.manager.model_test_imp import ModelTestImp
from data.manager.benchmark_manager_imp import BenchmarkManagerImp

from domain.usecases.check_timm_usecase import CheckTimmUseCase
from domain.usecases.train_model_usecase import TrainModelUseCase
from domain.usecases.validate_model_usecase import ValidateModelUseCase
from domain.usecases.test_model_usecase import TestModelUseCase
from domain.usecases.visualize_validation_result_usecase import VisualizeValidationResultUseCase
from domain.usecases.export_coreml_usecase import ExportCoreMLUseCase
from domain.usecases.export_tflite_usecase import ExportTFLiteUseCase
from domain.usecases.eval_grabcut_benchmark_usecase import EvalGrabcutBenchmarkUseCase
from domain.usecases.xai_gradcam_usecase import XAIGradCamUseCase


def init_output_directories():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
    
    global_candidates = [
        os.path.join(root_dir, "config", ".env.global")
    ]
    global_env_file = next((p for p in global_candidates if os.path.isfile(p)), None)

    if global_env_file:
        load_dotenv(dotenv_path=global_env_file, override=False)

    output_dirs = [
        os.getenv("CHECKPOINTS_DIR", "model_creation/output/checkpoints"),
        os.getenv("EXPERIMENTS_DIR", "model_creation/output/experiments"),
        os.getenv("OUTPUT_DIR", "model_creation/output/gen_images"),
        os.getenv("METRICS_DIR", "model_creation/output/metrics"),
        os.getenv("XAI_DIR", "model_creation/output/xai"),
    ]

    for d in output_dirs:
        abs_dir = d if os.path.isabs(d) else os.path.abspath(os.path.join(root_dir, d))
        os.makedirs(abs_dir, exist_ok=True)


class AppContainerMeta(type(containers.DeclarativeContainer)):
    
    def __call__(cls, *args, **kwargs):
        instance = super().__call__(*args, **kwargs)
        init_output_directories()
        return instance


class AppContainer(containers.DeclarativeContainer, metaclass=AppContainerMeta):
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

    benchmark_manager: providers.Provider[IBenchmarkManager] = providers.Singleton(
        BenchmarkManagerImp,
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

    # Step 6: Benchmark GrabCut vs U-Net
    eval_grabcut_benchmark_usecase = providers.Factory(
        EvalGrabcutBenchmarkUseCase,
        data_loader=matting_human_loader,
        benchmark_manager=benchmark_manager,
        logger=logger,
    )
