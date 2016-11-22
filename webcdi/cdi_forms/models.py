from django.db import models
import datetime
from django.core.exceptions import ValidationError
from django.core.validators import validate_comma_separated_integer_list,MaxValueValidator,MinValueValidator
from django.contrib.postgres.fields import ArrayField
from django import forms

class requests_log(models.Model):
    url_hash = models.CharField(max_length=128)
    request_type = models.CharField(max_length=4)
    timestamp = models.DateTimeField(auto_now = True)
    
# Create your models here.
class English_WS(models.Model):
    itemID = models.CharField(max_length = 101, primary_key=True)
    item = models.CharField(max_length = 101)
    item_type = models.CharField(max_length = 101)
    category = models.CharField(max_length = 101)
    choices = models.CharField(max_length = 101, null=True)
    definition = models.CharField(max_length = 201, null=True, blank=True)
    gloss = models.CharField(max_length = 101, null=True, blank=True)
    complexity_category = models.CharField(max_length = 101, null=True, blank=True)
    def __str__(self):
        return self.item

class English_WG(models.Model):
    itemID = models.CharField(max_length = 101, primary_key=True)
    item = models.CharField(max_length = 101)
    item_type = models.CharField(max_length = 101)
    category = models.CharField(max_length = 101)
    choices = models.CharField(max_length = 101)
    uni_lemma = models.CharField(max_length= 101, null=True, blank=True)
    definition = models.CharField(max_length = 201, null=True, blank=True)
    gloss = models.CharField(max_length = 1001, null=True, blank=True)
    complexity_category = models.CharField(max_length = 101, null=True, blank=True)
    def __str__(self):
        return self.item

def validate_g_zero(value):
        if value <= 0:
            raise ValidationError("Value should be greater than 0")

def validate_ge_zero(value):
        if value < 0:
            raise ValidationError("Value should be greater than or equal to 0")

def validate_ne_zero(value):
        if value ==  0:
            raise ValidationError("Value should be non-zero")

def format_currency(val):
    return "${:,}".format(val)

