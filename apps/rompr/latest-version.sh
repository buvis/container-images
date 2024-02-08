#!/usr/bin/env bash

version="$(curl --silent -qI https://github.com/fatg3erman/RompR/releases/latest | awk -F '/' '/^location/ {print  substr($NF, 1, length($NF)-1)}')"
printf "%s" "${version}"
