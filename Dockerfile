FROM python:3.8.2-slim

WORKDIR /opt/app

COPY Pipfile* ./
RUN apt-get -qq update \
    && apt-get -qq install -y git \
    && pip install --no-cache-dir pipenv \
    && pipenv install --system --deploy \
    && rm -rf /var/lib/apt

RUN mkdir content
COPY mkdocs.yml ./
COPY server.py ./

CMD ["gunicorn", "-b", "0.0.0.0:8000"]
