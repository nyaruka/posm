import logging
logger = logging.getLogger(__name__)

from django.contrib.gis.db import models
from django.contrib.contenttypes import generic


class Indicator(models.Model):
    factor_a = models.FloatField()
    factor_b = models.FloatField()
    content_type = models.ForeignKey('contenttypes.ContentType')
    object_id = models.CharField(max_length=15)
    content_object = generic.GenericForeignKey('content_type', 'object_id')


class AdminLevel0(models.Model):
    osm_id = models.CharField(max_length=15, primary_key=True)
    name = models.CharField(max_length=50)
    wkb_geometry = models.MultiPolygonField(srid=4326)
    natural_wkb_geometry = models.MultiPolygonField(srid=4326)

    objects = models.GeoManager()

    class Meta:
        managed = False
        db_table = 'simple_admin_0_view'


class AdminLevel1(models.Model):
    osm_id = models.CharField(max_length=15, primary_key=True)
    name = models.CharField(max_length=50)
    is_in_country = models.CharField(max_length=15)
    wkb_geometry = models.MultiPolygonField(srid=4326)
    natural_wkb_geometry = models.MultiPolygonField(srid=4326)

    objects = models.GeoManager()

    class Meta:
        managed = False
        db_table = 'simple_admin_1_view'


class AdminLevel2(models.Model):
    osm_id = models.CharField(max_length=15, primary_key=True)
    name = models.CharField(max_length=50)
    is_in_country = models.CharField(max_length=15)
    is_in_state = models.CharField(max_length=15)
    wkb_geometry = models.MultiPolygonField(srid=4326)
    natural_wkb_geometry = models.MultiPolygonField(srid=4326)

    objects = models.GeoManager()

    class Meta:
        managed = False
        db_table = 'simple_admin_2_view'
