import os
import sys
import logging
from time import sleep

from syncer import Syncer
from config import Config, ConfigError


def setup_logging():
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="[%(levelname)s] %(asctime)s %(name)s: %(message)s",
        handlers=[logging.StreamHandler()],
    )


def main() -> None:
    """
    Main execution loop for the syncer application.
    Loads configuration, sets up the syncer, and runs the update loop.
    """
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

    logger.info("Starting main update loop.")
    try:
        while True:
            try:
                syncer.update()
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
