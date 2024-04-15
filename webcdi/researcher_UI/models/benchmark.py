from django.db import models


class Benchmark(models.Model):
    """
    Class to store benchmark data for each instrument and score.
    Data is loaded from csv files held in /cdi_forms/form_data/benchmarking/
    """

    instrument = models.ForeignKey("Instrument", on_delete=models.CASCADE)
    instrument_score = models.ForeignKey("InstrumentScore", on_delete=models.CASCADE)
    percentile = models.IntegerField()
    age = models.IntegerField()
    raw_score = models.FloatField()
    raw_score_boy = models.FloatField()
    raw_score_girl = models.FloatField()

    def __str__(self):
        return f"{self.instrument_score} {self.percentile} {self.age}"

    class Meta:
        ordering = ["instrument_score", "age", "percentile"]
