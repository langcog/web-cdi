from __future__ import unicode_literals
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from registration.supplements.base import RegistrationSupplementBase

@python_2_unicode_compatible
class MyRegistrationSupplement(RegistrationSupplementBase):

    name = models.CharField(verbose_name = "Full name", max_length=101, help_text="Please fill your full name here")
    institution = models.CharField(verbose_name = "Name of institution", max_length=101)
    comments = models.TextField("Comments", blank=True)

    def __str__(self):
        # a summary of this supplement
        return "%s (%s)" % (self.name, self.institution)