import logging
logger = logging.getLogger(__file__)

import shapely.wkb
from shapely.validation import explain_validity


def osm_id_exists(osm_id, name):
    """
    Check if osm_id exists
    """
    if osm_id:
        return True
    else:
        logger.warning('Feature without OSM_ID, discarding... "%s"', name)
        return False


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
