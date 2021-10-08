# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'DefaultRegistrationSupplement'
        db.create_table(u'registration_defaultregistrationsupplement', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('registration_profile', self.gf('django.db.models.fields.related.OneToOneField')(related_name=u'_registration_defaultregistrationsupplement_supplement', unique=True, to=orm['registration.RegistrationProfile'])),
            ('remarks', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'registration', ['DefaultRegistrationSupplement'])


        # Changing field 'RegistrationProfile._status'
        db.alter_column(u'registration_registrationprofile', u'status', self.gf('django.db.models.fields.CharField')(max_length=10, db_column=u'status'))

    def backwards(self, orm):
        # Deleting model 'DefaultRegistrationSupplement'
        db.delete_table(u'registration_defaultregistrationsupplement')


        # Changing field 'RegistrationProfile._status'
        db.alter_column(u'registration_registrationprofile', 'status', self.gf(u'django.db.models.fields.CharField')(max_length=10, db_column='status'))

    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'registration.defaultregistrationsupplement': {
            'Meta': {'object_name': 'DefaultRegistrationSupplement'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'registration_profile': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "u'_registration_defaultregistrationsupplement_supplement'", 'unique': 'True', 'to': u"orm['registration.RegistrationProfile']"}),
            'remarks': ('django.db.models.fields.TextField', [], {})
        },
        u'registration.registrationprofile': {
            'Meta': {'object_name': 'RegistrationProfile'},
            '_status': ('django.db.models.fields.CharField', [], {'default': "u'untreated'", 'max_length': '10', 'db_column': "u'status'"}),
            'activation_key': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '40', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "u'registration_profile'", 'unique': 'True', 'to': u"orm['auth.User']"})
        }
    }

    complete_apps = ['registration']