#!/bin/bash

source "$PYTHONPATH/activate" && {
    # migrate
    python ./manage.py migrate --noinput;
    python ./manage.py collectstatic --noinput;
    python ./manage.py 01_populate_instrument_family;
    python ./manage.py 02_populate_instrument;
    python ./manage.py populate_scoring;
    python ./manage.py populate_benchmark
    python ./manage.py populate_choices;
    python ./manage.py populate_items;
}
