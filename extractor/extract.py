#!/usr/bin/python2
# -*- coding: utf-8 -*-
import logging
import logging.config

from osgeo import gdal
import rtree
import shapely.wkb
from shapely.validation import explain_validity

from settings import settings, admin_levels

# setup logging
logging.config.dictConfig(settings.get('logging'))
logger = logging.getLogger(__file__)


from writer import FeatureWriter
from reader import FeatureReader


# required for OSM data format
gdal.SetConfigOption('OGR_INTERLEAVED_READING', 'YES')
# set 'OSM_CONFIG_fILE'
gdal.SetConfigOption(
    'OSM_CONFIG_FILE', settings.get('sources').get('osm_config_file')
)
# this option is required when parsing large datasets, at least in my
# environment, I got lots of "Cannot read node ..." error messages
# http://svn.osgeo.org/gdal/trunk/gdal/ogr/ogrsf_frmts/osm/ogrosmdatasource.cpp
gdal.SetConfigOption('OSM_USE_CUSTOM_INDEXING', 'NO')

# large datasets require a lot of disk space, set temporary directory with
# enough free space
gdal.SetConfigOption('CPL_TMPDIR', '/tmp')

# setup logging options
gdal.SetConfigOption('CPL_TIMESTAMP', 'ON')
gdal.SetConfigOption('CPL_DEBUG', 'ON')
gdal.SetConfigOption('CPL_LOG', '/tmp/gdal_log.log')
gdal.PushErrorHandler('CPLLoggingErrorHandler')
gdal.SetConfigOption("CPL_LOG_ERRORS", 'ON')


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


def main():
    # setup index
    spat_index_0 = rtree.index.Index()
    # extract countries
    admin_level_0 = {}

    lyr_save = FeatureWriter('/tmp/out/admin_level_0.shp')
    lyr_read = FeatureReader(settings.get('sources').get('osm_data_file'))

    feature_id = 0

    logger.info('Started exporting admin_level_0 boundaries!')

    for feature in lyr_read.readData():

        # get data
        osm_id = feature.GetField('osm_id')
        admin_level = feature.GetField('admin_level')
        geom = shapely.wkb.loads(feature.GetGeometryRef().ExportToWkb())
        name = feature.GetField('name')

        # osm_id is crucial for establishing feature relationship
        if not(osm_id_exists(osm_id)):
            logger.warning('Feature without OSM_ID, discarding... "%s"', name)
            continue

        # process national level boundary
        if admin_level == '2':
            # set custom attribute
            feature.SetField('is_in', None)
            # save the feature
            lyr_save.saveFeature(feature)
            admin_level_0.update({feature_id: (osm_id, geom)})

            spat_index_0.insert(feature_id, geom.envelope.bounds)
            logger.debug('Index %s, record %s', feature_id, osm_id)

            feature_id += 1

    lyr_read.datasource.Destroy()
    lyr_save.datasource.Destroy()

    # extract states
    admin_level_1 = {}
    # create index
    spat_index_1 = rtree.index.Index()

    feature_id = 0

    lyr_save = FeatureWriter('/tmp/out/admin_level_1.shp')
    lyr_read = FeatureReader(settings.get('sources').get('osm_data_file'))

    for feature in lyr_read.readData():

        osm_id = feature.GetField('osm_id')
        admin_level = feature.GetField('admin_level')
        name = feature.GetField('name')
        geom = shapely.wkb.loads(feature.GetGeometryRef().ExportToWkb())

        # osm_id is crucial for establishing feature relationship
        if not(osm_id_exists(osm_id)):
            logger.warning('Feature without OSM_ID, discarding... "%s"', name)
            continue

        # check spatial relationship
        if geom.is_valid:
            # representative point is guaranteed within polygon
            geom_repr = geom.representative_point()
            # check index intersection

            is_in = intersect_geom(
                geom_repr, spat_index_0, admin_level_0, osm_id
            )

        else:
            # geometry is not valid
            logger.warning('%s not valid: %s', osm_id, explain_validity(geom))
            is_in = None
            continue

        # check for specific admin level mapping
        if is_in in admin_levels.get('per_country'):
            search_admin_level = (
                admin_levels.get('per_country')
                .get(is_in)
                .get('admin_level_1')
            )
            logger.info(
                'Using custom admin_level for %s (%s)',
                admin_levels.get('per_country')
                .get(is_in).get('meta').get('name'), is_in
            )
        else:
            search_admin_level = (
                admin_levels.get('default').get('admin_level_1')
            )

        # check current feature admin level
        if admin_level == str(search_admin_level):
            # update internal relationship
            feature.SetField('is_in', is_in)
            lyr_save.saveFeature(feature)

            admin_level_1.update({feature_id: (osm_id, geom)})

            spat_index_1.insert(feature_id, geom.envelope.bounds)
            logger.debug('Index %s, record %s', feature_id, osm_id)

            feature_id += 1

    lyr_read.datasource.Destroy()
    lyr_save.datasource.Destroy()

    # extract counties

    lyr_save = FeatureWriter('/tmp/out/admin_level_2.shp')
    lyr_read = FeatureReader(settings.get('sources').get('osm_data_file'))

    for feature in lyr_read.readData():

        osm_id = feature.GetField('osm_id')
        admin_level = feature.GetField('admin_level')
        name = feature.GetField('name')
        geom = shapely.wkb.loads(feature.GetGeometryRef().ExportToWkb())

        # osm_id is crucial for establishing feature relationship
        if not(osm_id_exists(osm_id)):
            logger.warning('Feature without OSM_ID, discarding... "%s"', name)
            continue

        # check spatial relationship
        if geom.is_valid:
            # representative point is guaranteed within polygon
            geom_repr = geom.representative_point()
            # check index intersection
            is_in = intersect_geom(
                geom_repr, spat_index_0, admin_level_0, osm_id
            )

            is_in_state = intersect_geom(
                geom_repr, spat_index_1, admin_level_1, osm_id
            )

        else:
            # geometry is not valid
            logger.warning('%s not valid: %s', osm_id, explain_validity(geom))
            is_in = None
            continue

        # check for specific admin level mapping
        if is_in in admin_levels.get('per_country'):
            search_admin_level = (
                admin_levels.get('per_country')
                .get(is_in)
                .get('admin_level_2')
            )
            logger.info(
                'Using custom admin_level for %s (%s)',
                admin_levels.get('per_country')
                .get(is_in).get('meta').get('name'), is_in
            )
        else:
            search_admin_level = (
                admin_levels.get('default').get('admin_level_2')
            )

        # check current feature admin level
        if admin_level == str(search_admin_level):
            # update internal relationship
            feature.SetField('is_in', is_in_state)
            lyr_save.saveFeature(feature)

    lyr_read.datasource.Destroy()
    lyr_save.datasource.Destroy()


if __name__ == '__main__':
    main()
