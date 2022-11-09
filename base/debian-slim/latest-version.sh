#!/usr/bin/env bash

version=$(curl -s "https://hub.docker.com/v2/repositories/library/debian/tags?page_size=100" | jq --raw-output '.results[] | select(.name | test("^stable-.*-slim$")) | .name'  | head -n1)
version="${version#*v}"
version="${version#*release-}"
printf "%s" "${version}"
