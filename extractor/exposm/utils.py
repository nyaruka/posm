import logging
logger = logging.getLogger(__file__)

import shapely.wkb
from shapely.validation import explain_validity


def prepare_osm_id(feature, layer):
    osm_id = feature.GetField('osm_id')
    osm_way_id = feature.GetField('osm_way_id')

    if layer == 'points':
        return 'P{}'.format(osm_id)
    elif layer == 'lines':
        return 'W{}'.format(osm_id)
    elif layer == 'multipolygons':
        if not(osm_id) and osm_way_id:
            return 'W{}'.format(osm_way_id)
        elif osm_id and not(osm_way_id):
            return 'R{}'.format(osm_id)
        else:
            logger.error('Can\'t detect osm_id, discarding ...')
            return None
    elif layer == 'multilinestrings':
        return 'R{}'.format(osm_id)
    elif layer == 'other_relations':
        return 'R{}'.format(osm_id)
    else:
        logger.error('Got unsupported layer %s, discarding ...')
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
            logger.error(
                'Bad geometry for the feature %s, reason: %s', osm_id, reason
            )
    except:
        reason = 'BONKERS!'
        logger.critical('BONKERS geometry for the feature %s', osm_id)

    return reason
