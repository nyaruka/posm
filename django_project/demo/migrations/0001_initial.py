# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Indicator'
        db.create_table(u'demo_indicator', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('factor_a', self.gf('django.db.models.fields.FloatField')()),
            ('factor_b', self.gf('django.db.models.fields.FloatField')()),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.CharField')(max_length=15)),
        ))
        db.send_create_signal(u'demo', ['Indicator'])


    def backwards(self, orm):
        # Deleting model 'Indicator'
        db.delete_table(u'demo_indicator')


    models = {
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'demo.adminlevel0': {
            'Meta': {'object_name': 'AdminLevel0', 'db_table': "'simple_admin_0_view'", 'managed': 'False'},
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'natural_wkb_geometry': ('django.contrib.gis.db.models.fields.MultiPolygonField', [], {}),
            'osm_id': ('django.db.models.fields.CharField', [], {'max_length': '15', 'primary_key': 'True'}),
            'wkb_geometry': ('django.contrib.gis.db.models.fields.MultiPolygonField', [], {})
        },
        u'demo.adminlevel1': {
            'Meta': {'object_name': 'AdminLevel1', 'db_table': "'simple_admin_1_view'", 'managed': 'False'},
            'is_in_country': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'natural_wkb_geometry': ('django.contrib.gis.db.models.fields.MultiPolygonField', [], {}),
            'osm_id': ('django.db.models.fields.CharField', [], {'max_length': '15', 'primary_key': 'True'}),
            'wkb_geometry': ('django.contrib.gis.db.models.fields.MultiPolygonField', [], {})
        },
        u'demo.adminlevel2': {
            'Meta': {'object_name': 'AdminLevel2', 'db_table': "'simple_admin_2_view'", 'managed': 'False'},
            'is_in_country': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'is_in_state': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'natural_wkb_geometry': ('django.contrib.gis.db.models.fields.MultiPolygonField', [], {}),
            'osm_id': ('django.db.models.fields.CharField', [], {'max_length': '15', 'primary_key': 'True'}),
            'wkb_geometry': ('django.contrib.gis.db.models.fields.MultiPolygonField', [], {})
        },
        u'demo.indicator': {
            'Meta': {'object_name': 'Indicator'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            'factor_a': ('django.db.models.fields.FloatField', [], {}),
            'factor_b': ('django.db.models.fields.FloatField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.CharField', [], {'max_length': '15'})
        }
    }

    complete_apps = ['demo']