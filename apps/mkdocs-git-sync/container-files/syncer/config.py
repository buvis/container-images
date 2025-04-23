import os
import sys
import logging
from typing import Optional

# Environment variable names as constants
GIT_REPO_ENV = "GIT_REPO"
GIT_CREDENTIALS_ENV = "GIT_CREDENTIALS"
GIT_BRANCH_ENV = "GIT_BRANCH"
UPDATE_INTERVAL_ENV = "UPDATE_INTERVAL"
# Defaults
DEFAULT_BRANCH = "main"
DEFAULT_INTERVAL = 900
DEFAULT_REQUIREMENTS_PATH = "/app/config/requirements.txt"

logger = logging.getLogger(__name__)


class ConfigError(Exception):
    """Custom exception for configuration errors."""

    pass


class Config:
    """
    Configuration loader for the application.

    Loads configuration from environment variables, applies defaults,
    and validates inputs.
    """

    def __init__(self) -> None:
        logger.info("Initializing configuration...")

        self.repo_url = os.environ.get(GIT_REPO_ENV)
        if not self.repo_url:
            logger.error(f"Environment variable {GIT_REPO_ENV} is required.")
            raise ConfigError(f"Environment variable {GIT_REPO_ENV} is required.")
        logger.info(f"Repository URL loaded from environment: {self.repo_url}.")

        if not self.repo_url.startswith("https://"):
            logger.error("Expected repo URL to start with https://")
            raise ConfigError("Expected repo URL to start with https://")

        credentials = os.environ.get(GIT_CREDENTIALS_ENV)
        if credentials:
            logger.info(
                "Git credentials found in environment. Injecting credentials into repo URL (not logging credentials)."
            )
            self.repo = f"https://{credentials}@{self.repo_url[8:]}"
        else:
            self.repo = self.repo_url
            logger.info("No git credentials found. Using plain repo URL.")

        self.branch = os.environ.get(GIT_BRANCH_ENV, DEFAULT_BRANCH)
        logger.info(f"Using branch: {self.branch}")

        interval_str = os.environ.get(UPDATE_INTERVAL_ENV)
        self.interval = self._parse_interval(interval_str)
        logger.info(f"Update interval set to: {self.interval} seconds")

    @staticmethod
    def _parse_interval(value: Optional[str]) -> int:
        """
        Parse the update interval from string, fallback to default if invalid.

        :param value: String value from environment.
        :return: Parsed integer interval.
        """
        if value is None:
            logger.info(
                f"No {UPDATE_INTERVAL_ENV} set; using default: {DEFAULT_INTERVAL}"
            )
            return DEFAULT_INTERVAL
        try:
            return int(value)
        except ValueError:
            logger.warning(
                f"Invalid {UPDATE_INTERVAL_ENV} value '{value}'; using default: {DEFAULT_INTERVAL}"
            )
            return DEFAULT_INTERVAL

    @staticmethod
    def install_requirements() -> None:
        """
        Install Python requirements if requirements.txt exists.
        """
        if os.path.exists(DEFAULT_REQUIREMENTS_PATH):
            logger.info(
                f"requirements.txt found at {DEFAULT_REQUIREMENTS_PATH}. Installing requirements..."
            )
            exit_code = os.system(
                f"python3 -m pip install --force-reinstall --no-cache-dir -q -r {DEFAULT_REQUIREMENTS_PATH}"
            )
            if exit_code == 0:
                logger.info("Requirements installed successfully.")
            else:
                logger.error(f"Failed to install requirements (exit code {exit_code}).")
        else:
            logger.info(
                f"No requirements.txt found at {DEFAULT_REQUIREMENTS_PATH}. Skipping requirements installation."
            )
