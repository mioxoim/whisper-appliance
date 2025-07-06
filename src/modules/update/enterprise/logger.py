"""
Enterprise Logger
Professional logging system for WhisperS2T Enterprise features

Author: WhisperS2T Enterprise Team
Version: 0.8.0
"""

import logging
import sys


class EnterpriseLogger:
    """Enterprise-grade structured logging"""

    def __init__(self, name: str = "enterprise_updater"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        if not self.logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter("%(asctime)s [%(levelname)8s] [Enterprise] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

    def info(self, message: str):
        self.logger.info(message)

    def warning(self, message: str):
        self.logger.warning(message)

    def error(self, message: str):
        self.logger.error(message)

    def debug(self, message: str):
        self.logger.debug(message)
