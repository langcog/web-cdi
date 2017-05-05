from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator


# Create your models here.
class instrument(models.Model):
    name = models.CharField(max_length = 51, primary_key=True)
    verbose_name = models.CharField(max_length = 51, blank = True)
    language = models.CharField(max_length = 51)
    form = models.CharField(max_length = 51)
    min_age = models.IntegerField(verbose_name = "Minimum age")
    max_age = models.IntegerField(verbose_name = "Maximum age")
    def __str__(self):
        return self.verbose_name
    class Meta:
         unique_together = ('language', 'form')
    
class study(models.Model):
    researcher = models.ForeignKey("auth.user")
    name = models.CharField(max_length = 51)
    instrument = models.ForeignKey("instrument")
    waiver = models.TextField(blank = True)
    study_group = models.CharField(max_length = 51, blank = True)
    anon_collection = models.BooleanField(default=False)
    subject_cap = models.IntegerField(blank = True, null=True)
    confirm_completion = models.BooleanField(default=False)
    allow_payment = models.BooleanField(default=False)
    allow_sharing = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ('researcher', 'name')
    
def get_meta_header():
    return ['study', 'subject_id', 'administration_number', 'link', 'completed', 'completedBackgroundInfo', 'expiration_date', 'last_modified']

def get_background_header():
    return ['id', 'age', 'sex', 'birth_order', 'birth_weight', 'early_or_late', 'due_date_diff', 'mother_yob', 'mother_education', 'father_yob', 'father_education', 'annual_income', 'child_hispanic_latino', 'caregiver_info', 'other_languages_boolean', 'language_from', 'language_days_per_week', 'language_hours_per_day', 'ear_infections_boolean', 'ear_infections', 'hearing_loss_boolean', 'hearing_loss', 'vision_problems_boolean', 'vision_problems']

class administration(models.Model):
    study = models.ForeignKey("study")
    subject_id = models.IntegerField()
    repeat_num = models.IntegerField(verbose_name = "Administration number")
    url_hash = models.CharField(max_length=128, unique=True)
    completed = models.BooleanField()
    completedBackgroundInfo = models.BooleanField(default=False)
    due_date = models.DateTimeField(verbose_name = "Expiration date")
    last_modified = models.DateTimeField(auto_now = True)
    created_date = models.DateTimeField(verbose_name = "Creation date", auto_now_add = True)
    page_number = models.IntegerField(verbose_name = "Page number", default = 0)
    analysis = models.NullBooleanField(verbose_name = "Confirmed Age and Completion", default = None)
    bypass = models.NullBooleanField(verbose_name = "Willing to forgo payment", default = None)
    include = models.NullBooleanField(verbose_name = "Include for eventual analysis", default = True)

    class Meta:
        unique_together = ('study', 'subject_id', 'repeat_num')

    def get_meta_data(self):
        return [self.study, self.subject_id, self.repeat_num, self.url_hash, self.completed, self.completedBackgroundInfo, self.due_date, self.last_modified]

class administration_data(models.Model):
    administration = models.ForeignKey("administration")
    item_ID = models.CharField(max_length = 101)
    value = models.CharField(max_length=200)
    class Meta:
        unique_together = ('administration', 'item_ID')

class payment_code(models.Model):
    study = models.ForeignKey("study")
    hash_id = models.CharField(max_length=128, unique=True, null=True)
    added_date = models.DateTimeField(verbose_name = "Date code was added to database", auto_now_add = True)
    assignment_date = models.DateTimeField(verbose_name = "Date code was given to participant", null=True)
    payment_type = models.CharField(max_length=50)
    gift_amount = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Monetary value")
    gift_code = models.CharField(max_length=50)

    class Meta:
        unique_together = ('payment_type', 'gift_code')

