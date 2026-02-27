import os
import sys
import logging
import threading

from syncer import Syncer
from config import Config, ConfigError
from linkcheck.service import LinkCheckService
from webhook.server import WebhookServer

LINKCHECK_CONFIG_PATH = "/app/config/linkcheck.yml"
SITE_PATH = "/app/site"


def setup_logging():
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="[%(levelname)s] %(asctime)s %(name)s: %(message)s",
        handlers=[logging.StreamHandler()],
    )


def main() -> None:
    setup_logging()
    logger = logging.getLogger("syncer")

    try:
        Config.install_requirements()
        config = Config()
    except ConfigError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during initialization: {e}", exc_info=True)
        sys.exit(1)

    syncer = Syncer(config)

    if not syncer.site_ready:
        logger.error("Initial site build failed. Exiting.")
        sys.exit(1)

    linkcheck = LinkCheckService(LINKCHECK_CONFIG_PATH, SITE_PATH)
    linkcheck.run_check(after_build=True)

    trigger_event = threading.Event()

    if config.webhook_enabled:
        webhook_server = WebhookServer(
            trigger_event=trigger_event,
            branch=config.branch,
            port=config.webhook_port,
            providers=config.webhook_providers,
        )
        webhook_server.start()

    logger.info("Starting main update loop.")
    try:
        while True:
            try:
                triggered = trigger_event.wait(timeout=config.interval)
                trigger_event.clear()
                source = "webhook" if triggered else "poll"

                rebuilt = syncer.update(source=source)
                if rebuilt:
                    linkcheck.run_check(after_build=True)
                elif syncer.site_ready and linkcheck.should_run():
                    linkcheck.run_check()
            except Exception as e:
                logger.error(f"Error during sync/update: {e}", exc_info=True)
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user. Exiting gracefully.")


if __name__ == "__main__":
    main()
