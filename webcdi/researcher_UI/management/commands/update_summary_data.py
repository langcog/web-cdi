from django.core.management.base import BaseCommand
from cdi_forms.scores import update_summary_scores
import datetime
from researcher_UI.models import administration

from django.conf import settings
from django.core.mail import EmailMessage

class Command(BaseCommand):

    def handle(self, *args, **options):
        email = EmailMessage(
                    subject="WebCDI Summary Data",
                    body=f'Starting at %s' % (datetime.datetime.now()),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=['hjsmehta@gmail.com'],
                )
        email.send()
        count = 0
        thousands = 0
        for instance in administration.objects.all():
            count += 1
            update_summary_scores(instance)
            if count == 3000:
                thousands += 1
                email = EmailMessage(
                    subject="WebCDI Summary Data",
                    body=f'%s of %s records processed at %s' % (thousands * count, len(administration.objects.all()), datetime.datetime.now()),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=['hjsmehta@gmail.com'],
                )
                email.send()
                count = 0
