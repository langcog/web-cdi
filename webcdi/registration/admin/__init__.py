# -*- coding: utf-8 -*-
from __future__ import unicode_literals
"""
Admins of django-inspectional-registration

This is a modification of django-registration_ ``admin.py``
The original code is written by James Bennett

.. _django-registration: https://bitbucket.org/ubernostrum/django-registration


Original License::

    Copyright (c) 2007-2011, James Bennett
    All rights reserved.

    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions are
    met:

        * Redistributions of source code must retain the above copyright
        notice, this list of conditions and the following disclaimer.
        * Redistributions in binary form must reproduce the above
        copyright notice, this list of conditions and the following
        disclaimer in the documentation and/or other materials provided
        with the distribution.
        * Neither the name of the author nor the names of other
        contributors may be used to endorse or promote products derived
        from this software without specific prior written permission.

    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
    "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
    LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
    A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
    OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
    SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
    LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
    DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
    THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
    (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
    OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
__author__ = 'Alisue <lambdalisue@hashnote.net>'
__all__ = (
    'RegistrationSupplementAdminInlineBase',
    'RegistrationAdmin'
)
import django
from django.db import transaction
from django.http import HttpResponseRedirect
from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.core.exceptions import ImproperlyConfigured
from django.views.decorators.csrf import csrf_protect
from django.utils.safestring import mark_safe
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import force_text

from registration.conf import settings
from registration.backends import get_backend
from registration.models import RegistrationProfile
from registration.utils import get_site
from registration.admin.forms import RegistrationAdminForm
from registration.compat import import_module
from registration.compat import transaction_atomic
from registration.compat import unquote


csrf_protect_m = method_decorator(csrf_protect)


def get_supplement_admin_inline_base_class(path=None):
    """
    Return a class of a admin inline class for registration supplement,
    given the dotted Python import path (as a string) to the admin inline
    class.

    If the addition cannot be located (e.g., because no such module
    exists, or because the module does not contain a class of the
    appropriate name), ``django.core.exceptions.ImproperlyConfigured``
    is raised.

    """
    path = path or settings.REGISTRATION_SUPPLEMENT_ADMIN_INLINE_BASE_CLASS
    i = path.rfind('.')
    module, attr = path[:i], path[i+1:]
    try:
        mod = import_module(module)
    except ImportError as e:
        raise ImproperlyConfigured((
            'Error loading admin inline class for registration supplement '
            '%s: "%s"'
        ) % (module, e))
    try:
        cls = getattr(mod, attr)
    except AttributeError:
        raise ImproperlyConfigured((
            'Module "%s" does not define a admin inline class for '
            'registration supplement named "%s"'
        ) % (module, attr))
    if cls and not issubclass(cls, RegistrationSupplementAdminInlineBase):
        raise ImproperlyConfigured((
            'Admin inline class for registration supplement class "%s" '
            'must be a subclass of ``registration.admin.'
            'RegistrationSupplementAdminInlineBase``'
        ) % path)
    return cls


class RegistrationSupplementAdminInlineBase(admin.StackedInline):
    """Registration supplement admin inline base class

    This inline class is used to generate admin inline class of current
    registration supplement. Used inline class is defined as
    ``settings.REGISTRATION_SUPPLEMENT_ADMIN_INLINE_BASE_CLASS`` thus if you
    want to modify the inline class of supplement, create a subclass of this
    class and set to ``REGISTRATION_SUPPLEMENT_ADMIN_INLINE_BASE_CLASS``

    """
    fields = ()

    def get_readonly_fields(self, request, obj=None):
        """get readonly fields of supplement

        Readonly fields will be generated by supplement's
        ``get_admin_fields`` and ``get_admin_excludes`` method thus if you want
        to change the fields displayed in django admin site. You want to change
        the method or attributes ``admin_fields`` or ``admin_excludes`` which
        is loaded by those method in default.

        See more detail in
        ``registration.supplements.DefaultRegistrationSupplement``
        documentation.

        """
        if obj is None:
            return ()
        fields = self.model.get_admin_fields()
        excludes = self.model.get_admin_excludes()
        if fields is None:
            try:
                #<django 1.10 _meta API
                fields = self.model._meta.get_all_field_names()
            except AttributeError:
                #django 1.10+ _meta API
                fields = [f.name for f in self.model._meta.get_fields()]
            
            if 'id' in fields:
                fields.remove('id')
            if 'registration_profile_id' in fields:
                fields.remove('registration_profile_id')
        if excludes is not None:
            for exclude in excludes:
                fields.remove(exclude)
        return fields

    def has_change_permission(self, request, obj=None):
        # Without change permission, supplemental information won't be shown
        # while get_queryset required change permission
        # Ref: https://github.com/django/django/blob/1.7
        #      /django/contrib/admin/options.py#L1852
        return True


class RegistrationAdmin(admin.ModelAdmin):
    """Admin class of RegistrationProfile

    Admin users can accept/reject registration and activate user in Django
    Admin page.

    If ``REGISTRATION_SUPPLEMENT_CLASS`` is specified, admin users can see the
    summary of the supplemental information in list view and detail of it in
    change view.

    ``RegistrationProfile`` is not assumed to handle by hand thus
    adding/changing/deleting is not accepted even in Admin page.
    ``RegistrationProfile`` only can be accepted/rejected or activated.
    To prevent these disallowed functions, the special AdminForm called
    ``RegistrationAdminForm`` is used.
    Its ``save`` method is overridden and it actually does not save the
    instance.
    It just call ``accept``, ``reject`` or ``activate`` method of current
    registration backend. So you don't want to override the ``save`` method of
    the form.

    """
    list_display = ('user', 'get_status_display',
                    'activation_key_expired', 'display_supplement_summary')
    raw_id_fields = ['user']
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    list_filter = ('_status', )

    form = RegistrationAdminForm
    backend = get_backend()

    readonly_fields = ('user', '_status')

    actions = (
        'accept_users',
        'reject_users',
        'force_activate_users',
        'resend_acceptance_email'
    )

    def __init__(self, model, admin_site):
        super(RegistrationAdmin, self).__init__(model, admin_site)
        if not hasattr(super(RegistrationAdmin, self), 'get_inline_instances'):
            # Django 1.3 doesn't have ``get_inline_instances`` method but
            # ``inline_instances`` was generated in ``__init__`` thus
            # update the attribute
            self.inline_instances = self.get_inline_instances(None)

    def has_add_permission(self, request):
        """registration profile should not be created by hand"""
        return False

    def has_delete_permission(self, request, obj=None):
        """registration profile should not be created by hand"""
        return False

    def has_accept_permission(self, request, obj):
        """whether the user has accept permission"""
        if not settings.REGISTRATION_USE_OBJECT_PERMISSION:
            obj = None
        return request.user.has_perm('registration.accept_registration', obj)

    def has_reject_permission(self, request, obj):
        """whether the user has reject permission"""
        if not settings.REGISTRATION_USE_OBJECT_PERMISSION:
            obj = None
        return request.user.has_perm('registration.reject_registration', obj)

    def has_activate_permission(self, request, obj):
        """whether the user has activate permission"""
        if not settings.REGISTRATION_USE_OBJECT_PERMISSION:
            obj = None
        return request.user.has_perm('registration.activate_user', obj)

    def get_actions(self, request):
        """get actions displaied in admin site

        RegistrationProfile should not be deleted in admin site thus
        'delete_selected' is disabled in default.

        Each actions has permissions thus delete the action if the accessed
        user doesn't have appropriate permission.

        """
        actions = super(RegistrationAdmin, self).get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        if not request.user.has_perm('registration.accept_registration'):
            del actions['accept_users']
        if not request.user.has_perm('registration.reject_registration'):
            del actions['reject_users']
        if not request.user.has_perm('registration.accept_registration') or \
           not request.user.has_perm('registration.activate_user'):
            del actions['force_activate_users']
        return actions

    def accept_users(self, request, queryset):
        """Accept the selected users, if they are not already accepted"""
        for profile in queryset:
            self.backend.accept(profile, request=request, force=True)
    accept_users.short_description = _(
        "(Re)Accept registrations of selected users"
    )

    def reject_users(self, request, queryset):
        """Reject the selected users, if they are not already accepted"""
        for profile in queryset:
            self.backend.reject(profile, request=request)
    reject_users.short_description = _(
        "Reject registrations of selected users"
    )

    def force_activate_users(self, request, queryset):
        """Activates the selected users, if they are not already activated"""
        for profile in queryset:
            self.backend.accept(profile, request=request, send_email=False)
            self.backend.activate(profile.activation_key, request=request)
    force_activate_users.short_description = _(
        "Activate selected users forcibly"
    )

    def resend_acceptance_email(self, request, queryset):
        """Re-sends acceptance emails for the selected users

        Note that this will *only* send acceptance emails for users
        who are eligible to activate; emails will not be sent to users
        whose activation keys have expired or who have already
        activated or rejected.

        """
        site = get_site(request)
        for profile in queryset:
            if not profile.activation_key_expired():
                if profile.status != 'rejected':
                    profile.send_acceptance_email(site=site)
    resend_acceptance_email.short_description = _(
        "Re-send acceptance emails to selected users"
    )

    def display_supplement_summary(self, obj):
        """Display supplement summary

        Display ``__unicode__`` method result of
        ``REGISTRATION_SUPPLEMENT_CLASS``
        ``Not available`` when ``REGISTRATION_SUPPLEMENT_CLASS`` is not
        specified

        """
        if obj.supplement:
            return force_text(obj.supplement)
        return _('Not available')
    display_supplement_summary.short_description = _(
        'A summary of supplemental information'
    )

    def display_activation_key(self, obj):
        """Display activation key with link

        Note that displaying activation key is not recommended in security
        reason.
        If you really want to use this method, create your own subclass and
        re-register to admin.site

        Even this is a little bit risky, it is really useful for developping
        (without checking email, you can activate any user you want) thus
        I created but turned off in default :-p

        """
        if obj.status == 'accepted':
            activation_url = reverse('registration_activate',
                                     kwargs={
                                         'activation_key': obj.activation_key})
            return mark_safe('<a href="%s">%s</a>' % (
                activation_url, obj.activation_key))
        return _('Not available')
    display_activation_key.short_description = _('Activation key')
    display_activation_key.allow_tags = True

    def get_inline_instances(self, request, obj=None):
        """
        return inline instances with registration supplement inline instance
        """
        inline_instances = []
        supplement_class = self.backend.get_supplement_class()
        if supplement_class:
            kwargs = {
                'extra': 1,
                'max_num': 1,
                'can_delete': False,
                'model': supplement_class,
            }
            inline_base = get_supplement_admin_inline_base_class()
            inline_form = type(
                str("RegistrationSupplementInlineAdmin"),
                (inline_base,), kwargs
            )
            inline_instances = [inline_form(self.model, self.admin_site)]
        supercls = super(RegistrationAdmin, self)
        if hasattr(supercls, 'get_inline_instances'):
            if django.VERSION >= (1, 5):
                inline_instances.extend(supercls.get_inline_instances(
                    request, obj
                ))
            else:
                # Django 1.4 cannot handle obj
                inline_instances.extend(supercls.get_inline_instances(
                    request,
                ))
        else:
            # Django 1.3
            for inline_class in self.inlines:
                inline_instance = inline_class(self.model, self.admin_site)
                inline_instances.append(inline_instance)
        return inline_instances

    def get_object(self, request, object_id, from_field=None):
        """add ``request`` instance to model instance and return

        To get ``request`` instance in form, ``request`` instance is stored
        in the model instance.

        """
        if django.VERSION < (1, 8, 0):
            obj = super(RegistrationAdmin, self).get_object(request, object_id)
        else:
            # Note:
            #   from_field was introduced from django 1.8
            obj = super(RegistrationAdmin, self).get_object(request,
                                                            object_id,
                                                            from_field)
        if obj:
            attr_name = settings._REGISTRATION_ADMIN_REQ_ATTR_NAME_IN_MODEL_INS
            setattr(obj, attr_name, request)
        return obj

    @csrf_protect_m
    @transaction_atomic
    def change_view(self, request, object_id, form_url='', extra_context=None):
        """called for change view

        Check permissions of the admin user for ``POST`` request depends on
        what action is requested and raise PermissionDenied if the action is
        not accepted for the admin user.

        """
        obj = self.get_object(request, unquote(object_id))

        # Permissin check
        if request.method == 'POST':
            #
            # Note:
            #   actions will be treated in form.save() method.
            #   in general, activate action will remove the profile because
            #   the profile is no longer required after the activation
            #   but if I remove the profile in form.save() method, django admin
            #   will raise IndexError thus I passed `no_profile_delete = True`
            #   to activate with backend in form.save() method.
            #
            action_name = request.POST.get('action_name')
            if (action_name == 'accept' and
                    not self.has_accept_permission(request, obj)):
                raise PermissionDenied
            elif (action_name == 'reject' and
                    not self.has_reject_permission(request, obj)):
                raise PermissionDenied
            elif (action_name == 'activate' and
                    not self.has_activate_permission(request, obj)):
                raise PermissionDenied
            elif action_name == 'force_activate' and (
                    not self.has_accept_permission(request, obj) or
                    not self.has_activate_permission(request, obj)):
                raise PermissionDenied

        if django.VERSION < (1, 4,):
            response = super(RegistrationAdmin, self).change_view(
                request, object_id, extra_context
            )
        else:
            response = super(RegistrationAdmin, self).change_view(
                request, object_id, form_url, extra_context
            )

        if (request.method == 'POST' and
                action_name in ('activate', 'force_activate')):
            # if the requested data is valid then response will be an instance
            # of ``HttpResponseRedirect`` otherwise ``TemplateResponse``
            if isinstance(response, HttpResponseRedirect):
                obj.delete()
        return response
admin.site.register(RegistrationProfile, RegistrationAdmin)
