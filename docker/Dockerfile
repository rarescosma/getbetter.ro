ARG BUILDER_VERSION
ARG REGISTRY

FROM ${REGISTRY}/getbetter:${BUILDER_VERSION} as BUILDER

WORKDIR /pv

COPY getbetter ./getbetter
COPY pyproject.toml ./
COPY hacks/gallerize-entrypoint.sh /usr/bin/

RUN pip install . --no-deps

RUN useradd -u 1000 -U getbetter
USER getbetter

CMD ["gunicorn", "-b", "0.0.0.0:8000"]
