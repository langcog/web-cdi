import datetime

from brookes.models import BrookesCode
from dateutil.relativedelta import relativedelta
from django.core.mail import EmailMessage
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Runs weekly to send to reminders to researchers whose access expires within a month"

    def handle(self, *args, **options):
        from_date = datetime.date.today()
        to_date = datetime.date.today() + relativedelta(months=1)
        codes = BrookesCode.objects.filter(expiry__gte=from_date, expiry__lte=to_date)
        for code in codes:
            if BrookesCode.objects.filter(
                researcher=code.researcher,
                expiry__gte=to_date,
                instrument_family=code.instrument_family,
            ).exists():
                codes = codes.exclude(pk=code.pk)
        for code in codes:
            email_message = EmailMessage(
                subject=f"WebCDI {code.instrument_family} renewal is due",
<<<<<<< HEAD
                body=f"Your annual license for WebCDI {code.instrument_family} will expire on {code.expiry}.  Please renew your subscription.",
=======
                body=f"You annual license for WebCDI {code.instrument_family} will expire on {code.expiry}.  Please renew your subscription.",
>>>>>>> 13a288bb2025bd188942000aa937b989368193ab
                to=[code.researcher.email],
            )
            email_message.send()
