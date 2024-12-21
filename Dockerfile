FROM python:3.12.8-slim-bullseye

ENV DJANGO_SETTINGS_MODULE acj.settings

WORKDIR /application
ADD . /application/

RUN pip3 install -r /application/requirements.txt