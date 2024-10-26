import os

import pandas as pd
from cdi_forms.models import Choices
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        PROJECT_ROOT = settings.BASE_DIR
        choices_csv_path = os.path.realpath(
            PROJECT_ROOT + "/cdi_form_csv/choice_options.csv"
        )

        choices_data = pd.read_csv(choices_csv_path, sep=",").fillna("")
        choice_fields = [f.name for f in Choices._meta.get_fields()]

        for index, row in choices_data.iterrows():
            data_dict = dict(row)
            sub_dict = {
                k: data_dict.get(k, None)
                for k in set.intersection(set(data_dict.keys()), set(choice_fields))
            }
            sub_dict.pop("choice_set", None)
            Choices.objects.update_or_create(
                choice_set=row["choice_set"], defaults=sub_dict
            )
