import datetime

from cdi_forms.scores import update_summary_scores
from django.conf import settings
from django.core.mail import EmailMessage
from django.core.management.base import BaseCommand
from django.db.models import Q
from researcher_UI.models import Administration, Study


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("-s", "--study_id", type=int)
        parser.add_argument("-l", "--language", type=str)
        parser.add_argument("-f", "--form", type=str)

    def handle(self, *args, **options):
        subject = f"WebCDI Summary Data"
        query = Q()
        if options["study_id"]:
            study_obj = Study.objects.get(pk=options["study_id"])
            query = Q(study=study_obj)
            # administrations = Administration.objects.filter(study=study_obj)
        if options["language"]:
            query = Q(query) & Q(study__instrument__language=options["language"])
        if options["form"]:
            query = Q(query) & Q(study__instrument__form=options["form"])

        administrations = Administration.objects.filter(query).filter(completed=True)
        
        '''email = EmailMessage(
            subject=subject,
            body=f"Starting at %s" % (datetime.datetime.now()),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=["hjsmehta@gmail.com"],
        )
        email.send()
        '''
        count = 0
        thousands = 0
        for instance in administrations:
            count += 1
            print(f"Processing item {count} of {len(administrations)}")
            update_summary_scores(instance)
            if count == 1000:
                thousands += 1
                email = EmailMessage(
                    subject=subject,
                    body=f"%s of %s records processed at %s"
                    % (
                        thousands * count,
                        len(administrations),
                        datetime.datetime.now(),
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=["hjsmehta@gmail.com"],
                )
                email.send()
                count = 0

        email = EmailMessage(
            subject=subject,
            body=f"COMPLETED at {datetime.datetime.now()} - {thousands * 1000 + count} Completed",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=["hjsmehta@gmail.com"],
        )
        email.send()