class BackgroundInfo(models.Model):
    administration = models.OneToOneField("researcher_UI.administration")
    years = [(x,str(x)) for x in range(1950, datetime.date.today().year+2)]
    years[-1] = (0, "Prefer not to disclose")
    age = models.IntegerField(verbose_name = "Age (in months)", validators=[MinValueValidator(0)], default = 999)
    sex = models.CharField(max_length = 1, choices = (('M', "Male"), ('F', "Female"), ('O', "Other")))
    birth_order = models.IntegerField(verbose_name = "Birth order (enter number e.g., 1 for first)", validators = [MinValueValidator(1, "Birth order cannot be less than 1. First born child gets value 1")], )
    birth_weight = models.FloatField(verbose_name = "Birth weight (in pounds)", validators = [validate_g_zero, MaxValueValidator(14, "Birth weight is not expected to be more than 14 pounds")],)
    #early_late = models.DateField(verbose_name = "Early or late birth", help_text = "If the child was born on due date, fill 0. If the child was born earlier than due date, fill the number of weeks after the due date as positive value. If the child was born later fill a negative value." )
    born_on_due_date = models.BooleanField(verbose_name = "Was your child born earlier or later than their due date?")
    early_or_late = models.CharField(verbose_name = "Was he/she early or late?", max_length = 5, choices = (('early', 'Early'),('late', 'Late')), blank=True, null=True)
    due_date_diff = models.IntegerField(verbose_name = "By how many weeks? (round to the nearest week)",blank=True, null=True, validators = [MinValueValidator(1, "Number of weeks cannot be less than 1")])


    education_levels = [(x,str(x)) for x in range(5,25)]
    education_levels[12-5] = (12, "12 (High school graduate)")
    education_levels[16-5] = (16, "16 (College graduate)")
    education_levels[18-5] = (18, "18 (Advanced degree)")
    education_levels[23-5] = (23, "23 or more")
    education_levels[-1] = (0, "Prefer not to disclose")
    mother_yob = models.IntegerField(verbose_name = "Mother's (or Parent 1) Year of birth", choices=years)
    mother_education = models.IntegerField(verbose_name = "Mother's (or Parent 1) Education", help_text ="Choose highest grade completed (12 = high school graduate; 16 = college graduate; 18 = advanced degree)", choices = education_levels)
    #mother_occupation = models.CharField(max_length = 101, verbose_name = "Occupation")
    #mother_hours_work = models.IntegerField(verbose_name = "Hours/week at work")

    father_yob = models.IntegerField(verbose_name = "Father's (or Parent 2) Year of birth", choices = years)
    father_education = models.IntegerField(verbose_name = "Father's (or Parent 2) Education", help_text ="Choose highest grade completed (12 = high school graduate; 16 = college graduate; 18 = advanced degree)", choices= education_levels)
    #father_occupation = models.CharField(max_length = 101, verbose_name = "Occupation")
    #father_hours_work = models.IntegerField(verbose_name = "Hours/week at work")

    low, high, inc = 25000, 200000, 25000
    income_choices = [("<" + str(low), "Under " + format_currency(low))] +\
        [("%d-%d" % (bottom, bottom + inc), "-".join([format_currency(bottom), format_currency(bottom + inc)])) for bottom in range(low, high, inc)] +\
        [(">" + str(high), "Over " + format_currency(high)), ("Prefer not to disclose", "Prefer not to disclose")]
    annual_income = models.CharField(max_length = 30, choices = income_choices, verbose_name = "Estimated Annual Family Income (in USD)")
    #annual_income = models.FloatField(verbose_name = "Estimated Annual Family Income (in USD)", validators = [validate_ge_zero])

    child_hispanic_latino = models.NullBooleanField(verbose_name = "Is your child Hispanic or Latino?", blank=True, null=True)
    child_ethnicity = ArrayField(models.CharField(max_length = 1), blank=True, null=True)

    #parent_1_hours = models.IntegerField(verbose_name = "Parent 1")
    #parent_2_hours = models.IntegerField(verbose_name = "Parent 2")
    #other = models.CharField(max_length = 20,  blank = True, verbose_name = "Other caregiver (if any)", help_text = "e.g. nanny, family provider, grandmother")
    #other_hours = models.IntegerField( blank = True, verbose_name = "Hours spend with other caregivers")
    caregiver_info = models.IntegerField(verbose_name = "Who does your child live with?", choices =((2, "Two parents"), (1, "One parent"), (3, "One parent plus other caregiver (e.g., grandparent)"), (0, "Other caregivers (e.g., grandparent or grandparents)")))

    #daycare_days_per_week = models.IntegerField( blank = True, verbose_name = "Number of days per week at daycare or preschool (if applicable)")
    #daycare_hours_per_day = models.IntegerField( blank = True, verbose_name = "Number of hours per day at daycare or preschool (if applicable)")
    #daycare_since = models.IntegerField( blank = True, verbose_name = "Since what age (in months) at daycare or preschool (if applicable)")

    #which_language = models.CharField(max_length = 20, blank = True)
    other_languages_boolean = models.BooleanField()
    other_languages = ArrayField(models.CharField(max_length = 101), blank = True, null=True)
    language_from = models.CharField(max_length = 50, blank = True, verbose_name = "From whom?", null=True)
    language_days_per_week = models.IntegerField(null=True, blank = True, verbose_name = "How many days per week is the child exposed to these languages?", validators = [MaxValueValidator(7, "Number of days per week cannot exceed 7"), MinValueValidator(1, "Number of days per week cannot be less than 1")], )
    language_hours_per_day = models.IntegerField(null=True, blank = True, verbose_name = "How many hours per day is the child exposed to these languages?", validators = [MaxValueValidator(24, "Number of hours per day cannot exceed 24"), MinValueValidator(1, "Number of hours per day cannot be less than 1")],)
    #language_since = models.IntegerField( blank = True)

    ear_infections_boolean = models.BooleanField(verbose_name = "Has your child experienced chronic ear infections (5 or more)? ")
    ear_infections = models.CharField(max_length = 1001, null=True, blank = True, verbose_name = "Has your child undergone interventions (e.g., tubes)?  Please describe")
    hearing_loss_boolean = models.BooleanField(verbose_name = 'Do you suspect that your child may have hearing loss?' )
    hearing_loss = models.CharField(max_length = 1001, blank = True, null=True,  verbose_name = 'Please describe' )
    vision_problems_boolean = models.BooleanField(verbose_name = 'Is there some reason to suspect that your child may have vision problems?' )
    vision_problems = models.CharField(max_length = 1001, blank = True, null=True, verbose_name = 'Please describe')
    illnesses_boolean = models.BooleanField(verbose_name = 'Has your child had any major illnesses, hospitalizations, or diagnosed disabilities?' )
    illnesses = models.CharField(max_length = 1001, blank = True, null=True, verbose_name = "Please describe")
    services_boolean = models.BooleanField(verbose_name = 'Has your child ever received any services for speech, language, or development issues?' )
    services = models.CharField(max_length = 1001, blank = True, null=True, verbose_name = "Please describe")
    worried_boolean = models.BooleanField(verbose_name = 'Are you worried about your child\'s progress in language or communication?' )
    worried = models.CharField(max_length = 1001, blank = True, null=True, verbose_name = "Please describe")
    learning_disability_boolean = models.BooleanField(verbose_name = 'Have you or anyone in your immediate family been diagnosed with a language or learning disability?' )
    learning_disability = models.CharField(max_length = 1001, blank = True, null=True, verbose_name = "Indicate which family member and provide a description")

    #def clean(self):
        #enabler_dependent_fields = (
        #(self.born_on_due_date, [self.early_or_late, self.due_date_diff,]),
        #(self.other_languages_boolean, [self.language_from, self.language_days_per_week, self.language_hours_per_day, self.language_fromm]),
        #(self.ear_infections_boolean, [self.ear_infections,]),
        #(self.hearing_loss_boolean, [self.hearing_loss,]),
        #(self.vision_problems_boolean, [self.vision_problems,]),
        #(self.illnesses_boolean, [self.illnesses,]),
        #(self.services_boolean, [self.services,]),
        #(self.worried_boolean, [self.worried,]),
        #(self.learning_disability_boolean , [self.learning_disability,]),)
        #errors = {}
        #for (enabler, dependents) in enabler_dependent_fields:
            #if enabler == 1:
                #for dependent in dependents:
                    #if dependent is None:
                        #errors[enabler.k


        

    
