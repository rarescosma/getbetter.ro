FROM python:3.8.2-slim

WORKDIR /pv

RUN apt-get -qq update \
    && apt-get -qq install -y git make wget rsync \
    && pip install --no-cache-dir pipenv \
    && rm -rf /var/lib/apt

RUN wget -qO- "https://github.com/mattgreen/watchexec/releases/download/1.8.6/watchexec-1.8.6-x86_64-unknown-linux-gnu.tar.gz" \
  | tar -xzf - --strip-components 1 -C /tmp/ \
  && mv /tmp/watchexec /usr/bin

COPY Pipfile* ./
RUN pipenv install --system --deploy

COPY getbetter ./
COPY setup.py ./

RUN pip install -e .

RUN useradd -u 1000 -U getbetter
USER getbetter

CMD ["gunicorn", "-b", "0.0.0.0:8000"]
