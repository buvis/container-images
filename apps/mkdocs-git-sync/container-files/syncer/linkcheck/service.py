import logging
import time

from linkcheck.config import LinkCheckConfig
from linkcheck.checker import LinkChecker
from linkcheck.notifiers import NotificationDispatcher

logger = logging.getLogger(__name__)


class LinkCheckService:
    def __init__(self, config_path: str, site_path: str):
        self.config = LinkCheckConfig(config_path)
        self.site_path = site_path
        self.last_run: float = 0

        if self.config.enabled:
            self.checker = LinkChecker(site_path, self.config.exclude_patterns)
            self.dispatcher = NotificationDispatcher(self.config.notifications)

    def should_run(self) -> bool:
        if not self.config.enabled:
            return False
        if self.last_run == 0:
            return True
        return (time.time() - self.last_run) >= self.config.interval

    def run_check(self, after_build: bool = False) -> None:
        if not self.config.enabled:
            return

        if not after_build and not self.should_run():
            return

        logger.info("Starting link check%s", " (post-build)" if after_build else "")
        result = self.checker.run()
        self.dispatcher.notify(result)
        self.last_run = time.time()
