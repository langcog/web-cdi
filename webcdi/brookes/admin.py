import csv
import datetime

from django.conf import settings
from django.contrib import admin, messages
from django.core.mail import EmailMessage
from rangefilter.filters import DateRangeFilter
from brookes.filters import (
    DropdownFilter
)

from brookes.models import BrookesCode
# Register your models here.


def create_50_codes(modeladmin, request, queryset):
    filename_csv = (
        f'/tmp/New Brookes Codes at {datetime.date.today().strftime("%b-%d-%Y")}.csv'
    )
    with open(filename_csv, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Code"])
        for count in range(50):
            x = BrookesCode()
            x.save()
            writer.writerow([x.code])

    email_message = EmailMessage(
        subject="New WebCDI Codes",
        body=f"Please find attached new WebCDI Codes {filename_csv}",
        to=[settings.BROOKES_EMAIL],
    )
    with open(filename_csv, "r") as csvfile:
        email_message.attach(filename_csv, csvfile.read(), "text/csv")
        email_message.send()

    messages.success(request, f"50 Codes created")


@admin.register(BrookesCode)
class BrookesCodeAdmin(admin.ModelAdmin):
    list_display = ["code", "researcher", "instrument_family", "applied", 'expiry']
    list_filter = [("applied", DateRangeFilter), ('expiry', DateRangeFilter), ("researcher", DropdownFilter), "instrument_family"]
    actions = [
        create_50_codes,
    ]
