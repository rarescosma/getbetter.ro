#!/usr/bin/env bash

git ls-files -s getbetter mkdocs.yml setup.cfg pyproject.toml poetry.lock \
  | git hash-object --stdin \
  | cut -c-20
