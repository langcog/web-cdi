from django.db import models

class Demographic(models.Model):
    """
    Class to store the different Demographic Form (Background Info) that can be used by Studies
    """

    name = models.CharField(max_length=30)
    path = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name}"