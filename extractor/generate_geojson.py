#!/usr/bin/python2
# -*- coding: utf-8 -*-
import logging
import logging.config

LOG = logging.getLogger(__file__)

import os
import os.path
import argparse

import shutil
import subprocess

from osgeo import ogr, osr

from POSMmanagement.settings import POSMSettings


# define a simple argparser
parser = argparse.ArgumentParser(
    description='Generate geojson files for osm_id'
)

group = parser.add_mutually_exclusive_group()

group.add_argument(
    'osm_ids', metavar='osm_id', type=str, nargs='*',
    help=(
        'an osm_id of an admin_level_0 feature or an iso code, for example '
        'isoNG will select a country with iso3166 code NG'),
    default=[]
)

group.add_argument(
    '--all', action='store_true',
    help='extract everything from the database'
)

parser.add_argument(
    '--rm', action='store_true', help='clean out temporary directory'
)

parser.add_argument(
    '--settings', default='settings.yaml',
    help='path to the settings file, default: settings.yaml'
)


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

    name_def = ogr.FieldDefn('name', ogr.OFTString)
    name_def.SetWidth(254)

    layer.CreateField(name_def)

    name_en_def = ogr.FieldDefn('name_en', ogr.OFTString)
    name_en_def.SetWidth(254)

    layer.CreateField(name_en_def)

    iso3166_def = ogr.FieldDefn('iso3166', ogr.OFTString)
    iso3166_def.SetWidth(254)

    layer.CreateField(iso3166_def)

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


def create_archive(directory, name):
    """
    Use subprocess call to 'zip' to create a zip archive of created geojson
    files

    ..Note: built-in module zipfile was creating correct zip files with
    corrupted files
    """
    filename = os.path.join(directory, '%s_exported_geojson.zip' % name)
    LOG.info(f"Creating {filename} ..")

    if os.path.exists(filename):
        os.unlink(filename)

    result = subprocess.call([
        'zip', '-j', '-r', filename,
        settings.get('exposm').get('geojson_output_directory')
    ],
        stdout=open(os.devnull, 'wb'),  # make it silent
        stderr=open(os.devnull, 'wb')
    )
    if result:
        LOG.error('Problem creating ZIP archive...')
    else:
        LOG.info(".. success!")


def main(settings, cli_args):
    database = settings.get('exposm').get('postgis')
    # driver = ogr.GetDriverByName('PostgreSQL')
    datasource = ogr.Open(database)

    simple_ad0 = datasource.GetLayerByName('simple_admin_0_view')
    simple_ad1 = datasource.GetLayerByName('simple_admin_1_view')
    simple_ad2 = datasource.GetLayerByName('simple_admin_2_view')

    # use provided arguments
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
        if osm_id[:3] == 'iso':
            simple_ad0.SetAttributeFilter(
                'iso3166=\'{}\''.format(osm_id[3:].upper())
            )
        else:
            simple_ad0.SetAttributeFilter('osm_id=\'{}\''.format(osm_id))
        feature0 = simple_ad0.GetNextFeature()
        if feature0:
            LOG.info('Found feature %s ...', osm_id)
            ad0_osm_id = feature0.GetField('osm_id')
            ad0_name = feature0.GetField('name')
            ad0_name_en = feature0.GetField('name_en')
            ad0_iso3166 = feature0.GetField('iso3166')
            ad0_is_in_c = None
            ad0_is_in_s = None

            ad0_attrs = [
                ('osm_id', ad0_osm_id), ('is_in_country', ad0_is_in_c),
                ('is_in_state', ad0_is_in_s), ('name', ad0_name),
                ('name_en', ad0_name_en), ('iso3166', ad0_iso3166)
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

            filename_sim = '{}admin{}{}.json'.format(
                ad0_osm_id, 0, '_simplified'
            )

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
            filename1_sim = '{}admin{}{}.json'.format(
                ad0_osm_id, 1, '_simplified'
            )
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
                ad1_name = feature1.GetField('name')
                ad1_name_en = feature1.GetField('name_en')
                ad1_is_in_s = None
                ad1_iso3166 = None

                ad1_attrs = [
                    ('osm_id', ad1_osm_id), ('is_in_country', ad1_is_in_c),
                    ('is_in_state', ad1_is_in_s), ('name', ad1_name),
                    ('name_en', ad1_name_en), ('iso3166', ad1_iso3166)
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
            geojson_ds_state_simple = None
            geojson_ds_state_normal = None

            # extract counties for a country
            filename2 = '{}admin{}{}.json'.format(ad0_osm_id, 2, '')
            filename2_sim = '{}admin{}{}.json'.format(
                ad0_osm_id, 2, '_simplified'
            )
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
                ad2_name = feature2.GetField('name')
                ad2_name_en = feature2.GetField('name_en')
                ad2_is_in_c = feature2.GetField('is_in_country')
                ad2_is_in_s = feature2.GetField('is_in_state')
                ad2_iso3166 = None

                ad2_attrs = [
                    ('osm_id', ad2_osm_id), ('is_in_country', ad2_is_in_c),
                    ('is_in_state', ad2_is_in_s), ('name', ad2_name),
                    ('name_en', ad2_name_en), ('iso3166', ad2_iso3166)
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
            geojson_ds_county_normal = None

        else:
            LOG.warning('Feature %s is missing ...', osm_id)

    if osm_ids:
        create_archive(settings.get('sources').get('data_directory'), ad0_osm_id)


if __name__ == '__main__':
    # parse the args, and call default function
    args = parser.parse_args()
    proj_settings = POSMSettings(args.settings)

    settings = proj_settings.get_settings()

    logging.config.dictConfig(settings.get('logging'))

    # define global SRS
    SRS = osr.SpatialReference()
    SRS.ImportFromEPSG(4326)

    main(settings=settings, cli_args=args)
