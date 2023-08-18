from django.db import models

from researcher_UI.models import InstrumentScore

class Measure(models.Model):
    """
    Class to store the measures and their values used for scoring
    """

    instrument_score = models.ForeignKey(InstrumentScore, on_delete=models.CASCADE)
    key = models.CharField(max_length=51)
    value = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.instrument_score} {self.key}"