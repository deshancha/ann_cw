# Author: Chamika Deshan
# Clean Architecture Core Logger

import logging
import os
import sys
from abc import ABC, abstractmethod


class ILogger(ABC):
    @abstractmethod
    def info(self, message: str): pass

    @abstractmethod
    def warn(self, message: str): pass

    @abstractmethod
    def error(self, message: str): pass

    @abstractmethod
    def verbose(self, message: str): pass


class _BaseLogger(ILogger):
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        self.formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | [%(name)s] %(message)s'
        )

    def info(self, message: str):
        if self._is_enabled():
            self.logger.info(message)

    def warn(self, message: str):
        if self._is_enabled():
            self.logger.warning(message)

    def error(self, message: str):
        if self._is_enabled():
            self.logger.error(message)

    def verbose(self, message: str):
        if self._is_enabled():
            self.logger.debug(message)

    def _is_enabled(self) -> bool:
        return os.environ.get("LOG_ENABLED", "1") == "1"


class _ColorFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: "\033[97m",   # White
        logging.INFO: "\033[94m",    # Blue
        logging.WARNING: "\033[93m", # Yellow
        logging.ERROR: "\033[91m",   # Red
    }
    RESET = "\033[0m"

    def format(self, record):
        original_msg = str(record.msg)
        color = self.COLORS.get(record.levelno, self.RESET)
        record.msg = f"{color}{original_msg}{self.RESET}"
        result = super().format(record)
        record.msg = original_msg
        return result


class _ConsoleLogger(_BaseLogger):
    def __init__(self, name: str = "ConsoleLogger"):
        super().__init__(name)
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            color_formatter = _ColorFormatter(
                '%(asctime)s | %(levelname)-8s | [%(name)s] %(message)s'
            )
            handler.setFormatter(color_formatter)
            self.logger.addHandler(handler)


class LoggerFactory:
    @staticmethod
    def create(logger_type: str = "console", name: str = "ANN_CW") -> ILogger:
        return _ConsoleLogger(name)
