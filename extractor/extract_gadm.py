#!/usr/bin/python2
# -*- coding: utf-8 -*-
import logging
import logging.config

from osgeo import ogr

LOG = logging.getLogger(__file__)

import argparse
import sys
import zipfile
import tempfile
import glob

import rtree
import shapely.wkb
from shapely.prepared import prep

from POSMmanagement.settings import POSMSettings
from POSMmanagement.utils import is_file_readable

# setup logging, has to be after osmext.settings
from exposm.writer import AdminLevelWriter
from exposm.reader import GADMAdminLevelReader
from exposm.utils import (
    check_bad_geom, intersect_geom, create_GEOJSON,
    writeProblem
)


def extractGADMArchive(filepath):
    LOG.debug('Extracting GADM archive: %s', filepath)

    tmpDir = tempfile.mkdtemp(suffix='_gadm')

    with zipfile.ZipFile(filepath, 'r') as zip_ref:
        zip_ref.extractall(tmpDir)

    return sorted(glob.glob('{}/*.shp'.format(tmpDir)))


def main(settings, problems_geojson):

    if problems_geojson:
        problems_datasource = create_GEOJSON('', 'problems.geojson')

    adm_0_temp = set()
    adm_1_temp = set()
    adm_2_temp = set()
    adm_3_temp = set()

    unusable_features = set()
    # setup index
    spat_index_0 = rtree.index.Index()
    # extract countries
    admin_level_0 = {}

    lyr_save = AdminLevelWriter.create_postgis('admin_level_0', settings)

    admin_files = extractGADMArchive(settings.get('gadm_source').get('shp_package'))
    LOG.debug('Admin files: {}'.format(admin_files))

    if not(all(is_file_readable(admin_path) for admin_path in admin_files)):
        sys.exit(99)

    lyr_read = GADMAdminLevelReader(admin_files[0])

    feature_id = 0

    LOG.info('Started exporting admin_level_0 boundaries!')
    for layer, feature in lyr_read.readData():

        osm_id = '{}0'.format(feature.GetField('ADM0_PCODE'))  # append 0 to the osm_id to satisfy import_geojson checks
        name = feature.GetField('ADM0_EN')
        name_en = feature.GetField('ADM0_EN')
        # iso3166 = 'NG'
        geom_raw = ogr.ForceToMultiPolygon(feature.GetGeometryRef())

        feature_data = (
            ('osm_id', osm_id),
            ('name', name),
            ('name_en', name_en),
            ('adminlevel', 0),
            ('iso3166', osm_id),
            ('is_in', None)
        )

        bad_geom = check_bad_geom(geom_raw, osm_id)
        # BONKERS features usually crash QGIS, we need to skip those
        if bad_geom:
            # add bad geom to the list
            unusable_features.add(osm_id)
            # skip further processing
            if problems_geojson:
                writeProblem(problems_datasource, osm_id, bad_geom)
            continue

        geom = shapely.wkb.loads(bytes(geom_raw.ExportToWkb()))

        lyr_save.saveFeature(feature_data, geom_raw)
        admin_level_0.update({osm_id: prep(geom)})
        spat_index_0.insert(
            feature_id, geom.envelope.bounds, obj=osm_id
        )
        LOG.debug('Index %s, record %s', feature_id, osm_id)

        feature_id += 1

    lyr_read.datasource = None
    lyr_save.datasource = None

    # write geojson problems file
    if problems_geojson:
        problems_datasource = None

    # extract states
    admin_level_1 = {}
    # create index
    spat_index_1 = rtree.index.Index()

    feature_id = 0

    lyr_save = AdminLevelWriter.create_postgis('admin_level_1', settings)

    if len(admin_files) < 2:
        lyr_save = None
    else:
        lyr_read = GADMAdminLevelReader(admin_files[1])

        for layer, feature in lyr_read.readData():
            osm_id = feature.GetField('ADM1_PCODE')
            name = feature.GetField('ADM1_EN')
            name_en = feature.GetField('ADM1_EN')
            geom_raw = ogr.ForceToMultiPolygon(feature.GetGeometryRef())

            if osm_id in unusable_features:
                # skip this feature
                LOG.debug(
                    'Feature previously marked as unusable: %s, skipping', osm_id
                )
                continue

            geom = shapely.wkb.loads(bytes(geom_raw.ExportToWkb()))

            # check spatial relationship
            # representative point is guaranteed within polygon
            geom_repr = geom.representative_point()
            # check index intersection

            is_in = intersect_geom(geom_repr, spat_index_0, admin_level_0)

            if not(is_in):
                # if we can't determine relationship, skip this feature
                LOG.info('Missing country information ... %s', osm_id)
                continue

            feature_data = (
                ('osm_id', osm_id),
                ('name', name),
                ('name_en', name_en),
                ('adminlevel', 1),
                ('iso3166', None),
                ('is_in', is_in)
            )

            lyr_save.saveFeature(feature_data, geom_raw)
            admin_level_1.update({osm_id: prep(geom)})
            spat_index_1.insert(
                feature_id, geom.envelope.bounds, obj=osm_id
            )
            LOG.debug('Index %s, record %s', feature_id, osm_id)

            feature_id += 1

            adm_1_temp.add(osm_id)

        lyr_read.datasource = None
        lyr_save.datasource = None

    # extract states
    admin_level_2 = {}
    # create index
    spat_index_2 = rtree.index.Index()

    feature_id = 0

    # extract counties
    lyr_save = AdminLevelWriter.create_postgis('admin_level_2', settings)

    if len(admin_files) < 3:
        lyr_save = None
    else:
        lyr_read = GADMAdminLevelReader(admin_files[2])

        for layer, feature in lyr_read.readData():

            osm_id = feature.GetField('ADM2_PCODE')
            name = feature.GetField('ADM2_EN')
            name_en = feature.GetField('ADM2_EN')
            geom_raw = ogr.ForceToMultiPolygon(feature.GetGeometryRef())

            if osm_id in unusable_features:
                # skip this feature
                LOG.debug(
                    'Feature previously marked as unusable: %s, skipping', osm_id
                )
                continue

            geom = shapely.wkb.loads(bytes(geom_raw.ExportToWkb()))

            # representative point is guaranteed within polygon
            geom_repr = geom.representative_point()

            is_in = intersect_geom(geom_repr, spat_index_0, admin_level_0)

            is_in_state = intersect_geom(geom_repr, spat_index_1, admin_level_1)

            if not(is_in_state):
                # if we can't determine relationship, skip this feature
                LOG.info('Missing state information ... %s', osm_id)
                continue

            feature_data = (
                ('osm_id', osm_id),
                ('name', name),
                ('name_en', name_en),
                ('adminlevel', 2),
                ('iso3166', None),
                ('is_in', is_in_state)
            )

            lyr_save.saveFeature(feature_data, geom_raw)
            admin_level_2.update({osm_id: prep(geom)})
            spat_index_2.insert(
                feature_id, geom.envelope.bounds, obj=osm_id
            )
            LOG.debug('Index %s, record %s', feature_id, osm_id)

            feature_id += 1

            adm_2_temp.add(osm_id)

        lyr_read.datasource = None
        lyr_save.datasource = None


    # extract district
    admin_level_3 = {}
    # create index
    spat_index_3 = rtree.index.Index()

    feature_id = 0

    # extract counties
    lyr_save = AdminLevelWriter.create_postgis('admin_level_3', settings)

    if len(admin_files) < 4:
        lyr_save = None
    else:
        lyr_read = GADMAdminLevelReader(admin_files[3])

        for layer, feature in lyr_read.readData():

            osm_id = feature.GetField('ADM3_PCODE')
            name = feature.GetField('ADM3_EN')
            name_en = feature.GetField('ADM3_EN')
            geom_raw = ogr.ForceToMultiPolygon(feature.GetGeometryRef())

            if osm_id in unusable_features:
                # skip this feature
                LOG.debug(
                    'Feature previously marked as unusable: %s, skipping', osm_id
                )
                continue

            geom = shapely.wkb.loads(bytes(geom_raw.ExportToWkb()))

            # representative point is guaranteed within polygon
            geom_repr = geom.representative_point()

            is_in = intersect_geom(geom_repr, spat_index_0, admin_level_0)

            is_in_state = intersect_geom(geom_repr, spat_index_1, admin_level_1)

            is_in_district = intersect_geom(geom_repr, spat_index_2, admin_level_2)

            if not(is_in_district):
                # if we can't determine relationship, skip this feature
                LOG.info('Missing state information ... %s', osm_id)
                continue

            feature_data = (
                ('osm_id', osm_id),
                ('name', name),
                ('name_en', name_en),
                ('adminlevel', 3),
                ('iso3166', None),
                ('is_in', is_in_district)
            )

            lyr_save.saveFeature(feature_data, geom_raw)
            admin_level_3.update({osm_id: prep(geom)})
            spat_index_3.insert(
                feature_id, geom.envelope.bounds, obj=osm_id
            )
            LOG.debug('Index %s, record %s', feature_id, osm_id)

            feature_id += 1

            adm_3_temp.add(osm_id)

        lyr_read.datasource = None
        lyr_save.datasource = None


parser = argparse.ArgumentParser(description='Extract admin levels (GADM)')

parser.add_argument(
    '--settings', default='settings.yaml',
    help='path to the settings file, default: settings.yaml'
)

parser.add_argument(
    '--problems_as_geojson', action='store_true', default=False,
    help='Generate problems.geojson in the current directory'
)

if __name__ == '__main__':
    # parse the args, and call default function
    args = parser.parse_args()
    proj_settings = POSMSettings(args.settings)

    settings = proj_settings.get_settings()

    logging.config.dictConfig(settings.get('logging'))

    main(
        settings=settings, problems_geojson=args.problems_as_geojson
    )
