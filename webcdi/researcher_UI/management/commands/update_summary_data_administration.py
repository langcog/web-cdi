from django.core.management.base import BaseCommand
from cdi_forms.scores import update_summary_scores
import datetime
from researcher_UI.models import administration

from django.conf import settings
from django.core.mail import EmailMessage

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('-a', '--administration_id', type=int)

    def handle(self, *args, **options):
        print (f'Starting at %s' % (datetime.datetime.now()))

        try :
            instance = administration.objects.get(pk=options['administration_id'])
        except: 
            print(f'No valid administration id given')
            return

        update_summary_scores(instance)
        
        print (f'Completed at %s' % (datetime.datetime.now()))