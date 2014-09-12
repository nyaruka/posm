#!/usr/bin/python2
# -*- coding: utf-8 -*-
import logging
import logging.config

LOG = logging.getLogger(__file__)

import argparse

from exposm.writer import AdminLevelWriter, DiscardFeatureWriter
from exposm.reader import AdminLevelReader
from exposm.utils import check_bad_geom, prepare_osm_id

from POSMmanagement.settings import POSMSettings


def main(settings):

    lyr_discard = DiscardFeatureWriter.create_shp('discarded', settings)

    lyr_save1 = AdminLevelWriter.create_shp('admin_level_1', settings)
    lyr_save2 = AdminLevelWriter.create_shp('admin_level_2', settings)
    lyr_save3 = AdminLevelWriter.create_shp('admin_level_3', settings)
    lyr_save4 = AdminLevelWriter.create_shp('admin_level_4', settings)
    lyr_save5 = AdminLevelWriter.create_shp('admin_level_5', settings)
    lyr_save6 = AdminLevelWriter.create_shp('admin_level_6', settings)
    lyr_save7 = AdminLevelWriter.create_shp('admin_level_7', settings)
    lyr_save8 = AdminLevelWriter.create_shp('admin_level_8', settings)
    lyr_save9 = AdminLevelWriter.create_shp('admin_level_9', settings)
    lyr_save10 = AdminLevelWriter.create_shp('admin_level_10', settings)

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
        osm_id = prepare_osm_id(feature, layer)
        if not osm_id:
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


parser = argparse.ArgumentParser(description='Extract admin levels')

parser.add_argument(
    '--settings', default='settings.yaml',
    help='path to the settings file, default: settings.yaml'
)


if __name__ == '__main__':
    # parse the args, and call default function
    args = parser.parse_args()
    proj_settings = POSMSettings(args.settings)

    settings = proj_settings.get_settings()

    logging.config.dictConfig(settings.get('logging'))

    main(settings=settings)
