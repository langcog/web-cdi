from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class instrument(models.Model):
    name = models.CharField(max_length = 51, primary_key=True)
    verbose_name = models.CharField(max_length = 51, blank = True)
    def __str__(self):
        return self.verbose_name
    
class study(models.Model):
    researcher = models.ForeignKey("auth.user")
    name = models.CharField(max_length = 51)
    instrument = models.ForeignKey("instrument")
    def __str__(self):
        return self.name

    class Meta:
        unique_together = ('researcher', 'name')
    
def get_meta_header():
    return ['study', 'subject_id', 'administration_number', 'link', 'completed', 'expiration_date', 'last_modified']
class administration(models.Model):
    study = models.ForeignKey("study")
    subject_id = models.IntegerField()
    repeat_num = models.IntegerField(verbose_name = "Administration number")
    url_hash = models.CharField(max_length=128, unique=True)
    completed = models.BooleanField()
    completedBackgroundInfo = models.BooleanField(default=False)
    due_date = models.DateTimeField(verbose_name = "Expiration date")
    last_modified = models.DateTimeField(auto_now = True)

    class Meta:
        unique_together = ('study', 'subject_id', 'repeat_num')

    def get_meta_data(self):
        return [self.study, self.subject_id, self.repeat_num, self.url_hash, self.completed, self.due_date, self.last_modified]

class administration_data(models.Model):
    administration = models.ForeignKey("administration")
    item_ID = models.CharField(max_length = 101)
    value = models.CharField(max_length=200)
    class Meta:
        unique_together = ('administration', 'item_ID')


