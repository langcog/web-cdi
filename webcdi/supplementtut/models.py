from __future__ import unicode_literals
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from registration.supplements.base import RegistrationSupplementBase

@python_2_unicode_compatible
class MyRegistrationSupplement(RegistrationSupplementBase): # Model for supplementary questions to account registration

    first_name = models.CharField(verbose_name = "First name", max_length=101) # First name of researcher or research group
    last_name = models.CharField(verbose_name = "Last name", max_length=101) # First name of researcher or research group
    institution = models.CharField(verbose_name = "Name of Institution", max_length=101) # Name of research institution they are affiliated with
    position = models.CharField(verbose_name = "Position in Institution", max_length=101) # Title of position within research institution
    comments = models.TextField(verbose_name = "Comments", blank=True) # Any additional comments they wanted to add

    def __str__(self):
        # a summary of this supplement
        return "%s %s, %s (%s)" % (self.first_name, self.last_name, self.position, self.institution) # Format for how to present a summary of supplementary information in staff interface