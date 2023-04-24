from django.contrib.postgres.fields import ArrayField
from django.db import models

# Create your models here.


class CatResponse(models.Model):
    administration = models.OneToOneField(
        "researcher_UI.administration", db_index=True, on_delete=models.CASCADE
    )
    administered_words = ArrayField(models.CharField(max_length=101), null=True)
    administered_items = ArrayField(models.IntegerField(), null=True)
    administered_responses = ArrayField(models.BooleanField(), null=True)
    est_theta = models.FloatField(null=True)

    def __str__(self):
        return self.administration
