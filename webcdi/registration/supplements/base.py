# -*- coding: utf-8 -*-
from __future__ import unicode_literals
"""
A registration supplemental abstract model
"""
__author__ = 'Alisue <lambdalisue@hashnote.net>'
from django.db import models
from django.forms.models import modelform_factory
from django.utils.translation import ugettext_lazy as _
#from django.utils.encoding import python_2_unicode_compatible

from six import python_2_unicode_compatible



@python_2_unicode_compatible
class RegistrationSupplementBase(models.Model):
    """A registration supplement abstract model

    Registration supplement model is used to add supplemental information to
    the account registration. The supplemental information is written by the
    user who tried to register the site and displaied in django admin page to
    help determine the acceptance/rejection of the registration

    The ``__str__()`` method is used to display the summary of the 
    supplemental information in django admin's change list view. Thus subclasses
    must define them own ``__str__()`` method.

    The ``get_form_class()`` is a class method return a value of ``form_class``
    attribute to determine the form class used for filling up the supplemental
    informatin in registration view if ``form_class`` is specified. Otherwise the
    method create django's ``ModelForm`` and return.

    The ``get_admin_fields()`` is a class method return a list of field names
    displayed in django admin site. It simply return a value of ``admin_fields`` 
    attribute in default. If the method return ``None``, then all fields except
    ``id`` (and fields in ``admin_excludes``) will be displayed.

    The ``get_admin_excludes()`` is a class method return a list of field names
    NOT displayed in django admin site. It simply return a value of ``admin_excludes`` 
    attribute in default. If the method return ``None``, then all fields selected
    with ``admin_fields`` except ``id`` will be displayed.
    
    The ``registration_profile`` field is used to determine the registration
    profile associated with. ``related_name`` of the field is used to get the
    supplemental information in ``_get_supplement()`` method of 
    ``RegistrationProfile`` thus DO NOT CHANGE the name.

    """
    form_class = None
    admin_fields = None
    admin_excludes = None
    registration_profile = models.OneToOneField(
            'registration.RegistrationProfile',
            verbose_name=_('registration profile'),
            editable=False, related_name='_%(app_label)s_%(class)s_supplement',
            on_delete=models.CASCADE)

    class Meta:
        abstract = True

    def __str__(self):
        """return the summary of this supplemental information

        Subclasses must define them own method
        """
        raise NotImplementedError(
                "You must define '__str__' method and return summary of "
                "the supplement")

    @classmethod
    def get_form_class(cls):
        """Return the form class used for this registration supplement model

        When ``form_class`` is specified, this method return the value of the
        attribute. Otherwise it generate django's ``ModelForm``, set it to
        ``form_class`` and return it

        This method MUST BE class method.

        """
        if not getattr(cls, 'form_class', None):
            setattr(cls, 'form_class', modelform_factory(cls, exclude=[]))
        return getattr(cls, 'form_class')

    @classmethod
    def get_admin_fields(cls):
        """Return a list of field names displayed in django admin site

        It is simply return a value of ``admin_fields`` in default. If it returns
        ``None`` then all fields except ``id`` (and fields in ``admin_excludes``)
        will be displayed.

        """
        return cls.admin_fields

    @classmethod
    def get_admin_excludes(cls):
        """Return a list of field names NOT displayed in django admin site

        It is simply return a value of ``admin_excludes`` in default. If it returns
        ``None`` then all fields (selected in ``admin_fields``) except ``id``
        will be displayed.

        """
        return cls.admin_excludes
