#!/bin/bash

source "$PYTHONPATH/activate" && {
    # migrate
    python ./webcdi/manage.py migrate --noinput;
    python ./webcdi/manage.py collectstatic --noinput;
    python ./webcdi/manage.py createsu;
    python ./webcdi/manage.py populate_instrument;
    python ./webcdi/manage.py populate_scoring;
    python ./webcdi/manage.py populate_benchmark
    python ./webcdi/manage.py populate_choices;
    python ./webcdi/manage.py populate_items;
    python ./webcdi/manage.py populate_cat_items;
}
