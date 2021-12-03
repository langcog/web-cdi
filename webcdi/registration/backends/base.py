# -*- coding: utf-8 -*-
from __future__ import unicode_literals
"""
Base class of registration backend

All backends of django-inspectional-registration should be a subclass
of the ``BackendBase``
"""
__author__ = 'Alisue <lambdalisue@hashnote.net>'
from registration.utils import get_site


class RegistrationBackendBase(object):

    """Base class of registration backend

    Methods:
        get_site                      -- return current site
        register                      -- register a new user
        accept                        -- accept a registration
        reject                        -- reject a registration
        activate                      -- activate a user
        get_supplement_class          -- get registration supplement class
        get_activation_form_class     -- get activation form class
        get_registration_form_class   -- get registration form class
        get_supplement_form_class     -- get registration supplement form class
        get_activation_complete_url   -- get activation complete redirect url
        get_registration_complete_url -- get registration complete redirect url
        get_registration_closed_url   -- get registration closed redirect url
        registration_allowed          -- whether registration is allowed now

    """

    def get_site(self, request):
        """get current ``django.contrib.Site`` instance

        return ``django.contrib.RequestSite`` instance when the ``Site`` is
        not installed.

        """
        return get_site(request)

    def register(self, username, email, request,
                 supplement=None, send_email=True):
        """register a new user account with given ``username`` and ``email``

        Returning should be a instance of new ``User``

        """
        raise NotImplementedError

    def accept(self, profile, request,
               send_email=True, message=None, force=False):
        """accept account registration with given ``profile`` (an instance of
        ``RegistrationProfile``)

        Returning should be a instance of accepted ``User`` for success,
        ``None`` for fail.

        This method **SHOULD** work even after the account registration has
        rejected.

        """
        raise NotImplementedError

    def reject(self, profile, request, send_email=True, message=None):
        """reject account registration with given ``profile`` (an instance of
        ``RegistrationProfile``)

        Returning should be a instance of accepted ``User`` for success,
        ``None`` for fail.

        This method **SHOULD NOT** work after the account registration has
        accepted.

        """
        raise NotImplementedError

    def activate(self, activation_key, request, password=None, send_email=True,
                 message=None, no_profile_delete=False):
        """activate account with ``activation_key`` and ``password``

        This method should be called after the account registration has
        accepted, otherwise it should not be success.

        Returning is ``user``, ``password`` and ``is_generated`` for success,
        ``None`` for fail.

        If ``password`` is not given, this method will generate password and
        ``is_generated`` should be ``True`` in this case.

        """
        raise NotImplementedError

    def get_supplement_class(self):
        """Return the current registration supplement class"""
        raise NotImplementedError

    def get_activation_form_class(self):
        """get activation form class"""
        raise NotImplementedError

    def get_registration_form_class(self):
        """get registration form class"""
        raise NotImplementedError

    def get_supplement_form_class(self):
        """get registration supplement form class"""
        raise NotImplementedError

    def get_activation_complete_url(self, user):
        """get activation complete url"""
        raise NotImplementedError

    def get_registration_complete_url(self, user):
        """get registration complete url"""
        raise NotImplementedError

    def get_registration_closed_url(self):
        """get registration closed url"""
        raise NotImplementedError

    def registration_allowed(self):
        """return ``False`` if the registration has closed"""
        raise NotImplementedError
