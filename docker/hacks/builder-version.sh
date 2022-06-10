#!/usr/bin/env bash

ROOT=$(git rev-parse --show-toplevel)

[[ -x "$(command -v md5)" ]] && md5_cmd="md5 -r"
[[ -x "$(command -v md5sum)" ]] && md5_cmd="md5sum"

REQ_HASH=$(
  cat \
    "$ROOT/Pipfile" \
    "$ROOT/Pipfile.lock" \
    "$ROOT/docker/Dockerfile-builder" \
  | ${md5_cmd} \
  | cut -d' ' -f1 \
  | tr '[:upper:]' '[:lower:]'
)

echo "builder-${REQ_HASH:0:16}"
