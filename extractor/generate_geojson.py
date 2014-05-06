#!/usr/bin/python2
# -*- coding: utf-8 -*-
import logging
import logging.config

import os
import os.path
import argparse

import shutil

from osgeo import ogr, osr

from exposm.settings import settings
# setup logging, has to be after exposm.settings
logging.config.dictConfig(settings.get('logging'))
logger = logging.getLogger(__file__)

# define a simple argparser
parser = argparse.ArgumentParser(
    description='Generate geojson files for osm_id'
)

group = parser.add_mutually_exclusive_group()

group.add_argument(
    'osm_ids', metavar='osm_id', type=str, nargs='*',
    help='an osm_id of admin_level_0 feature', default=[]
)

group.add_argument(
    '--all', action='store_true',
    help='extract everything from the database'
)

parser.add_argument(
    '--rm', action='store_true', help='clean out temporary directory'
)

cli_args = parser.parse_args()

# define global SRS
SRS = osr.SpatialReference()
SRS.ImportFromEPSG(4326)

database = settings.get('exposm').get('postgis')
driver = ogr.GetDriverByName('PostgreSQL')
datasource = ogr.Open(database)

simple_ad0 = datasource.GetLayerByName('simple_admin_0_view')
simple_ad1 = datasource.GetLayerByName('simple_admin_1_view')
simple_ad2 = datasource.GetLayerByName('simple_admin_2_view')


def create_GEOJSON(path, filename):
    # geoJSON datasource
    GEOJSON_driver = ogr.GetDriverByName('GEOJson')
    GEOJSON_datasource = GEOJSON_driver.CreateDataSource(
        os.path.join(path, filename)
    )

    layer = GEOJSON_datasource.CreateLayer(
        'boundary', SRS, ogr.wkbMultiPolygon,
        # options=['COORDINATE_PRECISION=2']
    )

    # define fields
    osm_id_def = ogr.FieldDefn('osm_id', ogr.OFTString)
    osm_id_def.SetWidth(254)

    layer.CreateField(osm_id_def)

    is_in_c_def = ogr.FieldDefn('is_in_country', ogr.OFTString)
    is_in_c_def.SetWidth(254)

    layer.CreateField(is_in_c_def)

    is_in_s_def = ogr.FieldDefn('is_in_state', ogr.OFTString)
    is_in_s_def.SetWidth(254)

    layer.CreateField(is_in_s_def)

    return GEOJSON_datasource


def write_feature(datasource, feature_data, feature_geom):
    layer = datasource.GetLayer(0)

    new_feat = ogr.Feature(layer.GetLayerDefn())

    for field in feature_data:
        new_feat.SetField(field[0], field[1])

    # set geometry for the feature
    new_feat.SetGeometry(feature_geom)
    # add feature to the layer
    layer.CreateFeature(new_feat)

    new_feat = None


def create_archive():
    """
    Use shutil make_archive to create a zip archive of created geojson files
    """
    shutil.make_archive(
        base_name='exported_geojson',
        format='zip',
        root_dir=settings.get('exposm').get('geojson_output_directory'),
        base_dir='.'
    )


# use provided arguments
if cli_args.rm:
    directory = settings.get('exposm').get('geojson_output_directory')
    if os.path.exists(directory):
        shutil.rmtree(directory)
    os.mkdir(settings.get('exposm').get('geojson_output_directory'))

if cli_args.all:
    args_list = []
    feature0 = simple_ad0.GetNextFeature()
    while feature0:
        ad0_osm_id = feature0.GetField('osm_id')
        args_list.append(ad0_osm_id)
        feature0 = simple_ad0.GetNextFeature()
    osm_ids = args_list

else:
    osm_ids = cli_args.osm_ids

