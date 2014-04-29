import logging
logger = logging.getLogger(__name__)

from django.contrib.gis.db import models
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType

from model_utils.managers import PassThroughManager


class IndicatorQuerySet(models.query.QuerySet):
    def for_osm_id(self, osm_id):
        try:
            # check adminlevel0
            admin_level = AdminLevel0.objects.get(osm_id__exact=osm_id)
            ad1_ct = ContentType.objects.get(
                app_label="demo", model="adminlevel1"
            )
            ad1_data = AdminLevel1.objects.filter(
                is_in_country__exact=admin_level.pk
            )
            # setup filter
            return self.filter(object_id__in=ad1_data, content_type=ad1_ct)
        except AdminLevel0.DoesNotExist:
            pass

        try:
            # check adminlevel1
            admin_level = AdminLevel1.objects.get(osm_id__exact=osm_id)
            ad2_ct = ContentType.objects.get(
                app_label="demo", model="adminlevel2"
            )
            ad2_data = AdminLevel2.objects.filter(
                is_in_state__exact=admin_level.pk
            )
            # setup filter
            return self.filter(object_id__in=ad2_data, content_type=ad2_ct)
        except AdminLevel1.DoesNotExist:
            pass


class Indicator(models.Model):
    factor_a = models.FloatField()
    factor_b = models.FloatField()
    content_type = models.ForeignKey('contenttypes.ContentType')
    object_id = models.CharField(max_length=15)
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    # define custom queryset
    objects = PassThroughManager.for_queryset_class(IndicatorQuerySet)()

    def name(self):
        return self.content_object.name or 'Unknown'


class AdminLevel0(models.Model):
    osm_id = models.CharField(max_length=15, primary_key=True)
    name = models.CharField(max_length=50)
    wkb_geometry = models.MultiPolygonField(srid=4326)
    natural_wkb_geometry = models.MultiPolygonField(srid=4326)

    # reverse generic relation
    indicators = generic.GenericRelation(Indicator)

    objects = models.GeoManager()

    class Meta:
        managed = False  # don't manage database view
        db_table = 'simple_admin_0_view'


class AdminLevel1(models.Model):
    osm_id = models.CharField(max_length=15, primary_key=True)
    name = models.CharField(max_length=50)
    is_in_country = models.CharField(max_length=15)
    wkb_geometry = models.MultiPolygonField(srid=4326)
    natural_wkb_geometry = models.MultiPolygonField(srid=4326)

    # reverse generic relation
    indicators = generic.GenericRelation(Indicator)

    objects = models.GeoManager()

    class Meta:
        managed = False  # don't manage database view
        db_table = 'simple_admin_1_view'


class AdminLevel2(models.Model):
    osm_id = models.CharField(max_length=15, primary_key=True)
    name = models.CharField(max_length=50)
    is_in_country = models.CharField(max_length=15)
    is_in_state = models.CharField(max_length=15)
    wkb_geometry = models.MultiPolygonField(srid=4326)
    natural_wkb_geometry = models.MultiPolygonField(srid=4326)

    # reverse generic relation
    indicators = generic.GenericRelation(Indicator)

    objects = models.GeoManager()

    class Meta:
        managed = False  # don't manage database view
        db_table = 'simple_admin_2_view'
