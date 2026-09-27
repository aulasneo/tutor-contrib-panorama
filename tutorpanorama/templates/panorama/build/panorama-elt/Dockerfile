FROM python:3.12-slim-bookworm
LABEL Maintainer="andres@aulasneo.com"

RUN mkdir /config

# Install cron
RUN apt-get update && apt-get install -y --no-install-recommends cron git \
    && rm -rf /var/lib/apt/lists/*

RUN git clone {{ PANORAMA_ELT_REPO }} /panorama-elt \
    && git -C /panorama-elt checkout {{ PANORAMA_ELT_VERSION }}

WORKDIR /panorama-elt
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir --no-deps . \
    && pip check

RUN touch /etc/cron.d/crontab
