from django.db import models

from researcher_UI.models import Instrument

KIND_OPTIONS = (("count", "count"), ("list", "list"))


class InstrumentScore(models.Model):
    """
    Class to store the instrument scoring mechanisms loaded from json files held in
    /cdi_forms/form_data/scoring/
    """

    instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE)
    title = models.CharField(max_length=101)
    category = models.CharField(max_length=101)
    scoring_measures = models.CharField(max_length=101)
    order = models.IntegerField(default=999)
    kind = models.CharField(max_length=5, default="count", choices=KIND_OPTIONS)

    def __str__(self):
        return f"%s: %s" % (self.instrument, self.title)

    class Meta:
        ordering = ["instrument", "order"]
