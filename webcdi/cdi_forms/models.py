from django.db import models
import datetime
from django.core.exceptions import ValidationError
from django.core.validators import validate_comma_separated_integer_list,MaxValueValidator,MinValueValidator,RegexValidator
from django.contrib.postgres.fields import ArrayField
from django import forms

class requests_log(models.Model):
    url_hash = models.CharField(max_length=128)
    request_type = models.CharField(max_length=4)
    timestamp = models.DateTimeField(auto_now = True)
    
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
    zip_code = models.CharField(max_length = 5, verbose_name = 'Zip Code (if you live in the U.S.)', blank = True, null=True, validators=[RegexValidator(regex='^\d{5}$', message='Please enter a valid U.S. zip code')])


    birth_order_choices = [
        (1, "1 (First)"),
        (2, "2 (Second)"),
        (3, "3 (Third)"),
        (4, "4 (Fourth)"),
        (5, "5 (Fifth)"),
        (6, "6 (Sixth)"),
        (7, "7 (Seventh)"),
        (8, "8 (Eighth)"),
        (9, "9 (Ninth)"),
        (10, "10 or more (Tenth or Later)"),
        (0, "Prefer not to disclose")

    ]

    birth_weight_choices = [
        (1.0, "Less than 3 lbs, 0 oz"),
        (3.0, "3 lbs, 0 oz - 3 lbs, 7 oz"),
        (3.5, "3 lbs, 8 oz - 3 lbs, 15 oz"),
        (4.0, "4 lbs, 0 oz - 4 lbs, 7 oz"),
        (4.5, "4 lbs, 8 oz - 4 lbs, 15 oz"),
        (5.0, "5 lbs, 0 oz - 5 lbs, 7 oz"),
        (5.5, "5 lbs, 8 oz - 5 lbs, 15 oz"),
        (6.0, "6 lbs, 0 oz - 6 lbs, 7 oz"),
        (6.5, "6 lbs, 8 oz - 6 lbs, 15 oz"),
        (7.0, "7 lbs, 0 oz - 7 lbs, 7 oz"),
        (7.5, "7 lbs, 8 oz - 7 lbs, 15 oz"),
        (8.0, "8 lbs, 0 oz - 8 lbs, 7 oz"),
        (8.5, "8 lbs, 8 oz - 8 lbs, 15 oz"),
        (9.0, "9 lbs, 0 oz - 9 lbs, 7 oz"),
        (9.5, "9 lbs, 8 oz - 9 lbs, 15 oz"),
        (10.0, "10 lbs, 0 oz or more"),
        (0.0, "Prefer not to disclose")

    ]

    birth_order = models.IntegerField(verbose_name = "Birth order", choices = birth_order_choices)

    multi_birth_choices = [
        (2, "Twins"),
        (3, "Triplets"),
        (4, "Quadruplets"),
        (5, "Quintuplets or greater"),
    ]

    multi_birth_boolean = models.IntegerField(verbose_name = "Was your child born as part of a multiple birth?")
    multi_birth = models.IntegerField(verbose_name = "Twins, triplets, quadruplets, other?", choices = multi_birth_choices, blank=True, null=True)

    birth_weight = models.FloatField(verbose_name = "Birth weight", choices = birth_weight_choices)
    born_on_due_date = models.IntegerField(verbose_name = "Was your child born earlier or later than their due date?")
    early_or_late = models.CharField(verbose_name = "Was he/she early or late?", max_length = 5, choices = (('early', 'Early'),('late', 'Late')), blank=True, null=True)
    due_date_diff = models.IntegerField(verbose_name = "By how many weeks? (round to the nearest week)",blank=True, null=True, validators = [MinValueValidator(1, "Number of weeks cannot be less than 1")])


    education_levels = [(x,str(x)) for x in range(5,25)]
    education_levels[12-5] = (12, "12 (High school graduate)")
    education_levels[16-5] = (16, "16 (College graduate)")
    education_levels[18-5] = (18, "18 (Advanced degree)")
    education_levels[23-5] = (23, "23 or more")
    education_levels[-1] = (0, "Prefer not to disclose")
    mother_yob = models.IntegerField(verbose_name = "Mother / Parent or Guardian 1 Year of birth", choices=years)
    mother_education = models.IntegerField(verbose_name = "Mother / Parent or Guardian 1 Education", help_text ="Choose highest grade completed (12 = high school graduate; 16 = college graduate; 18 = advanced degree)", choices = education_levels)

    father_yob = models.IntegerField(verbose_name = "Father / Parent or Guardian 2 Year of birth", choices = years)
    father_education = models.IntegerField(verbose_name = "Father / Parent or Guardian 2 Education", help_text ="Choose highest grade completed (12 = high school graduate; 16 = college graduate; 18 = advanced degree)", choices= education_levels)

    low, high, inc = 25000, 200000, 25000
    income_choices = [("<" + str(low), "Under " + format_currency(low))] +\
        [("%d-%d" % (bottom, bottom + inc), "-".join([format_currency(bottom), format_currency(bottom + inc)])) for bottom in range(low, high, inc)] +\
        [(">" + str(high), "Over " + format_currency(high)), ("Prefer not to disclose", "Prefer not to disclose")]
    annual_income = models.CharField(max_length = 30, choices = income_choices, verbose_name = "Estimated Annual Family Income (in USD)")

    child_hispanic_latino = models.NullBooleanField(verbose_name = "Is your child Hispanic or Latino?", blank=True, null=True)
    child_ethnicity = ArrayField(models.CharField(max_length = 1), blank=True, null=True)

    caregivers_choices = ((2, "Two parents"), (1, "One parent"), (3, "One parent plus other caregiver (e.g., grandparent)"), (4, "Other caregivers (e.g., grandparent or grandparents)"), (0, "Prefer not to disclose"))
    caregiver_info = models.IntegerField(verbose_name = "Who does your child live with?", choices = caregivers_choices)

    other_languages_boolean = models.IntegerField()
    other_languages = ArrayField(models.CharField(max_length = 101), blank = True, null=True)
    language_from = models.CharField(max_length = 50, blank = True, verbose_name = "From whom?", null=True)
    language_days_per_week = models.IntegerField(null=True, blank = True, verbose_name = "How many days per week is the child exposed to these languages?", validators = [MaxValueValidator(7, "Number of days per week cannot exceed 7"), MinValueValidator(1, "Number of days per week cannot be less than 1")], )
    language_hours_per_day = models.IntegerField(null=True, blank = True, verbose_name = "How many hours per day is the child exposed to these languages?", validators = [MaxValueValidator(24, "Number of hours per day cannot exceed 24"), MinValueValidator(1, "Number of hours per day cannot be less than 1")],)

    ear_infections_boolean = models.IntegerField(verbose_name = "Has your child experienced chronic ear infections (5 or more)? ")
    ear_infections = models.CharField(max_length = 1001, null=True, blank = True, verbose_name = "Has your child undergone interventions (e.g., tubes)?  Please describe")
    hearing_loss_boolean = models.IntegerField(verbose_name = 'Do you suspect that your child may have hearing loss?' )
    hearing_loss = models.CharField(max_length = 1001, blank = True, null=True,  verbose_name = 'Please describe' )
    vision_problems_boolean = models.IntegerField(verbose_name = 'Is there some reason to suspect that your child may have vision problems?' )
    vision_problems = models.CharField(max_length = 1001, blank = True, null=True, verbose_name = 'Please describe')
    illnesses_boolean = models.IntegerField(verbose_name = 'Has your child had any major illnesses, hospitalizations, or diagnosed disabilities?' )
    illnesses = models.CharField(max_length = 1001, blank = True, null=True, verbose_name = "Please describe")
    services_boolean = models.IntegerField(verbose_name = 'Has your child ever received any services for speech, language, or development issues?' )
    services = models.CharField(max_length = 1001, blank = True, null=True, verbose_name = "Please describe")
    worried_boolean = models.IntegerField(verbose_name = 'Are you worried about your child\'s progress in language or communication?' )
    worried = models.CharField(max_length = 1001, blank = True, null=True, verbose_name = "Please describe")
    learning_disability_boolean = models.IntegerField(verbose_name = 'Have you or anyone in your immediate family been diagnosed with a language or learning disability?' )
    learning_disability = models.CharField(max_length = 1001, blank = True, null=True, verbose_name = "Indicate which family member and provide a description")


        

    
