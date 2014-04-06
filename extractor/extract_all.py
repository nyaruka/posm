#!/usr/bin/python2
# -*- coding: utf-8 -*-
import logging
import logging.config

import shapely.wkb

from exposm.settings import settings

# setup logging, has to be after osmext.settings
logging.config.dictConfig(settings.get('logging'))
logger = logging.getLogger(__file__)

from exposm.writer import FeatureWriter
from exposm.reader import FeatureReader
from exposm.utils import osm_id_exists, check_geom


def main():

    lyr_save0 = FeatureWriter('/tmp/out/admin_level_0.shp')
    lyr_save1 = FeatureWriter('/tmp/out/admin_level_1.shp')
    lyr_save2 = FeatureWriter('/tmp/out/admin_level_2.shp')
    lyr_save3 = FeatureWriter('/tmp/out/admin_level_3.shp')
    lyr_save4 = FeatureWriter('/tmp/out/admin_level_4.shp')
    lyr_save5 = FeatureWriter('/tmp/out/admin_level_5.shp')
    lyr_save6 = FeatureWriter('/tmp/out/admin_level_6.shp')
    lyr_save7 = FeatureWriter('/tmp/out/admin_level_7.shp')
    lyr_save8 = FeatureWriter('/tmp/out/admin_level_8.shp')
    lyr_save9 = FeatureWriter('/tmp/out/admin_level_9.shp')
    lyr_save10 = FeatureWriter('/tmp/out/admin_level_10.shp')

    lyr_read = FeatureReader(settings.get('sources').get('osm_data_file'))

    logger.info('Started exporting admin_level_0 boundaries!')

    for feature in lyr_read.readData():

        # get data
        osm_id = feature.GetField('osm_id')
        admin_level = feature.GetField('admin_level')
        name = feature.GetField('name')
        geom = feature.GetGeometryRef()

        if check_geom(geom, osm_id):
            geom = shapely.wkb.loads(feature.GetGeometryRef().ExportToWkb())
        else:
            # skip further processing
            continue

        # osm_id is crucial for establishing feature relationship
        if not(osm_id_exists(osm_id)):
            logger.warning('Feature without OSM_ID, discarding... "%s"', name)
            continue

        feature.SetField('is_in', None)

        # process national level boundary
        if admin_level == '0':
            logger.debug('Writing admin_level=0, feature %s', osm_id)
            lyr_save0.saveFeature(feature)
        if admin_level == '1':
            logger.debug('Writing admin_level=1, feature %s', osm_id)
            lyr_save1.saveFeature(feature)
        if admin_level == '2':
            logger.debug('Writing admin_level=2, feature %s', osm_id)
            lyr_save2.saveFeature(feature)
        if admin_level == '3':
            logger.debug('Writing admin_level=3, feature %s', osm_id)
            lyr_save3.saveFeature(feature)
        if admin_level == '4':
            logger.debug('Writing admin_level=4, feature %s', osm_id)
            lyr_save4.saveFeature(feature)
        if admin_level == '5':
            logger.debug('Writing admin_level=5, feature %s', osm_id)
            lyr_save5.saveFeature(feature)
        if admin_level == '6':
            logger.debug('Writing admin_level=6, feature %s', osm_id)
            lyr_save6.saveFeature(feature)
        if admin_level == '7':
            logger.debug('Writing admin_level=7, feature %s', osm_id)
            lyr_save7.saveFeature(feature)
        if admin_level == '8':
            logger.debug('Writing admin_level=8, feature %s', osm_id)
            lyr_save8.saveFeature(feature)
        if admin_level == '9':
            logger.debug('Writing admin_level=9, feature %s', osm_id)
            lyr_save9.saveFeature(feature)
        if admin_level == '10':
            logger.debug('Writing admin_level=10, feature %s', osm_id)
            lyr_save10.saveFeature(feature)

    lyr_read.datasource.Destroy()
    lyr_save0.datasource.Destroy()
    lyr_save1.datasource.Destroy()
    lyr_save2.datasource.Destroy()
    lyr_save3.datasource.Destroy()
    lyr_save4.datasource.Destroy()
    lyr_save5.datasource.Destroy()
    lyr_save6.datasource.Destroy()
    lyr_save7.datasource.Destroy()
    lyr_save8.datasource.Destroy()
    lyr_save9.datasource.Destroy()
    lyr_save10.datasource.Destroy()

if __name__ == '__main__':
    main()
