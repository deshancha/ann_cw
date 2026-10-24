# Author: Chamika Deshan
# Dependency Injection Container

from dependency_injector import containers, providers

from core.util.logger import LoggerFactory, ILogger
from domain.manager.isegmentation_loader import ISegmentationLoader
from data.manager.person_segmentation_loader_imp import PersonSegmentationLoaderImp
from data.manager.matting_human_loader_imp import MattingHumanLoaderImp


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
