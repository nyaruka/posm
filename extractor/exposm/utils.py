import logging
LOG = logging.getLogger(__file__)

from osgeo import osr
from osgeo import ogr

import os

import shapely.wkb
from shapely.validation import explain_validity


def prepare_osm_id(feature, layer):
    osm_id = feature.GetField('osm_id')
    osm_way_id = feature.GetField('osm_way_id')

    if layer == 'points':
        return 'N{}'.format(osm_id)
    elif layer == 'lines':
        return 'W{}'.format(osm_id)
    elif layer == 'multipolygons':
        if not(osm_id) and osm_way_id:
            return 'W{}'.format(osm_way_id)
        elif osm_id and not(osm_way_id):
            return 'R{}'.format(osm_id)
        else:
            LOG.error('Can\'t detect osm_id, discarding ...')
            return None
    elif layer == 'multilinestrings':
        return 'R{}'.format(osm_id)
    elif layer == 'other_relations':
        return 'R{}'.format(osm_id)
    else:
        LOG.error('Got unsupported layer %s, discarding ...')
        return None


def intersect_geom(geom, index, mapping):
    """
    Intersect geom with data
    """

    for obj in index.intersection(geom.bounds, objects=True):
        if mapping.get(obj.object).contains(geom):
            return obj.object
    else:
        # if the loop finished successfully return None
        return None


def check_bad_geom(geom, osm_id):
    """
    Check if geom is valid
    """
    try:
        # check if we can parse the geom and determine why is geometry
        # invalid
        tst_geom = shapely.wkb.loads(geom.ExportToWkb())
        if tst_geom.is_valid:
            return False
        else:
            reason = explain_validity(tst_geom)
            LOG.error(
                'Bad geometry for the feature %s, reason: %s', osm_id, reason
            )
    except:
        reason = 'BONKERS!'
        LOG.critical('BONKERS geometry for the feature %s', osm_id)

    return reason


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
        'boundary', srs, ogr.wkbPoint
    )

    # define fields
    osm_id_def = ogr.FieldDefn('osm_id', ogr.OFTString)
    osm_id_def.SetWidth(254)
    reason_def = ogr.FieldDefn('reason', ogr.OFTString)
    reason_def.SetWidth(254)
    link_def = ogr.FieldDefn('link', ogr.OFTString)
    link_def.SetWidth(254)

    layer.CreateField(osm_id_def)
    layer.CreateField(reason_def)
    layer.CreateField(link_def)

    return GEOJSON_datasource


def parseReason(reason):
    if reason.startswith('Self-intersection'):
        return [float(coord) for coord in reason[18:-1].split(' ')]
    elif reason.startswith('Ring Self-intersection'):
        return [float(coord) for coord in reason[23:-1].split(' ')]
    elif reason.startswith('Duplicate Rings'):
        return [float(coord) for coord in reason[16:-1].split(' ')]
    elif reason.startswith('BONKERS!'):
        return (0, 0)
    else:
        return (-1000, -1000)


def genProblemLink(osm_id):
    if osm_id[0] == 'N':
        return 'http://www.openstreetmap.org/node/{}'.format(osm_id[1:])
    elif osm_id[0] == 'W':
        return 'http://www.openstreetmap.org/way/{}'.format(osm_id[1:])
    elif osm_id[0] == 'R':
        return 'http://www.openstreetmap.org/relation/{}'.format(osm_id[1:])
    else:
        return 'Unknown feature type for osm_id: {}'.format(osm_id)


def writeProblem(datasource, osm_id, reason):
        layer = datasource.GetLayer(0)

        new_feat = ogr.Feature(layer.GetLayerDefn())
        new_feat.SetField('osm_id', osm_id)

        new_feat.SetField('reason', reason)

        coordinates = parseReason(reason)

        problem_link = genProblemLink(osm_id)
        if coordinates != (0, 0):
            problem_link = (
                '{link}?mlat={lat}&mlon={lon}#map=18/{lat}/{lon}'.format(
                    link=problem_link, lat=coordinates[1], lon=coordinates[0]
                )
            )
        new_feat.SetField('link', problem_link)
        # set geometry for the feature
        new_geom = ogr.Geometry(ogr.wkbPoint)
        new_geom.AddPoint(*coordinates)

        new_feat.SetGeometry(new_geom)
        # add feature to the layer
        layer.CreateFeature(new_feat)
