#!/usr/bin/env bash

version="curl -Ls https://pypi.org/pypi/Mopidy-Iris/json | jq -r .info.version"
printf "%s" "${version}"
