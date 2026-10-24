# Author: Chamika Deshan
# Dependency Injection Container

from dependency_injector import containers, providers

from core.util.logger import LoggerFactory, ILogger
from domain.manager.idata_loader import IDataLoader

from data.manager.imagenette_loader_imp import ImagenetteLoaderImp

from domain.manager.isegmentation_loader import ISegmentationLoader
from data.manager.matting_human_loader_imp import MattingHumanLoaderImp


class AppContainer(containers.DeclarativeContainer):
    """DI Container"""

    config = providers.Configuration()

    logger: providers.Provider[ILogger] = providers.Singleton(
        LoggerFactory.create,
        logger_type="console",
        name="ANN_CW",
    )

    data_loader: providers.Provider[IDataLoader] = providers.Singleton(
        ImagenetteLoaderImp,
        data_dir=config.training.data_dir,
        logger=logger,
    )

    matting_human_loader: providers.Provider[ISegmentationLoader] = providers.Singleton(
        MattingHumanLoaderImp,
        data_dir=config.training.matting_data_dir,
        logger=logger,
    )
