# -*- coding: utf-8 -*-
from django.db import models
from south.db import db
from south.utils import datetime_utils as datetime
from south.v2 import SchemaMigration


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'DefaultRegistrationSupplement'
        db.create_table(
            "registration_defaultregistrationsupplement",
            (
                ("id", self.gf("django.db.models.fields.AutoField")(primary_key=True)),
                (
                    "registration_profile",
                    self.gf("django.db.models.fields.related.OneToOneField")(
                        related_name="_registration_defaultregistrationsupplement_supplement",
                        unique=True,
                        to=orm["registration.RegistrationProfile"],
                    ),
                ),
                ("remarks", self.gf("django.db.models.fields.TextField")()),
            ),
        )
        db.send_create_signal("registration", ["DefaultRegistrationSupplement"])

        # Changing field 'RegistrationProfile._status'
        db.alter_column(
            "registration_registrationprofile",
            "status",
            self.gf("django.db.models.fields.CharField")(
                max_length=10, db_column="status"
            ),
        )

    def backwards(self, orm):
        # Deleting model 'DefaultRegistrationSupplement'
        db.delete_table("registration_defaultregistrationsupplement")

        # Changing field 'RegistrationProfile._status'
        db.alter_column(
            "registration_registrationprofile",
            "status",
            self.gf("django.db.models.fields.CharField")(
                max_length=10, db_column="status"
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
                "ordering": "(u'content_type__app_label', u'content_type__model', u'codename')",
                "unique_together": "((u'content_type', u'codename'),)",
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
        "registration.defaultregistrationsupplement": {
            "Meta": {"object_name": "DefaultRegistrationSupplement"},
            "id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
            "registration_profile": (
                "django.db.models.fields.related.OneToOneField",
                [],
                {
                    "related_name": "u'_registration_defaultregistrationsupplement_supplement'",
                    "unique": "True",
                    "to": "orm['registration.RegistrationProfile']",
                },
            ),
            "remarks": ("django.db.models.fields.TextField", [], {}),
        },
        "registration.registrationprofile": {
            "Meta": {"object_name": "RegistrationProfile"},
            "_status": (
                "django.db.models.fields.CharField",
                [],
                {
                    "default": "u'untreated'",
                    "max_length": "10",
                    "db_column": "u'status'",
                },
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
                    "related_name": "u'registration_profile'",
                    "unique": "True",
                    "to": "orm['auth.User']",
                },
            ),
        },
    }

    complete_apps = ["registration"]
