FROM python:3.8.2-slim

WORKDIR /opt/app

RUN apt-get -qq update \
    && apt-get -qq install -y git make \
    && pip install --no-cache-dir pipenv \
    && rm -rf /var/lib/apt

COPY Pipfile* ./
RUN pipenv install --system --deploy

RUN mkdir content
COPY mkdocs.yml ./
COPY server.py ./

CMD ["gunicorn", "-b", "0.0.0.0:8000"]
