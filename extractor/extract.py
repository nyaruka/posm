#!/usr/bin/python2
# -*- coding: utf-8 -*-
import logging
import logging.config

import rtree
import shapely.wkb
from shapely.prepared import prep

from exposm.settings import settings, admin_levels

# setup logging, has to be after osmext.settings
logging.config.dictConfig(settings.get('logging'))
logger = logging.getLogger(__file__)

from exposm.writer import AdminLevelWriter
from exposm.reader import AdminLevelReader
from exposm.utils import osm_id_exists, check_bad_geom, intersect_geom


def main():
    unusable_features = set()
    # setup index
    spat_index_0 = rtree.index.Index()
    # extract countries
    admin_level_0 = {}

    lyr_save = AdminLevelWriter.create_shp('admin_level_0')
    lyr_read = AdminLevelReader(settings.get('sources').get('osm_data_file'))

    feature_id = 0

    logger.info('Started exporting admin_level_0 boundaries!')
    for layer, feature in lyr_read.readData():

        # get data
        osm_id = feature.GetField('osm_id')
        admin_level = feature.GetField('admin_level')
        name = feature.GetField('name')
        name_en = feature.GetField('name:en')
        geom_raw = feature.GetGeometryRef()
        feature_data = []

        bad_geom = check_bad_geom(geom_raw, osm_id)
        # BONKERS features usually crash QGIS, we need to skip those
        if bad_geom or not(osm_id_exists(osm_id, name)):
            # add bad geom to the list
            unusable_features.add((layer, osm_id))
            # skip further processing
            continue

        geom = shapely.wkb.loads(geom_raw.ExportToWkb())

        # process national level boundary
        if admin_level == '2':
            feature_data = [
                ('osm_id', osm_id),
                ('name', name),
                ('name_en', name_en),
                ('adminlevel', admin_level),
                ('is_in', None)
            ]
            lyr_save.saveFeature(feature_data, geom_raw)
            admin_level_0.update({osm_id: prep(geom)})
            spat_index_0.insert(
                feature_id, geom.envelope.bounds, obj=osm_id
            )
            logger.debug('Index %s, record %s', feature_id, osm_id)

            feature_id += 1

    lyr_read.datasource.Destroy()
    lyr_save.datasource.Destroy()

    # extract states
    admin_level_1 = {}
    # create index
    spat_index_1 = rtree.index.Index()

    feature_id = 0

    lyr_save = AdminLevelWriter.create_shp('admin_level_1')
    lyr_read = AdminLevelReader(settings.get('sources').get('osm_data_file'))

    for layer, feature in lyr_read.readData():
        osm_id = feature.GetField('osm_id')
        admin_level = feature.GetField('admin_level')
        name = feature.GetField('name')
        name_en = feature.GetField('name:en')
        geom_raw = feature.GetGeometryRef()

        feature_data = []

        if (layer, osm_id) in unusable_features:
            # skip this feature
            logger.debug(
                'Feature previously marked as unusable: %s-%s, skipping',
                layer, osm_id
            )
            continue

        geom = shapely.wkb.loads(geom_raw.ExportToWkb())

        # check spatial relationship
        # representative point is guaranteed within polygon
        geom_repr = geom.representative_point()
        # check index intersection

        is_in = intersect_geom(geom_repr, spat_index_0, admin_level_0)

        # check for specific admin level mapping
        if is_in in admin_levels.get('per_country'):
            search_admin_level = (
                admin_levels['per_country'][is_in]['admin_level_1']
            )
            if search_admin_level:
                logger.info(
                    'Using custom admin_level for %s (%s)',
                    admin_levels.get('per_country')
                    .get(is_in).get('meta').get('name'), is_in
                )
            else:
                # use the default admin_level
                search_admin_level = (
                    admin_levels['default']['admin_level_1']
                )
        elif is_in:
            search_admin_level = (
                admin_levels['default']['admin_level_1']
            )
        else:
            # if we can't determine relationship, skip this feature
            continue

        # check current feature admin level
        if admin_level == str(search_admin_level):

            feature_data = [
                ('osm_id', osm_id),
                ('name', name),
                ('name_en', name_en),
                ('adminlevel', admin_level),
                ('is_in', is_in)
            ]
            lyr_save.saveFeature(feature_data, geom_raw)

            admin_level_1.update({osm_id: prep(geom)})
            spat_index_1.insert(
                feature_id, geom.envelope.bounds, obj=osm_id
            )
            logger.debug('Index %s, record %s', feature_id, osm_id)

            feature_id += 1

    lyr_read.datasource.Destroy()
    lyr_save.datasource.Destroy()

    # extract counties
    lyr_save = AdminLevelWriter.create_shp('admin_level_2')
    lyr_read = AdminLevelReader(settings.get('sources').get('osm_data_file'))

    for layer, feature in lyr_read.readData():

        osm_id = feature.GetField('osm_id')
        admin_level = feature.GetField('admin_level')
        name = feature.GetField('name')
        name_en = feature.GetField('name:en')
        geom_raw = feature.GetGeometryRef()

        feature_data = []

        if (layer, osm_id) in unusable_features:
            # skip this feature
            logger.debug(
                'Feature previously marked as unusable: %s-%s, skipping',
                layer, osm_id
            )
            continue

        geom = shapely.wkb.loads(geom_raw.ExportToWkb())

        # representative point is guaranteed within polygon
        geom_repr = geom.representative_point()

        is_in = intersect_geom(geom_repr, spat_index_0, admin_level_0)

        is_in_state = intersect_geom(geom_repr, spat_index_1, admin_level_1)

        # check for specific admin level mapping
        if is_in in admin_levels.get('per_country'):
            search_admin_level = (
                admin_levels.get('per_country')
                .get(is_in)
                .get('admin_level_2')
            )
            if search_admin_level:
                logger.info(
                    'Using custom admin_level for %s (%s)',
                    admin_levels.get('per_country')
                    .get(is_in).get('meta').get('name'), is_in
                )
            else:
                # use the default admin_level
                search_admin_level = (
                    admin_levels.get('default').get('admin_level_2')
                )
        elif is_in:
            search_admin_level = (
                admin_levels.get('default').get('admin_level_2')
            )
        else:
            # if we can't determine relationship, skip this feature
            continue

        if not(is_in_state):
            # if we can't determine relationship, skip this feature
            continue

        # check current feature admin level
        if admin_level == str(search_admin_level):
            feature_data = [
                ('osm_id', osm_id),
                ('name', name),
                ('name_en', name_en),
                ('adminlevel', admin_level),
                ('is_in', is_in_state)
            ]
            lyr_save.saveFeature(feature_data, geom_raw)

    lyr_read.datasource.Destroy()
    lyr_save.datasource.Destroy()


if __name__ == '__main__':
    main()
