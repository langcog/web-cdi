#!/bin/bash

source "$PYTHONPATH/activate" && {
    # migrate
    python ./manage.py migrate --noinput;
    #python ./manage.py collectstatic --noinput;
    #python ./manage.py 01_populate_instrument_family;
    #python ./manage.py 02_populate_instrument;
    #python ./manage.py 03_populate_scoring;
    #python ./manage.py 04a_delete_benchmark;
    #python ./manage.py 04_populate_benchmark;
    #python ./manage.py 05_populate_choices;
    #python ./manage.py 06_populate_items;
    #python ./manage.py 07_populate_cat_items;
}
