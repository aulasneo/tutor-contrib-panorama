FROM python:3.11-slim-bookworm
LABEL Maintainer="andres@aulasneo.com"

RUN mkdir config

# Install cron
RUN apt-get update
RUN apt-get install -y cron git

RUN git clone https://github.com/aulasneo/panorama-elt.git --branch {{ PANORAMA_ELT_VERSION }}

RUN pip install -r /panorama-elt/requirements.txt

RUN touch /etc/cron.d/crontab
