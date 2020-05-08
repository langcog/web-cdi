from django.core.management.base import BaseCommand
from cdi_forms.scores import update_summary_scores
import datetime
from researcher_UI.models import administration, study
from django.db.models import Q
from django.conf import settings
from django.core.mail import EmailMessage

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('-s', '--study_id', type=int)
        parser.add_argument('-l', '--language', type=str)

    def handle(self, *args, **options):
        subject = f'WebCDI Summary Data'
        query = Q()
        if options['study_id']:
            study_obj = study.objects.get(pk=options['study_id'])
            query = Q(study=study_obj)
            administrations = administration.objects.filter(study=study_obj)
        if options['language']:
            query = Q(query) & Q(study__instrument__language=options['language']) 

        administrations = administration.objects.filter(query)
        
        email = EmailMessage(
                    subject=subject,
                    body=f'Starting at %s' % (datetime.datetime.now()),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=['hjsmehta@gmail.com'],
                )
        email.send()
        count = 0
        thousands = 0
        for instance in administrations:
            count += 1
            update_summary_scores(instance)
            if count == 1000:
                thousands += 1
                email = EmailMessage(
                    subject=subject,
                    body=f'%s of %s records processed at %s' % (thousands * count, len(administrations), datetime.datetime.now()),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=['hjsmehta@gmail.com'],
                )
                email.send()
                count = 0

        email = EmailMessage(
                    subject=subject,
                    body=f'COMPLETED at {datetime.datetime.now()} - {thousands * 1000 + count} Completed',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=['hjsmehta@gmail.com'],
                )
        email.send()