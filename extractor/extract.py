#!/usr/bin/python2
# -*- coding: utf-8 -*-
from osgeo import gdal

from settings import settings

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
    lyr_save = FeatureWriter('/tmp/out/world.shp')

    lyr_read = FeatureReader(
        settings.get('osm_data_file'), 'admin_level = \'4\''
    )

    for feature in lyr_read.readData():
        lyr_save.saveFeature(feature)

    lyr_read.datasource.Destroy()
    lyr_save.datasource.Destroy()


if __name__ == '__main__':
    main()
