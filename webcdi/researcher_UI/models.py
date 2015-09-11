from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class instrument(models.Model):
    name = models.CharField(max_length = 51, primary_key=True)
    def __str__(self):
        return self.name
    
class study(models.Model):
    researcher = models.ForeignKey("auth.user")
    name = models.CharField(max_length = 51)
    instrument = models.ForeignKey("instrument")
    def __str__(self):
        return self.name

    class Meta:
        unique_together = ('researcher', 'name')
    
class administration(models.Model):
    study = models.ForeignKey("study")
    subject_id = models.IntegerField()
    repeat_num = models.IntegerField()
    url_hash = models.CharField(max_length=128)
    completed = models.BooleanField()

    class Meta:
        unique_together = ('study', 'subject_id', 'repeat_num')

class administration_data(models.Model):
    administration = models.ForeignKey("administration")
    item_ID = models.CharField(max_length = 101)
    value = models.CharField(max_length=101)
    class Meta:
        unique_together = ('administration', 'item_ID')


