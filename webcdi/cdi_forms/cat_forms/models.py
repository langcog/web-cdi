from django.db import models
from django.contrib.postgres.fields import ArrayField

# Create your models here.

'''
class InstrumentItem(models.Model):
    instrument = models.ForeignKey('researcher_UI.instrument', db_index=True, on_delete=models.CASCADE)
    definition = models.CharField(max_length = 1001, null=True, blank=True) # item listed in plaintext. This is what is displayed to test-takers along with possible choices
    discrimination = models.FloatField()
    difficulty = models.FloatField()
    guessing = models.FloatField()
    upper_asymptote = models.FloatField()
    
    def __str__(self):
        return f"%s (%s)" % (self.definition, self.instrument.verbose_name)
    
    class Meta:
        unique_together = ('instrument', 'definition') # Each instrument in the database must have a unique combination of instrument and itemID
        ordering = ['definition']
'''
class CatResponse(models.Model):
    administration = models.OneToOneField('researcher_UI.administration', db_index=True, on_delete=models.CASCADE)
    administered_words = ArrayField(models.CharField(max_length=101), null=True)
    administered_items = ArrayField(models.IntegerField(), null=True)
    administered_responses = ArrayField(models.BooleanField(), null=True)
    est_theta = models.FloatField(null=True)

    def __str__(self):
        return self.administration
'''
class CatStartingWord(models.Model):
    instrument = models.ForeignKey('researcher_UI.instrument', db_index=True, on_delete=models.CASCADE)
    instrument_item = models.ForeignKey(InstrumentItem, db_index=True, on_delete=models.CASCADE)
    age = models.IntegerField()

    def __str__(self):
        return f'{self.instrument.name} {self.age} {self.instrument_item.definition}'

    class Meta:
        unique_together = ('instrument', 'age') # Each instrument in the database must have a unique combination of instrument and age
        ordering = ['instrument','age']
'''