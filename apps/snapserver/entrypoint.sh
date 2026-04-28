#!/usr/bin/env bash
exec /usr/bin/snapserver --logging.sink=stdout -c /etc/snapserver.conf "$@"
