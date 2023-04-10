from django.db import models
from .instrument_family import InstrumentFamily

# Model for individual instruments
class instrument(models.Model):
    name = models.CharField(max_length=51, primary_key=True)  # Instrument short name
    verbose_name = models.CharField(
        max_length=51, blank=True
    )  # Instrument official title
    language = models.CharField(
        max_length=51
    )  # Instrument's language. For 'English Words & Sentences' this would be 'English'
    form = models.CharField(
        max_length=51
    )  # Instrument's form type abbreviation. For 'English Words & Sentences' this would be 'WS'
    min_age = models.IntegerField(
        verbose_name="Minimum age"
    )  # Minimum age in months that instrument was built for
    max_age = models.IntegerField(
        verbose_name="Maximum age"
    )  # Maximum age in months that instrument was built for
    demographics = models.ManyToManyField("Demographic")
    active = models.BooleanField(default=True)
    family = models.ForeignKey(InstrumentFamily, on_delete=models.SET_NULL, null=True, blank=True)

    def __unicode__(self):
        return "%s (%s %s)" % (self.verbose_name, self.language, self.form)

    def __str__(self):
        return f"%s" % (self.verbose_name)

    class Meta:
        unique_together = (
            "language",
            "form",
        )  # Each instrument in the database must have a unique combination of language and form type
        ordering = ["verbose_name"]

    @property
    def item_count(self):
        from cdi_forms.models import Instrument_Forms
        return Instrument_Forms.objects.filter(instrument=self).count()