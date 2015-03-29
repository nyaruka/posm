#!/usr/bin/python2
# -*- coding: utf-8 -*-
import logging
import logging.config
LOG = logging.getLogger(__file__)

import itertools
import os
import sys

import ogr
import osr

import shapely.wkb
import shapely.geometry

import argparse

from POSMmanagement.settings import POSMSettings
from POSMmanagement.utils import is_file_readable
from exposm.reader import AdminLevelReader
from exposm.utils import prepare_osm_id, check_bad_geom


def create_GEOJSON(path, filename):
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)

    abspath = os.path.join(path, filename)
    # remove file if it exists, GDAL can't overwrite exiting geojson files
    if os.path.isfile(abspath):
        os.unlink(abspath)

    # geoJSON datasource
    GEOJSON_driver = ogr.GetDriverByName('GEOJson')
    GEOJSON_datasource = GEOJSON_driver.CreateDataSource(abspath)

    layer = GEOJSON_datasource.CreateLayer(
        'boundary', srs, ogr.wkbMultiPolygon
    )

    # define fields
    osm_id_def = ogr.FieldDefn('osm_id', ogr.OFTString)
    osm_id_def.SetWidth(254)

    layer.CreateField(osm_id_def)

    return GEOJSON_datasource


def checkGeom(geom, buf_geom, sim_geom, bufferDistance, simplifyDistance):
    while not(sim_geom.contains(geom)):
        # simplified geometry does not contains original geometry
        # try to reduce simplification distance by 10%
        simplifyDistance -= simplifyDistance * 0.1
        LOG.debug('Reducing simplifyDistance to ... %s', simplifyDistance)

        sim_geom = buf_geom.simplify(simplifyDistance)
        if sim_geom.contains(geom):
            # it's ok
            break

        # try to increase buffer by 10%
        bufferDistance += bufferDistance * 0.1
        LOG.debug('Increasing bufferDistance to ... %s', bufferDistance)
        buf_geom = geom.buffer(bufferDistance)
        sim_geom = buf_geom.simplify(simplifyDistance)

    return sim_geom


def createPolys(
        feature, abspath, bufferDistance, simplifyDistance, geojson, osm_id):
    feat_iso = feature.GetField('ISO3166-1')

    if not(feat_iso):
        return None

    polyName = '{}_{}'.format(feat_iso, osm_id)
    polyFilename = '{}.poly'.format(polyName)
    full_path = os.path.join(abspath, polyFilename)
    LOG.info('Creating %s ...', full_path)

    f = open(full_path, 'wt')
    print >>f, polyName

    # this will be a polygon, TODO: handle linestrings (must be buffered)
    geom = feature.GetGeometryRef()
    geomType = geom.GetGeometryType()

    nonAreaTypes = [
        ogr.wkbPoint, ogr.wkbLineString, ogr.wkbMultiPoint,
        ogr.wkbMultiLineString
    ]
    if geomType in nonAreaTypes and bufferDistance == 0:
        LOG.error(
            'Ignoring non-area geom, you must set a buffer distance.'
        )
        return None
    if geomType in [ogr.wkbUnknown, ogr.wkbNone]:
        LOG.error('Ignoring unknown geometry type.')
        return None

    geom = shapely.wkb.loads(geom.ExportToWkb())

    buf_geom = geom.buffer(bufferDistance)
    sim_geom = buf_geom.simplify(simplifyDistance)

    fin_geom = checkGeom(
        geom, buf_geom, sim_geom, bufferDistance, simplifyDistance
    )

    if fin_geom.geom_type == 'Polygon':
        fin_geom = shapely.geometry.MultiPolygon([fin_geom])
    LOG.debug('# of polygons: %s', len(fin_geom.geoms))
    for g in fin_geom.geoms:
        # loop over all rings in the polygon
        LOG.debug('# of rings: %s', len(g.interiors))
        for i, ring in enumerate(itertools.chain([g.exterior], g.interiors)):
            if i == 0:
                # outer ring
                print >>f, i + 1
            else:
                # inner ring
                print >>f, '!%d' % (i + 1)

            if len(ring.coords) > 0:
                LOG.debug('# of points: %s', len(ring.coords))
            else:
                LOG.warn('Ring with no points')

            # output all points in the ring
            for j, coord in enumerate(ring.coords):
                (x, y) = coord
                print >>f, '   %.6E   %.6E' % (x, y)
            print >>f, 'END'
    print >>f, 'END'
    f.close()

    if geojson:
        jsonFilename = '{}.geojson'.format(polyName)

        # write geoJSON
        geojson_poly = create_GEOJSON(abspath, jsonFilename)
        layer = geojson_poly.GetLayer(0)

        new_feat = ogr.Feature(layer.GetLayerDefn())
        new_feat.SetField('osm_id', osm_id)

        # set geometry for the feature
        new_feat.SetGeometry(ogr.CreateGeometryFromWkb(fin_geom.wkb))
        # add feature to the layer
        layer.CreateFeature(new_feat)

        # write geojson
        geojson_poly = None


def main(settings, directory, bufferDistance, simplifyDistance, geojson):
    abspath = os.path.abspath(directory)

    if os.path.isdir(abspath):
        if not(os.access(abspath, os.W_OK)):
            LOG.error('Missing write permission: %s', abspath)
            sys.exit(99)
    else:
        LOG.error('Directory not found: %s', abspath)
        sys.exit(99)

    admin_level_data_path = os.path.join(
        settings.get('sources').get('data_directory'),
        '{}.pbf'.format(settings.get('sources').get('admin_levels_file'))
    )
    if not(is_file_readable(admin_level_data_path)):
        sys.exit(99)

    lyr_read = AdminLevelReader(admin_level_data_path)

    for layer, feature in lyr_read.readData():
        # get data
        osm_id = prepare_osm_id(feature, layer)
        if not osm_id:
            continue

        admin_level = feature.GetField('admin_level')

        geom_raw = feature.GetGeometryRef()

        bad_geom = check_bad_geom(geom_raw, osm_id)
        # BONKERS features usually crash QGIS, we need to skip those

        if bad_geom:
            # skip further processing
            continue

        if feature.GetField('boundary') != 'administrative':
            # skip further processing
            continue

        # process national level boundary
        if admin_level == '2':
            createPolys(
                feature, abspath, bufferDistance, simplifyDistance, geojson,
                osm_id
            )


parser = argparse.ArgumentParser(
    description='Extract poly files from the database'
)

parser.add_argument(
    '--settings', default='settings.yaml',
    help='path to the settings file, default: settings.yaml'
)

parser.add_argument(
    '--buffer', default=0, help='buffer distance in degrees, default: 0',
    type=float
)

parser.add_argument(
    '--simplify', default=0, help='simplify tolerance in degrees, default: 0',
    type=float
)

parser.add_argument(
    '--output_dir', default='poly', help='output directory, default: poly'
)

parser.add_argument(
    '--geojson', action='store_true', default=False,
    help='create GEOJson files of poly geometry'
)

if __name__ == '__main__':
    # parse the args, and call default function
    args = parser.parse_args()
    proj_settings = POSMSettings(args.settings)

    settings = proj_settings.get_settings()
    admin_levels = proj_settings.get_admin_levels()

    logging.config.dictConfig(settings.get('logging'))

    main(
        settings=settings, directory=args.output_dir,
        bufferDistance=args.buffer, simplifyDistance=args.simplify,
        geojson=args.geojson
    )
