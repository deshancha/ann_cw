from dependency_injector import containers, providers

from core.util.logger import LoggerFactory, ILogger


class AppContainer(containers.DeclarativeContainer):
    """DI Container"""

    config = providers.Configuration()

    logger: providers.Provider[ILogger] = providers.Singleton(
        LoggerFactory.create,
        logger_type="console",
        name="ANN_CW",
    )
