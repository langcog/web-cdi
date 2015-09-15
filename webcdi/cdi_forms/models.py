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

class BackgroundInfo(models.Model):
    age = models.IntegerField(verbose_name = "Age (in months)")
    gender = models.CharField(max_length = 1, choices = (('M', "Male"), ('F', "Female"), ('O', "Other")))
    birth_order = models.IntegerField()
    birth_weight = models.IntegerField()
    early_late = models.DateField(verbose_name = "Early or late birth", help_text = "If the child was born on due date, fill 0. If the child was born earlier than due date, fill the number of weeks after the due date as positive value. If the child was born later fill a negative value." )

    mother_yob = models.DateField(verbose_name = "Year of birth", )
    mother_education = models.IntegerField(verbose_name = "Education", help_text ="Choose highest grade completed (12 = high school graduate; 16 = college graduate; 18 = advanced degree)")
    mother_occupation = models.CharField(max_length = 101, verbose_name = "Occupation")
    mother_hours_work = models.IntegerField(verbose_name = "Hours/week at work")

    father_yob = models.DateField(verbose_name = "Year of birth")
    father_education = models.IntegerField(verbose_name = "Education")
    father_occupation = models.CharField(max_length = 101, verbose_name = "Occupation")
    father_hours_work = models.IntegerField(verbose_name = "Hours/week at work")
    
    annual_income = models.IntegerField(verbose_name = "Estimated Annual Family Income")

    child_hispanic_latino = models.BooleanField(verbose_name = "Is your child Hispanic or Latino?")
    child_ethnicity = models.CharField(max_length = 101)

    parent_1_hours = models.IntegerField(verbose_name = "Parent 1")
    parent_2_hours = models.IntegerField(verbose_name = "Parent 2")
    other = models.CharField(max_length = 20,  blank = True, verbose_name = "Other caregiver (if any)", help_text = "e.g. nanny, family provider, grandmother")
    other_hours = models.IntegerField( blank = True, verbose_name = "Hours spend with other caregivers")

    daycare_days_per_week = models.IntegerField( blank = True, verbose_name = "Number of days per week at daycare or preschool (if applicable)")
    daycare_hours_per_day = models.IntegerField( blank = True, verbose_name = "Number of hours per day at daycare or preschool (if applicable)")
    daycare_since = models.IntegerField( blank = True, verbose_name = "Since what age (in months) at daycare or preschool (if applicable)")

    which_language = models.CharField(max_length = 20, blank = True)
    language_from = models.CharField(max_length = 20, blank = True)
    language_days_per_week = models.IntegerField( blank = True)
    language_hours_per_day = models.IntegerField( blank = True)
    language_since = models.IntegerField( blank = True)

    ear_infections = models.CharField(max_length = 101, blank = True, verbose_name = "Has your child experienced chronic ear infections (5 or more)? If yes, has your child undergone interventions (e.g., tubes)?  Please describe. If no, leave blank")
    hearing_loss = models.CharField(max_length = 101, blank = True,  verbose_name = 'Do you suspect that your child may have hearing loss? If yes, please describe. If no, leave blank.' )
    vision_problems = models.CharField(max_length = 101, blank = True,  verbose_name = 'Is there some reason to suspect that your child may have vision problems? If yes, describe, leave blank otherwise.')
    illnesses = models.CharField(max_length = 101, blank = True, verbose_name = "Has your child had any major illnesses, hospitalizations, or diagnosed disabilities? If yes, describe, leave blank otherwise.")
    services = models.CharField(max_length = 101, blank = True, verbose_name = "Has your child ever received any services for speech, language, or development issues? If yes, describe, leave blank otherwise. ")
    worried = models.CharField(max_length = 101, blank = True, verbose_name = "Are you worried about your child's progress in language or communication? If yes, describe, leave blank otherwise. ")
    learning_disability = models.CharField(max_length = 101, blank = True, verbose_name = "Have you or anyone in your extended family been diagnosed with a language or learning disability? If yes, indicate which family member and provide a description, leave blank otherwise.")


    
