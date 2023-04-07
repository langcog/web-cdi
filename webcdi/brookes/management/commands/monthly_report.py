import csv
import datetime

from brookes.models import BrookesCode
from django.conf import settings
from django.core.mail import EmailMessage
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Sends monthly report to settings.BROOKES_EMAIL"
    to_email = settings.BROOKES_EMAIL

    def handle(self, *args, **options):
        codes = BrookesCode.objects.all()
        filename_csv = (
            f'/tmp/Brookes Codes as of {datetime.date.today().strftime("%b-%d-%Y")}.csv'
        )
        with open(filename_csv, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(
                [
                    "Code",
                    "Researcher",
                    "Created",
                    "Modified",
                    "Instrument Family",
                    "Applied",
                ]
            )
            for code in codes:
                writer.writerow(
                    [
                        code.code,
                        code.researcher,
                        code.created,
                        code.modified,
                        code.instrument_family,
                        code.applied,
                    ]
                )

        email_message = EmailMessage(
            subject="WebCDI Monthly Report",
            body=f"Please find attached monthly report {filename_csv}",
            to=[self.to_email],
        )
        with open(filename_csv, "r") as csvfile:
            email_message.attach(filename_csv, csvfile.read(), "text/csv")
            email_message.send()
