# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime

from django.db import models
from south.db import db
from south.v2 import SchemaMigration


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Adding field 'RegistrationProfile._status'
        db.add_column(
            "registration_registrationprofile",
            "_status",
            self.gf("django.db.models.fields.CharField")(
                default="untreated", max_length=10, db_column="status"
            ),
            keep_default=False,
        )

        # Changing field 'RegistrationProfile.activation_key'
        db.alter_column(
            "registration_registrationprofile",
            "activation_key",
            self.gf("django.db.models.fields.CharField")(max_length=40, null=True),
        )

        # Changing field 'RegistrationProfile.user'
        db.alter_column(
            "registration_registrationprofile",
            "user_id",
            self.gf("django.db.models.fields.related.OneToOneField")(
                unique=True, to=orm["auth.User"]
            ),
        )

    def backwards(self, orm):

        # Deleting field 'RegistrationProfile._status'
        db.delete_column("registration_registrationprofile", "status")

        # Changing field 'RegistrationProfile.activation_key'
        db.alter_column(
            "registration_registrationprofile",
            "activation_key",
            self.gf("django.db.models.fields.CharField")(default="", max_length=40),
        )

        # Changing field 'RegistrationProfile.user'
        db.alter_column(
            "registration_registrationprofile",
            "user_id",
            self.gf("django.db.models.fields.related.ForeignKey")(
                to=orm["auth.User"], unique=True
            ),
        )

    models = {
        "auth.group": {
            "Meta": {"object_name": "Group"},
            "id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
            "name": (
                "django.db.models.fields.CharField",
                [],
                {"unique": "True", "max_length": "80"},
            ),
            "permissions": (
                "django.db.models.fields.related.ManyToManyField",
                [],
                {
                    "to": "orm['auth.Permission']",
                    "symmetrical": "False",
                    "blank": "True",
                },
            ),
        },
        "auth.permission": {
            "Meta": {
                "ordering": "('content_type__app_label', 'content_type__model', 'codename')",
                "unique_together": "(('content_type', 'codename'),)",
                "object_name": "Permission",
            },
            "codename": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "100"},
            ),
            "content_type": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {"to": "orm['contenttypes.ContentType']"},
            ),
            "id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
            "name": ("django.db.models.fields.CharField", [], {"max_length": "50"}),
        },
        "auth.user": {
            "Meta": {"object_name": "User"},
            "date_joined": (
                "django.db.models.fields.DateTimeField",
                [],
                {"default": "datetime.datetime.now"},
            ),
            "email": (
                "django.db.models.fields.EmailField",
                [],
                {"max_length": "75", "blank": "True"},
            ),
            "first_name": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "30", "blank": "True"},
            ),
            "groups": (
                "django.db.models.fields.related.ManyToManyField",
                [],
                {"to": "orm['auth.Group']", "symmetrical": "False", "blank": "True"},
            ),
            "id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
            "is_active": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "True"},
            ),
            "is_staff": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "False"},
            ),
            "is_superuser": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "False"},
            ),
            "last_login": (
                "django.db.models.fields.DateTimeField",
                [],
                {"default": "datetime.datetime.now"},
            ),
            "last_name": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "30", "blank": "True"},
            ),
            "password": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "128"},
            ),
            "user_permissions": (
                "django.db.models.fields.related.ManyToManyField",
                [],
                {
                    "to": "orm['auth.Permission']",
                    "symmetrical": "False",
                    "blank": "True",
                },
            ),
            "username": (
                "django.db.models.fields.CharField",
                [],
                {"unique": "True", "max_length": "30"},
            ),
        },
        "contenttypes.contenttype": {
            "Meta": {
                "ordering": "('name',)",
                "unique_together": "(('app_label', 'model'),)",
                "object_name": "ContentType",
                "db_table": "'django_content_type'",
            },
            "app_label": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "100"},
            ),
            "id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
            "model": ("django.db.models.fields.CharField", [], {"max_length": "100"}),
            "name": ("django.db.models.fields.CharField", [], {"max_length": "100"}),
        },
        "registration.registrationprofile": {
            "Meta": {"object_name": "RegistrationProfile"},
            "_status": (
                "django.db.models.fields.CharField",
                [],
                {"default": "'untreated'", "max_length": "10", "db_column": "'status'"},
            ),
            "activation_key": (
                "django.db.models.fields.CharField",
                [],
                {"default": "None", "max_length": "40", "null": "True"},
            ),
            "id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
            "user": (
                "django.db.models.fields.related.OneToOneField",
                [],
                {
                    "related_name": "'registration_profile'",
                    "unique": "True",
                    "to": "orm['auth.User']",
                },
            ),
        },
    }

    complete_apps = ["registration"]
