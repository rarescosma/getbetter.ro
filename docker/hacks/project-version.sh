#!/usr/bin/env bash

git ls-files -s        \
  getbetter mkdocs.yml \
  setup.cfg setup.py   \
  Pipfile Pipfile.lock \
  | git hash-object --stdin \
  | cut -c-20
