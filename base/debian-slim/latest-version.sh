#!/usr/bin/env bash

version=$(curl -s "https://registry.hub.docker.com/v1/repositories/library/debian/tags" | jq --raw-output '.[] | select(.name | test("^stable-.*-slim$")) | .name'  | tail -n1)
version="${version#*v}"
version="${version#*release-}"
printf "%s" "${version}"
