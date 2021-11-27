from time import sleep

from syncer import Syncer
from config import Config


if __name__ == "__main__":
    cfg = Config()
    syncer = Syncer(cfg.repo, cfg.branch)

    print(f"Source repo will be checked every {cfg.interval}s")

    while True:
        syncer.update()
        sleep(cfg.interval)
