from django.core.management.base import BaseCommand
from cdi_forms.scores import update_summary_scores
import datetime
from researcher_UI.models import administration

class Command(BaseCommand):

    def handle(self, *args, **options):
        print (f'Starting at %s' % (datetime.datetime.now()))
        count = 0
        thousands = 0
        for instance in administration.objects.filter(study__name="norming_wg_11_19"):
            count += 1
            update_summary_scores(instance)
            if count == 3000:
                thousands += 1
                print (f'%s of %s records processed at %s' % (thousands * count, len(administration.objects.all()), datetime.datetime.now()))
                count = 0
