#!/bin/bash

source "$PYTHONPATH/activate" && {
    # migrate
    python ./manage.py migrate --noinput;
    python ./manage.py collectstatic --noinput;
    python ./manage.py populate_instrument;
    python ./manage.py populate_scoring;
    python ./manage.py populate_benchmark
    python ./manage.py populate_choices;
    python ./manage.py populate_items;
    python ./manage.py populate_cat_items;
}
