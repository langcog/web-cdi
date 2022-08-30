from django.core.management.base import BaseCommand
from cdi_forms.scores import update_summary_scores
import datetime
from researcher_UI.models import administration, study

from django.conf import settings
from django.core.mail import EmailMessage

class Command(BaseCommand):

    def handle(self, *args, **options):
        study_count = 307    
        for study_obj in study.objects.all()[study_count:]:
            study_count += 1
            count = 0
            thousands = 0
            administrations = administration.objects.filter(study=study_obj)
            subject = f'{study_count} WebCDI Summary Data for {study_obj.name}'
            email = EmailMessage(
                    subject=subject,
                    body=f'Starting at %s' % (datetime.datetime.now()),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=['hjsmehta@gmail.com'],
                )
            try:
                email.send()
            except: pass
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
                    try:
                        email.send()
                    except: pass
                    count = 0

            email = EmailMessage(
                        subject=subject,
                        body=f'COMPLETED at %s' % datetime.datetime.now(),
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=['hjsmehta@gmail.com'],
                    )
            try:
                email.send()
            except: pass
        email = EmailMessage(
                        subject='COMPLETED ALL DATA SUMMARIES',
                        body=f'COMPLETED ALL DATA SUMMARIES at %s' % datetime.datetime.now(),
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=['hjsmehta@gmail.com'],
                    )
        email.send()