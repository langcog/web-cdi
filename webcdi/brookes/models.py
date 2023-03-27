from brookes.utils import create_brookes_code
from django.db import models
from researcher_UI.models import User, instrument

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
    instrument = models.ForeignKey(
        instrument, on_delete=models.SET_NULL, blank=True, null=True
    )
    applied = models.DateTimeField(blank=True, null=True)

    def __str__(self) -> str:
        return f"{self.code}"
