from django.db import models


class InstrumentFamily(models.Model):
    name = models.CharField(max_length=51)
    chargeable = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name}"

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Instrument Families"
