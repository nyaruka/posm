import logging
logger = logging.getLogger(__file__)

import shapely.wkb
from shapely.validation import explain_validity


def osm_id_exists(osm_id):
    """
    Check if osm_id exists
    """
    if osm_id:
        return True
    else:
        return False


def intersect_geom(geom, index, mapping, osm_id):
    """
    Intersect geom with data
    """
    intersection_set = list(index.intersection(geom.bounds))

    # do we have a hit?
    if len(intersection_set) > 0:
        logger.debug(
            'Found %s intersections for %s', len(intersection_set),
            osm_id
        )
        for country_pk in intersection_set:
            country = mapping.get(country_pk)
            # is the point within the country boundary
            if geom.within(country[1]):
                return country[0]

    else:
        logger.debug('No intersections for %s', osm_id)
        return None


def check_geom(geom, osm_id):
    """
    Check if geom is valid
    """
    if geom.IsValid():
        return True
    else:
        logger.error('Bad geometry for feature %s', osm_id)
        try:
            # check if we can parse the geom and determine why is geometry
            # invalid
            tst_geom = shapely.wkb.loads(
                geom.ExportToWkb()
            )
            logger.error('Validity reason: %s', explain_validity(tst_geom))
        except:
            logger.error('Validity reason: BONKERS!')

        return None
