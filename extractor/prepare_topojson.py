#!/usr/bin/python2
# -*- coding: utf-8 -*-
import logging
import logging.config

import os
import os.path

import subprocess

from osgeo import ogr, osr

from exposm.settings import settings
# setup logging, has to be after exposm.settings
logging.config.dictConfig(settings.get('logging'))
logger = logging.getLogger(__file__)

# define global SRS
SRS = osr.SpatialReference()
SRS.ImportFromEPSG(4326)

database = settings.get('exposm').get('postgis')
driver = ogr.GetDriverByName('PostgreSQL')
datasource = ogr.Open(database)

simple_ad0 = datasource.GetLayerByName('simple_admin_0_view')
simple_ad1 = datasource.GetLayerByName('simple_admin_1_view')
simple_ad2 = datasource.GetLayerByName('simple_admin_2_view')


def create_GEOJSON(path):
    # geoJSON datasource
    GEOJSON_driver = ogr.GetDriverByName('GEOJson')
    GEOJSON_datasource = GEOJSON_driver.CreateDataSource(
        os.path.join(path, 'geometry.geojson')
    )

    layer = GEOJSON_datasource.CreateLayer(
        'boundary', SRS, ogr.wkbMultiPolygon,
        # options=['COORDINATE_PRECISION=2']
    )

    # define fields
    osm_id_def = ogr.FieldDefn('osm_id', ogr.OFTString)
    osm_id_def.SetWidth(254)

    boundary_def = ogr.FieldDefn('is_boundary', ogr.OFTInteger)

    layer.CreateField(osm_id_def)
    layer.CreateField(boundary_def)

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


def convert_to_topojson(path):
    # cur_path = os.getcwd()
    # os.chdir(path)
    geojson_path = os.path.join(path, 'geometry.geojson')
    topojson_path = os.path.join(path, 'geometry.topojson')
    logger.info('Converting %s to %s', geojson_path, topojson_path)
    result = subprocess.call(
        ['topojson', '-p', '-o', topojson_path, geojson_path],
        stdout=open(os.devnull, 'wb'),  # make it silent
        stderr=open(os.devnull, 'wb')
    )

    if result:
        logger.error('Cannot convert to topojson...')

feature0 = simple_ad0.GetNextFeature()
while feature0:
    ad0_osm_id = feature0.GetField('osm_id')

    ad0_dir = os.path.join(
        settings.get('exposm').get('geojson_output_directory'),
        ad0_osm_id
    )
    logger.info('Creating ad0 directory: %s', ad0_dir)
    os.mkdir(ad0_dir)

    geojson_datasource_country = create_GEOJSON(ad0_dir)

    simple_ad1.SetAttributeFilter(
        'is_in_country=\'{}\''.format(ad0_osm_id)
    )
    feature1 = simple_ad1.GetNextFeature()

    while feature1:
        ad1_osm_id = feature1.GetField('osm_id')
        ad1_dir = os.path.join(
            settings.get('exposm').get('geojson_output_directory'),
            ad0_osm_id, ad1_osm_id
        )

        logger.info('Creating ad1 directory: %s', ad1_dir)
        os.mkdir(ad1_dir)

        # create state level geojson
        geojson_datasource_state = create_GEOJSON(ad1_dir)

        simple_ad2.SetAttributeFilter(
            'is_in_state=\'{}\''.format(ad1_osm_id)
        )
        feature2 = simple_ad2.GetNextFeature()

        while feature2:
            ad2_osm_id = feature2.GetField('osm_id')
            # write feature to the state.geojson
            write_feature(
                geojson_datasource_state,
                [('osm_id', ad2_osm_id)],
                feature2.GetGeomFieldRef(0)
            )

            # read next ad2 feature
            feature2 = simple_ad2.GetNextFeature()

        # write feature as a boundary to the state.geojson
        write_feature(
            geojson_datasource_state,
            [('osm_id', ad1_osm_id), ('is_boundary', 1)],
            feature1.GetGeomFieldRef(0)
        )
        # write feature to the country.geojson
        write_feature(
            geojson_datasource_country,
            [('osm_id', ad1_osm_id)],
            feature1.GetGeomFieldRef(0)
        )
        # write feature to the state.geojson
        geojson_datasource_state = None
        convert_to_topojson(ad1_dir)
        # read next ad1 feature
        feature1 = simple_ad1.GetNextFeature()

    # write feature as a boundary to the country.geojson
    write_feature(
        geojson_datasource_country,
        [('osm_id', ad0_osm_id), ('is_boundary', 1)],
        feature0.GetGeomFieldRef(0)
    )
    geojson_datasource_country = None
    convert_to_topojson(ad0_dir)
    # read next ad0 feature
    feature0 = simple_ad0.GetNextFeature()
