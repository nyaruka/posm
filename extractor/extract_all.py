#!/usr/bin/python2
# -*- coding: utf-8 -*-
import logging
import logging.config

from exposm.settings import settings

# setup logging, has to be after osmext.settings
logging.config.dictConfig(settings.get('logging'))
LOG = logging.getLogger(__file__)

from exposm.writer import AdminLevelWriter, DiscardFeatureWriter
from exposm.reader import AdminLevelReader
from exposm.utils import osm_id_exists, check_bad_geom


def main():

    lyr_discard = DiscardFeatureWriter.create_shp('discarded')

    lyr_save1 = AdminLevelWriter.create_shp('admin_level_1')
    lyr_save2 = AdminLevelWriter.create_shp('admin_level_2')
    lyr_save3 = AdminLevelWriter.create_shp('admin_level_3')
    lyr_save4 = AdminLevelWriter.create_shp('admin_level_4')
    lyr_save5 = AdminLevelWriter.create_shp('admin_level_5')
    lyr_save6 = AdminLevelWriter.create_shp('admin_level_6')
    lyr_save7 = AdminLevelWriter.create_shp('admin_level_7')
    lyr_save8 = AdminLevelWriter.create_shp('admin_level_8')
    lyr_save9 = AdminLevelWriter.create_shp('admin_level_9')
    lyr_save10 = AdminLevelWriter.create_shp('admin_level_10')

    lyr_read = AdminLevelReader(settings.get('sources').get('osm_data_file'))

    LOG.info('Started exporting admin_level_0 boundaries!')

    for layer, feature in lyr_read.readData():

        # get data
        osm_id = feature.GetField('osm_id')
        admin_level = feature.GetField('admin_level')
        name = feature.GetField('name')
        name_en = feature.GetField('name:en')
        geom = feature.GetGeometryRef()

        bad_geom = check_bad_geom(geom, osm_id)
        # BONKERS features usually crash QGIS, we need to skip those
        if bad_geom and bad_geom != 'BONKERS!':
            feature_data = [
                ('osm_id', osm_id),
                ('name', name),
                ('adminlevel', admin_level),
                ('reason', bad_geom)
            ]
            lyr_discard.saveFeature(feature_data, geom)
            # skip further processing
            continue
        elif bad_geom == 'BONKERS!':
            continue

        # osm_id is crucial for establishing feature relationship
        if not(osm_id_exists(osm_id, name)):
            LOG.warning('Feature without OSM_ID, discarding... "%s"', name)
            feature_data = [
                ('osm_id', osm_id),
                ('name', name),
                ('adminlevel', admin_level),
                ('reason', 'Feature without OSM_ID!')
            ]
            lyr_discard.saveFeature(feature_data, geom)
            continue

        feature_data = [
            ('osm_id', osm_id),
            ('name', name),
            ('name_en', name_en),
            ('adminlevel', admin_level),
            ('is_in', None)
        ]

        # process national level boundary
        if admin_level == '1':
            LOG.debug('Writing admin_level=1, feature %s', osm_id)
            lyr_save1.saveFeature(feature_data, geom)
        if admin_level == '2':
            LOG.debug('Writing admin_level=2, feature %s', osm_id)
            lyr_save2.saveFeature(feature_data, geom)
        if admin_level == '3':
            LOG.debug('Writing admin_level=3, feature %s', osm_id)
            lyr_save3.saveFeature(feature_data, geom)
        if admin_level == '4':
            LOG.debug('Writing admin_level=4, feature %s', osm_id)
            lyr_save4.saveFeature(feature_data, geom)
        if admin_level == '5':
            LOG.debug('Writing admin_level=5, feature %s', osm_id)
            lyr_save5.saveFeature(feature_data, geom)
        if admin_level == '6':
            LOG.debug('Writing admin_level=6, feature %s', osm_id)
            lyr_save6.saveFeature(feature_data, geom)
        if admin_level == '7':
            LOG.debug('Writing admin_level=7, feature %s', osm_id)
            lyr_save7.saveFeature(feature_data, geom)
        if admin_level == '8':
            LOG.debug('Writing admin_level=8, feature %s', osm_id)
            lyr_save8.saveFeature(feature_data, geom)
        if admin_level == '9':
            LOG.debug('Writing admin_level=9, feature %s', osm_id)
            lyr_save9.saveFeature(feature_data, geom)
        if admin_level == '10':
            LOG.debug('Writing admin_level=10, feature %s', osm_id)
            lyr_save10.saveFeature(feature_data, geom)

    lyr_read.datasource = None
    lyr_save1.datasource = None
    lyr_save2.datasource = None
    lyr_save3.datasource = None
    lyr_save4.datasource = None
    lyr_save5.datasource = None
    lyr_save6.datasource = None
    lyr_save7.datasource = None
    lyr_save8.datasource = None
    lyr_save9.datasource = None
    lyr_save10.datasource = None
    lyr_discard.datasource = None

if __name__ == '__main__':
    main()
