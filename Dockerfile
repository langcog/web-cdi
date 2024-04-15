FROM python:3.11-slim

COPY . /app

WORKDIR /app
RUN pip install --upgrade pip
RUN apt clean
RUN apt-get -y update
RUN apt-get -y install gcc
RUN apt-get install -y libpangocairo-1.0-0
RUN apt-get install gettext -y

RUN pip install -r ./webcdi/requirements.txt
RUN pip install -r ./webcdi/requirements_test.txt

# install selenlium for tests
RUN pip install selenium