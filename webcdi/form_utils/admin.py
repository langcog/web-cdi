# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.contrib import admin

from .fields import ClearableFileField


class ClearableFileFieldsAdmin(admin.ModelAdmin):
    def formfield_for_dbfield(self, db_field, **kwargs):
        field = super(ClearableFileFieldsAdmin, self).formfield_for_dbfield(
            db_field, **kwargs
        )
        if isinstance(field, forms.FileField):
            field = ClearableFileField(field)
        return field
