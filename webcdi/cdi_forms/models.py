from django.db import models

# Create your models here.
class English_WS(models.Model):
    itemID = models.CharField(max_length = 101, primary_key=True)
    item = models.CharField(max_length = 101)
    item_type = models.CharField(max_length = 101)
    category = models.CharField(max_length = 101)
    choices = models.CharField(max_length = 101)
    definition = models.CharField(max_length = 201)
    gloss = models.CharField(max_length = 101)
    complexity_category = models.CharField(max_length = 101)
