FROM python:3.8.2-slim

WORKDIR /pv

RUN apt-get -qq update \
    && apt-get -qq install -y git make wget rsync imagemagick xz-utils \
    && pip install --no-cache-dir pipenv \
    && rm -rf /var/lib/apt

RUN wget -qO- "https://github.com/watchexec/watchexec/releases/download/1.12.0/watchexec-1.12.0-x86_64-unknown-linux-gnu.tar.xz" \
  | tar -xJf - --strip-components 1 -C /tmp/ \
  && mv /tmp/watchexec /usr/bin

COPY Pipfile* ./
RUN pipenv install --system --deploy

COPY getbetter ./getbetter
COPY setup.py ./
COPY hacks/gallerize-entrypoint.sh /usr/bin/

RUN pip install .

RUN useradd -u 1000 -U getbetter
USER getbetter

CMD ["gunicorn", "-b", "0.0.0.0:8000"]
