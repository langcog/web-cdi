from django.db import models

from researcher_UI.models import Administration


class SummaryData(models.Model):
    """
    Class to store the administrations summary scores for the instrument scoring mechanisms loaded from json files held in
    /cdi_forms/form_data/scoring/
    """

    administration = models.ForeignKey(Administration, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    value = models.CharField(max_length=255)

    def __str__(self):
        return f"%s: %s" % (self.administration, self.title)

    class Meta:
        unique_together = ("administration", "title")
        ordering = ["administration"]
