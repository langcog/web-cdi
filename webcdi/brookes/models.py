from brookes.utils import create_brookes_code
from dateutil.relativedelta import relativedelta
from django.db import models
from researcher_UI.models import InstrumentFamily, User

# Create your models here.


class BrookesCode(models.Model):
    code = models.CharField(
        max_length=15, unique=True, primary_key=True, default=create_brookes_code
    )
    researcher = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    instrument_family = models.ForeignKey(
        InstrumentFamily, on_delete=models.SET_NULL, blank=True, null=True
    )
    applied = models.DateTimeField(blank=True, null=True)
    expiry = models.DateTimeField(blank=True, null=True)

    def __str__(self) -> str:
        return f"{self.code}"

    def save(self):
        if self.applied and not self.expiry:
            self.expiry = self.applied + relativedelta(years=1)
        return super().save()