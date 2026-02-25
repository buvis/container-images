from redis import Redis
from rq import Worker

from clara.config import get_settings


def main() -> None:
    redis_conn = Redis.from_url(str(get_settings().redis_url))
    worker = Worker(["default"], connection=redis_conn)
    worker.work()


if __name__ == "__main__":
    main()
