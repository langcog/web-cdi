from django.db import models

from django.contrib.auth.models import User

from .instrument import instrument
from .instrument_family import InstrumentFamily

class researcher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    institution = models.CharField(
        verbose_name="Name of Institution", max_length=101
    )  # Name of research institution they are affiliated with
    position = models.CharField(
        verbose_name="Position in Institution", max_length=101
    )  # Title of position within research institution
    allowed_instruments = models.ManyToManyField(
        instrument, verbose_name="Instruments this researcher has access to", blank=True
    )
    allowed_instrument_families = models.ManyToManyField(
        InstrumentFamily,
        verbose_name="Instrument Families this researcher has access to", 
        blank=True
    )

    def __str__(self):
        return f"%s %s (%s, %s)" % (
            self.user.first_name,
            self.user.last_name,
            self.position,
            self.institution,
        )

   