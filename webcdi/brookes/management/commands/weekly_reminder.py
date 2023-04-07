import datetime

from brookes.models import BrookesCode
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core.mail import EmailMessage
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Runs weekly to send to reminders to researchers whose access expires within a month"

    def handle(self, *args, **options):
        from_date = datetime.date.today() - relativedelta(years=1)
        to_date = (
            datetime.date.today() - relativedelta(years=1) + relativedelta(months=1)
        )
        codes = BrookesCode.objects.filter(applied__gte=from_date, applied__lte=to_date)
        for code in codes:
            email_message = EmailMessage(
                subject=f"WebCDI {code.instrument_family} renewal is due",
                body=f"You annual license for WebCDI {code.instrument_family} will expire on {code.applied + relativedelta(years=1)}.  Please renew your subscription.",
                to=[code.researcher.email],
            )
            email_message.send()
