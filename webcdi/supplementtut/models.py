from __future__ import unicode_literals
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from registration.supplements.base import RegistrationSupplementBase

@python_2_unicode_compatible
class MyRegistrationSupplement(RegistrationSupplementBase): # Model for supplementary questions to account registration

    name = models.CharField(verbose_name = "Full name", max_length=101, help_text="Please fill your full name here") # Full name of researcher or research group
    institution = models.CharField(verbose_name = "Name of institution", max_length=101) # Name of research institution they are affiliated with
    position = models.CharField(verbose_name = "Position in Institution", max_length=101) # Title of position within research institution
    comments = models.TextField(verbose_name = "Comments", blank=True) # Any additional comments they wanted to add

    def __str__(self):
        # a summary of this supplement
        return "%s, %s (%s)" % (self.name, self.position, self.institution) # Format for how to present a summary of supplementary information in staff interface