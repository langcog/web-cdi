FROM python:3.8-bullseye

COPY . /app

WORKDIR /app
RUN apt-get -y update
RUN apt-get -y install libcairo2-dev
RUN apt-get install gettext -y

RUN pip install -r ./webcdi/requirements.txt
