ARG BUILDER_VERSION
ARG REGISTRY

FROM ${REGISTRY}/getbetter.ro:${BUILDER_VERSION} as BUILDER

COPY getbetter ./getbetter
COPY pyproject.toml ./
COPY hacks/gallerize-entrypoint.sh /usr/bin/

RUN pip install . --no-deps

RUN useradd -u 1000 -U getbetter
USER getbetter
