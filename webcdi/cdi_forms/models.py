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

#Model for English Words & Sentences form. Each row represents another item in the CDI questionnaire and its descriptive variables     
class English_WS(models.Model):
    itemID = models.CharField(max_length = 101, primary_key=True) # ID number for identification
    item = models.CharField(max_length = 101) # string variable name
    item_type = models.CharField(max_length = 101) # type of variable (word, phrase, etc.)
    category = models.CharField(max_length = 101) # if word, the subcategory for item (animals, sounds, etc.)
    choices = models.CharField(max_length = 101, null=True) # possible positive choices for item
    definition = models.CharField(max_length = 1001, null=True, blank=True) # item listed in plaintext. This is what is displayed to test-takers along with possible choices
    gloss = models.CharField(max_length = 1001, null=True, blank=True) # English translation for item. At the moment, we only have English instruments so definition and gloss are identical
    complexity_category = models.CharField(max_length = 101, null=True, blank=True) # category for complexity item. Currently blank.
    def __str__(self):
        return self.item
#Model for English Words & Gestures form. Each row represents another item in the CDI questionnaire and its descriptive variables  
class English_WG(models.Model):
    itemID = models.CharField(max_length = 101, primary_key=True) # ID number for identification
    item = models.CharField(max_length = 101) # string variable name
    item_type = models.CharField(max_length = 101) # type of variable (word, phrase, etc.)
    category = models.CharField(max_length = 101) # if word, the subcategory for item (animals, sounds, etc.)
    choices = models.CharField(max_length = 101) # possible positive choices for item
    uni_lemma = models.CharField(max_length= 101, null=True, blank=True) # ID for matching terms across languages. Currently unused.
    definition = models.CharField(max_length = 1001, null=True, blank=True) # item listed in plaintext. This is what is displayed to test-takers along with possible choices
    gloss = models.CharField(max_length = 1001, null=True, blank=True) # English translation for item. At the moment, we only have English instruments so definition and gloss are identical
    complexity_category = models.CharField(max_length = 101, null=True, blank=True) # category for complexity item. Currently blank.
    def __str__(self):
        return self.item

#Model for Spanish Words & Sentences form. Each row represents another item in the CDI questionnaire and its descriptive variables     
class Spanish_WS(models.Model):
    itemID = models.CharField(max_length = 101, primary_key=True) # ID number for identification
    item = models.CharField(max_length = 101) # string variable name
    item_type = models.CharField(max_length = 101) # type of variable (word, phrase, etc.)
    category = models.CharField(max_length = 101) # if word, the subcategory for item (animals, sounds, etc.)
    choices = models.CharField(max_length = 101, null=True) # possible positive choices for item
    definition = models.CharField(max_length = 1001, null=True, blank=True) # item listed in plaintext. This is what is displayed to test-takers along with possible choices
    uni_lemma = models.CharField(max_length= 101, null=True, blank=True) # ID for matching terms across languages. Currently unused.
    gloss = models.CharField(max_length = 1001, null=True, blank=True) # English translation for item. At the moment, we only have English instruments so definition and gloss are identical
    complexity_category = models.CharField(max_length = 101, null=True, blank=True) # category for complexity item. Currently blank.
    def __str__(self):
        return self.item
#Model for Spanish Words & Gestures form. Each row represents another item in the CDI questionnaire and its descriptive variables     
class Spanish_WG(models.Model):
    itemID = models.CharField(max_length = 101, primary_key=True) # ID number for identification
    item = models.CharField(max_length = 101) # string variable name
    item_type = models.CharField(max_length = 101) # type of variable (word, phrase, etc.)
    category = models.CharField(max_length = 101) # if word, the subcategory for item (animals, sounds, etc.)
    choices = models.CharField(max_length = 101, null=True) # possible positive choices for item
    definition = models.CharField(max_length = 1001, null=True, blank=True) # item listed in plaintext. This is what is displayed to test-takers along with possible choices
    uni_lemma = models.CharField(max_length= 101, null=True, blank=True) # ID for matching terms across languages. Currently unused.
    gloss = models.CharField(max_length = 1001, null=True, blank=True) # English translation for item. At the moment, we only have English instruments so definition and gloss are identical
    complexity_category = models.CharField(max_length = 101, null=True, blank=True) # category for complexity item. Currently blank.
    def __str__(self):
        return self.item