for osm_id in osm_ids:
    simple_ad0.SetAttributeFilter('osm_id=\'{}\''.format(osm_id))
    feature0 = simple_ad0.GetNextFeature()
    if feature0:
        logger.info('Found feature %s ...', osm_id)
        ad0_osm_id = feature0.GetField('osm_id')
        ad0_is_in_c = None
        ad0_is_in_s = None

        ad0_attrs = [
            ('osm_id', ad0_osm_id), ('is_in_country', ad0_is_in_c),
            ('is_in_state', ad0_is_in_s)
        ]

        filename = '{}admin{}{}.json'.format(ad0_osm_id, 0, '')

        geojson_ds_country_normal = create_GEOJSON(
            settings.get('exposm').get('geojson_output_directory'),
            filename
        )
        write_feature(
            geojson_ds_country_normal, ad0_attrs,
            feature0.GetGeomFieldRef(1)
        )

        geojson_ds_country_normal = None

        filename_sim = '{}admin{}{}.json'.format(ad0_osm_id, 0, '_simplified')

        geojson_ds_country_simple = create_GEOJSON(
            settings.get('exposm').get('geojson_output_directory'),
            filename_sim
        )
        write_feature(
            geojson_ds_country_simple, ad0_attrs,
            feature0.GetGeomFieldRef(0)
        )

        geojson_ds_country_simple = None

        filename1 = '{}admin{}{}.json'.format(ad0_osm_id, 1, '')
        filename1_sim = '{}admin{}{}.json'.format(ad0_osm_id, 1, '_simplified')
        geojson_ds_state_normal = create_GEOJSON(
            settings.get('exposm').get('geojson_output_directory'),
            filename1
        )
        geojson_ds_state_simple = create_GEOJSON(
            settings.get('exposm').get('geojson_output_directory'),
            filename1_sim
        )

        # extract states for a country
        simple_ad1.SetAttributeFilter(
            'is_in_country=\'{}\''.format(ad0_osm_id)
        )
        feature1 = simple_ad1.GetNextFeature()

        while feature1:
            ad1_osm_id = feature1.GetField('osm_id')
            ad1_is_in_c = feature1.GetField('is_in_country')
            ad1_is_in_s = None

            ad1_attrs = [
                ('osm_id', ad1_osm_id), ('is_in_country', ad1_is_in_c),
                ('is_in_state', ad1_is_in_s)
            ]

            write_feature(
                geojson_ds_state_normal, ad1_attrs,
                feature1.GetGeomFieldRef(1)
            )
            write_feature(
                geojson_ds_state_simple, ad1_attrs,
                feature1.GetGeomFieldRef(0)
            )

            feature1 = simple_ad1.GetNextFeature()
        # write feature to the state.geojson
        geojson_ds_country_simple = None
        geojson_ds_country_normal = None

        # extract counties for a country
        filename2 = '{}admin{}{}.json'.format(ad0_osm_id, 2, '')
        filename2_sim = '{}admin{}{}.json'.format(ad0_osm_id, 2, '_simplified')
        geojson_ds_county_normal = create_GEOJSON(
            settings.get('exposm').get('geojson_output_directory'),
            filename2
        )
        geojson_ds_county_simple = create_GEOJSON(
            settings.get('exposm').get('geojson_output_directory'),
            filename2_sim
        )
        # extract states for a country
        simple_ad2.SetAttributeFilter(
            'is_in_country=\'{}\''.format(ad0_osm_id)
        )
        feature2 = simple_ad2.GetNextFeature()

        while feature2:
            ad2_osm_id = feature2.GetField('osm_id')
            ad2_is_in_c = feature2.GetField('is_in_country')
            ad2_is_in_s = feature2.GetField('is_in_state')

            ad2_attrs = [
                ('osm_id', ad2_osm_id), ('is_in_country', ad2_is_in_c),
                ('is_in_state', ad2_is_in_s)
            ]

            write_feature(
                geojson_ds_county_normal, ad2_attrs,
                feature2.GetGeomFieldRef(1)
            )
            write_feature(
                geojson_ds_county_simple, ad2_attrs,
                feature2.GetGeomFieldRef(0)
            )

            feature2 = simple_ad2.GetNextFeature()
        # write feature to the state.geojson
        geojson_ds_county_simple = None
        geojson_ds_ccounty_normal = None

    else:
        logger.warning('Feature %s is missing ...', osm_id)

if osm_ids:
    logger.info('Creating archive in the current directory...')
    create_archive()
