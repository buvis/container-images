import os
import sys
import logging
from time import sleep

from syncer import Syncer
from config import Config, ConfigError
from linkcheck.service import LinkCheckService

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
    linkcheck = LinkCheckService(LINKCHECK_CONFIG_PATH, SITE_PATH)

    # run initial link check after first build
    linkcheck.run_check(after_build=True)

    logger.info("Starting main update loop.")
    try:
        while True:
            try:
                rebuilt = syncer.update()
                if rebuilt:
                    linkcheck.run_check(after_build=True)
                elif linkcheck.should_run():
                    linkcheck.run_check()
                logger.info(f"Waiting for {config.interval} seconds")
                sleep(config.interval)
            except Exception as e:
                logger.error(f"Error during sync/update: {e}", exc_info=True)
                logger.info(f"Retrying in {config.interval} seconds...")
                sleep(config.interval)
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user. Exiting gracefully.")


if __name__ == "__main__":
    main()