# Method for ensuring that a value is positive
def validate_g_zero(value):
        if value <= 0:
            raise ValidationError("Value should be greater than 0")

# Method for ensuring that a value is not negative
def validate_ge_zero(value):
        if value < 0:
            raise ValidationError("Value should be greater than or equal to 0")

# Method for ensuring that a value is not zero
def validate_ne_zero(value):
        if value ==  0:
            raise ValidationError("Value should be non-zero")

#Method for formatting integers according to U.S. currency formats.
def format_currency(val):
    return "${:,}".format(val)

#Model for storing demographic variables associated with a subject.
class BackgroundInfo(models.Model):
    administration = models.OneToOneField("researcher_UI.administration") # Administration ID# unique to the entire database
    age = models.IntegerField(verbose_name = "Age (in months)", validators=[MinValueValidator(0)], default = 999) #age in months for child (views.py converts DOB field in forms.py into age for this model)
    sex = models.CharField(max_length = 1, choices = (('M', "Male"), ('F', "Female"), ('O', "Other"))) # Reported gender for child
    zip_code = models.CharField(max_length = 5, verbose_name = 'Zip Code (if you live in the U.S.)', blank = True, null=True, validators=[RegexValidator(regex='^(\d{3}([*]{2})?)|([A-Z]{2})$', message='Please enter a valid U.S. zip code')]) # Reported zip code for family. Follows Safe Harbor guidelines. Stores first 3 digits of zip code or state abbreviation.

    #Declared set of choices for birth order. Displays text version of integer ("First" instead of 1)
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

    birth_order = models.IntegerField(verbose_name = "Birth order", choices = birth_order_choices) # Birth order for child

    #Declared set of options for subjects born in a multiple birth
    multi_birth_choices = [
        (2, "Twins"),
        (3, "Triplets"),
        (4, "Quadruplets"),
        (5, "Quintuplets or greater"),
    ]

    multi_birth_boolean = models.IntegerField(verbose_name = "Was your child born as part of a multiple birth?") # Boolean for multiple birth
    multi_birth = models.IntegerField(verbose_name = "Twins, triplets, quadruplets, other?", choices = multi_birth_choices, blank=True, null=True) # Elaboration on circumstances for subjects born in a multiple birth (twins, triplets, etc.)

    #Declared set of birthweight choices (in lb and oz). Displays intervals instead of birthweight rounded down to nearest 0.5 lb
    birth_weight_lb_choices = [
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

    #Declared set of birthweight choices (in lb and oz). Displays intervals instead of birthweight rounded down to nearest 0.5 lb
    birth_weight_kg_choices = [
        (1.00, "Less than 1500 grams"),
        (1.50, "1500 grams - 1749 grams"),
        (1.75, "1750 grams - 1999 grams"),
        (2.00, "2000 grams - 2249 grams"),
        (2.25, "2250 grams - 2499 grams"),
        (2.50, "2500 grams - 2749 grams"),
        (2.75, "2750 grams - 2999 grams"),
        (3.00, "3000 grams - 3249 grams"),
        (3.25, "3250 grams - 3499 grams"),
        (3.50, "3500 grams - 3749 grams"),
        (3.75, "3750 grams - 3999 grams"),
        (4.00, "4000 grams - 4249 grams"),
        (4.25, "4250 grams - 4499 grams"),
        (4.50, "4500 grams - 4749 grams"),
        (4.75, "4750 grams - 4999 grams"),
        (5.00, "5000 grams or more"),
        (0.00, "Prefer not to disclose")

    ]

    birth_weight_lb = models.FloatField(verbose_name = "Birth weight", choices = birth_weight_lb_choices, blank=True, null=True) # Declared birthweight for subject (in lb and oz)
    birth_weight_kg = models.FloatField(verbose_name = "Birth weight", choices = birth_weight_kg_choices, blank=True, null=True) # Declared birthweight for subject


    born_on_due_date = models.IntegerField(verbose_name = "Was your child born earlier or later than their due date?") # Boolean for whether child was born on due date
    early_or_late = models.CharField(verbose_name = "Was he/she early or late?", max_length = 5, choices = (('early', 'Early'),('late', 'Late')), blank=True, null=True) # Determines if child was born earlier or later than due date
    due_date_diff = models.IntegerField(verbose_name = "By how many weeks? (round to the nearest week)",blank=True, null=True, validators = [MinValueValidator(1, "Number of weeks cannot be less than 1")]) # Determines # of weeks between DOB and due date

    education_levels = [(x,str(x)) for x in range(5,25)] #Declares tuple of integers for # of years of education

    # Appends additional text descriptions for years of education w/ milestones (high school diploma, bachelor's degree, and master's degree)
    education_levels[12-5] = (12, "12 (High school graduate)")
    education_levels[16-5] = (16, "16 (College graduate)")
    education_levels[18-5] = (18, "18 (Advanced degree)")
    education_levels[23-5] = (23, "23 or more")
    education_levels[-1] = (0, "Prefer not to disclose")

    years = [(x,str(x)) for x in range(1950, datetime.date.today().year+2)] #Declares tuple for year of birth for parents/guardians
    years[-1] = (0, "Prefer not to disclose")

    mother_yob = models.IntegerField(verbose_name = "Mother / Parent or Guardian 1 Year of birth", choices=years) # Asks for year of birth for mother. Can be used to roughly determine maternal age
    mother_education = models.IntegerField(verbose_name = "Mother / Parent or Guardian 1 Education", help_text ="Choose highest grade completed (12 = high school graduate; 16 = college graduate; 18 = advanced degree)", choices = education_levels) # Asks for # of years of maternal education

    father_yob = models.IntegerField(verbose_name = "Father / Parent or Guardian 2 Year of birth", choices = years) # Asks for year of birth for father. Can be used to roughly determine paternal age
    father_education = models.IntegerField(verbose_name = "Father / Parent or Guardian 2 Education", help_text ="Choose highest grade completed (12 = high school graduate; 16 = college graduate; 18 = advanced degree)", choices= education_levels) # Asks for # of years of paternal education

    low, high, inc = 25000, 200000, 25000 # Declares range of values and step interval for annual income question
    income_choices = [("<" + str(low), "Under " + format_currency(low))] +\
        [("%d-%d" % (bottom, bottom + inc), "-".join([format_currency(bottom), format_currency(bottom + inc)])) for bottom in range(low, high, inc)] +\
        [(">" + str(high), "Over " + format_currency(high)), ("Prefer not to disclose", "Prefer not to disclose")] # Declares set of choices for annual_income that span from under $25,000 to over $200,000 in $25,000 intervals
    annual_income = models.CharField(max_length = 30, choices = income_choices, verbose_name = "Estimated Annual Family Income (in USD)") # Asks for bracket of annual income

    child_hispanic_latino = models.NullBooleanField(verbose_name = "Is your child Hispanic or Latino?", blank=True, null=True) # Asks whether child is hispanic/latino
    child_ethnicity = ArrayField(models.CharField(max_length = 1), blank=True, null=True) # Asks for child's ethnicity according to NIH ethnicity categories. Can check multiple answers.

    #Declares possible choices for child's family situation (# of caregivers, parents, grandparents, etc.)
    caregivers_choices = [
        (2, "Two parents"), 
        (1, "One parent"), 
        (3, "One parent plus other caregiver (e.g., grandparent)"), 
        (4, "Other caregivers (e.g., grandparent or grandparents)"), 
        (0, "Prefer not to disclose")
    ]

    caregiver_info = models.IntegerField(verbose_name = "Who does your child live with?", choices = caregivers_choices) # Asks for child's family situation

    other_languages_boolean = models.IntegerField() #Asks whether child is regularly exposed to other languages besides the instrument's language (currently English)
    other_languages = ArrayField(models.CharField(max_length = 101), blank = True, null=True) # Lists possible languages from languages.json that child may be exposed to
    language_from = models.CharField(max_length = 50, blank = True, verbose_name = "From whom?", null=True) # Free text response that asks who child hears other languages from
    language_days_per_week = models.IntegerField(null=True, blank = True, verbose_name = "How many days per week is the child exposed to these languages?", validators = [MaxValueValidator(7, "Number of days per week cannot exceed 7"), MinValueValidator(1, "Number of days per week cannot be less than 1")], ) # Asks to quantify the # of days in a week that child is exposed to another language
    language_hours_per_day = models.IntegerField(null=True, blank = True, verbose_name = "How many hours per day is the child exposed to these languages?", validators = [MaxValueValidator(24, "Number of hours per day cannot exceed 24"), MinValueValidator(1, "Number of hours per day cannot be less than 1")],) # Asks to quantify the # of hours a day that child is exposed to another language

    ear_infections_boolean = models.IntegerField(verbose_name = "Has your child experienced chronic ear infections (5 or more)? ") # Asks whether child has ever experiences 5+ ear infections
    ear_infections = models.CharField(max_length = 1001, null=True, blank = True, verbose_name = "Has your child undergone interventions (e.g., tubes)?  Please describe") # Free response describing treatment for chronic ear infections

    hearing_loss_boolean = models.IntegerField(verbose_name = 'Do you suspect that your child may have hearing loss?' ) # Asks whether child is suspected to have hearing loss
    hearing_loss = models.CharField(max_length = 1001, blank = True, null=True,  verbose_name = 'Please describe' ) # Free response asking for elaboration on suspicion of hearing loss

    vision_problems_boolean = models.IntegerField(verbose_name = 'Is there some reason to suspect that your child may have vision problems?' ) # Asks whether child is suspected to have vision problems
    vision_problems = models.CharField(max_length = 1001, blank = True, null=True, verbose_name = 'Please describe') # Free response asking for elaboration on suspicion of vision problems

    illnesses_boolean = models.IntegerField(verbose_name = 'Has your child had any major illnesses, hospitalizations, or diagnosed disabilities?' ) # Asks whether child has any major illnesses, diagnoses, or hospitalizations
    illnesses = models.CharField(max_length = 1001, blank = True, null=True, verbose_name = "Please describe") # Free response asking for elaboration on child's symptoms and diagnoses

    services_boolean = models.IntegerField(verbose_name = 'Has your child ever received any services for speech, language, or development issues?' ) # Asks whether child has ever received therapy for speech or development
    services = models.CharField(max_length = 1001, blank = True, null=True, verbose_name = "Please describe") # Free response asking for elaboration on services received

    worried_boolean = models.IntegerField(verbose_name = 'Are you worried about your child\'s progress in language or communication?' ) # Asks whether test-taker is worried about child's language acquisition
    worried = models.CharField(max_length = 1001, blank = True, null=True, verbose_name = "Please describe") # Free response asking for elaboration on test-taker's worries about child's language development

    learning_disability_boolean = models.IntegerField(verbose_name = 'Have you or anyone in your immediate family been diagnosed with a language or learning disability?' ) # Asks whether a relative of the child has ever been diagnoses with a learning/language disability
    learning_disability = models.CharField(max_length = 1001, blank = True, null=True, verbose_name = "Indicate which family member and provide a description") # Free response asking for elaboration on the relationship between child and family member and a description of diagnosis

#Model of zipcodes reported to be in 3-digit zip code prefixes with a population lower than 20,000. Tests with a zipcode found in this model will have their digits replaced with their state abbreviation.
class Zipcode(models.Model):
    zip_code=models.CharField(max_length = 5)
    zip_prefix=models.CharField(max_length = 3)
    population=models.IntegerField()
    state=models.CharField(max_length = 2)


    
