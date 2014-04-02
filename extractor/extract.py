#!/usr/bin/python2
# -*- coding: utf-8 -*-
from osgeo import gdal
import rtree

from settings import settings, admin_levels

import shapely.wkb

from writer import FeatureWriter
from reader import FeatureReader

# required for OSM data format
gdal.SetConfigOption('OGR_INTERLEAVED_READING', 'YES')
# set 'OSM_CONFIG_fILE'
gdal.SetConfigOption(
    'OSM_CONFIG_FILE', settings.get('osm_config_file')
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


def main():
    # setup index
    spat_index = rtree.index.Index()
    # extract countries
    admin_level_0 = {}

    lyr_save = FeatureWriter('/tmp/out/admin_level_0.shp')
    lyr_read = FeatureReader(settings.get('osm_data_file'))

    feature_id = 0
    for feature in lyr_read.readData():

        admin_level = feature.GetField('admin_level')
        geom = shapely.wkb.loads(feature.GetGeometryRef().ExportToWkb())
        name_en = feature.GetField('name:en')

        if admin_level == '2':
            lyr_save.saveFeature(feature)
            admin_level_0.update({feature_id: (name_en, geom)})
            spat_index.insert(feature_id, geom.envelope.bounds)
            feature_id += 1

    lyr_read.datasource.Destroy()
    lyr_save.datasource.Destroy()

    # extract states
    admin_level_1 = []

    lyr_save = FeatureWriter('/tmp/out/admin_level_1.shp')
    lyr_read = FeatureReader(settings.get('osm_data_file'))

    for feature in lyr_read.readData():

        admin_level = feature.GetField('admin_level')
        is_in = feature.GetField('is_in')
        name_en = feature.GetField('name:en') or feature.GetField('name')
        geom = shapely.wkb.loads(feature.GetGeometryRef().ExportToWkb())

        # check spatial relationship
        if geom.is_valid:
            # representative point is guaranteed within polygon
            geom_repr = geom.representative_point()
            # check index intersection
            intersection_set = list(spat_index.intersection(geom_repr.bounds))

            # do we have a hit?
            if len(intersection_set) > 0:
                for country_pk in intersection_set:
                    country = admin_level_0.get(country_pk)
                    # is the point within the country boundary
                    if geom_repr.within(country[1]):
                        is_in = country[0]
        else:
            is_in = None

        # determine admin level
        if is_in in admin_levels.get('per_country'):
            search_admin_level = (
                admin_levels.get('per_country')
                .get(is_in)
                .get('admin_level_1')
            )
        else:
            search_admin_level = (
                admin_levels.get('default').get('admin_level_1')
            )

        # check feature admin level
        if admin_level == str(search_admin_level):
            feature.SetField('is_in', is_in)
            lyr_save.saveFeature(feature)

    lyr_read.datasource.Destroy()
    lyr_save.datasource.Destroy()


if __name__ == '__main__':
    main()
