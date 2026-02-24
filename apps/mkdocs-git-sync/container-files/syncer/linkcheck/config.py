import logging
from typing import List, Dict, Any

import yaml

logger = logging.getLogger(__name__)

DEFAULT_EXCLUSIONS = [
    r"^javascript:",
    r"^mailto:",
    r"^tel:",
    r"^data:",
    r"^#",
]

DEFAULT_INTERVAL = 21600  # 6 hours


class LinkCheckConfig:
    def __init__(self, config_path: str):
        self.enabled: bool = False
        self.interval: int = DEFAULT_INTERVAL
        self.exclude_patterns: List[str] = list(DEFAULT_EXCLUSIONS)
        self.notifications: List[Dict[str, Any]] = []

        self._load(config_path)

    def _load(self, path: str) -> None:
        try:
            with open(path) as f:
                data = yaml.safe_load(f) or {}
        except FileNotFoundError:
            logger.info(f"No linkcheck config at {path}, link checking disabled")
            return
        except yaml.YAMLError as e:
            logger.error(f"Invalid linkcheck config: {e}")
            return

        self.enabled = data.get("enabled", False)
        if not self.enabled:
            return

        self.interval = data.get("interval", DEFAULT_INTERVAL)
        user_excludes = data.get("exclude", [])
        self.exclude_patterns = list(DEFAULT_EXCLUSIONS) + user_excludes
        self.notifications = data.get("notifications", [])

        logger.info(
            f"Link checking enabled: interval={self.interval}s, "
            f"{len(self.notifications)} notification target(s), "
            f"{len(self.exclude_patterns)} exclusion pattern(s)"
        )
