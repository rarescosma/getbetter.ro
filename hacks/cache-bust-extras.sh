#!/usr/bin/env bash

ASSET_VERSION=$(git rev-parse HEAD | cut -c 1-16)

for file in content/assets/stylesheets/*.css; do
    mv "$file" "${file%.css}.${ASSET_VERSION}.css"
done

for file in content/assets/javascripts/*.js; do
    mv "$file" "${file%.js}.${ASSET_VERSION}.js"
done

sed -i'' -r \
  -e "s#- assets/([^.]+)([^[:space:]]+)#- assets/\1.${ASSET_VERSION}\2#g" \
  mkdocs.yml
