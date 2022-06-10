ARG BUILDER_VERSION
ARG REGISTRY

FROM ${REGISTRY}/getbetter:${BUILDER_VERSION} as BUILDER

WORKDIR /pv

COPY getbetter ./getbetter
COPY setup.py ./
COPY hacks/gallerize-entrypoint.sh /usr/bin/

RUN pip install -e .

RUN useradd -u 1000 -U getbetter
USER getbetter

CMD ["gunicorn", "-b", "0.0.0.0:8000"]
