#!/usr/bin/env bash

version="$(curl -Ls https://api.github.com/repos/badaix/snapcast/releases/latest | jq -r .tag_name | sed 's/^v//')"
printf "%s" "${version}"
