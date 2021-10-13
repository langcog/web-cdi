#!/bin/bash

source "$PYTHONPATH/activate" && {
    # migrate
    python ./manage.py migrate --noinput;
    python ./manage.py collectstatic --noinput;
    #python ./webcdi/manage.py populate_instrument;
    #python ./webcdi/manage.py populate_scoring;
    #python ./webcdi/manage.py populate_benchmark
    #python ./webcdi/manage.py populate_choices;
    #python ./webcdi/manage.py populate_items;
}
