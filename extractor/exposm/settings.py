import yaml
from osgeo import gdal

settings = {}
admin_levels = {}

# source file definitions
settings_file = open('settings.yaml', 'rb')
admin_levels_file = open('admin_mapping.yaml', 'rb')

# update settings dictionary
settings.update(yaml.load(settings_file))
admin_levels.update(yaml.load(admin_levels_file))

# required for OSM data format
gdal.SetConfigOption('OGR_INTERLEAVED_READING', 'YES')
# set 'OSM_CONFIG_fILE'
gdal.SetConfigOption(
    'OSM_CONFIG_FILE', settings.get('sources').get('osm_config_file')
)
# this option is required when parsing large datasets, at least in my
# environment, I got lots of "Cannot read node ..." error messages
# http://svn.osgeo.org/gdal/trunk/gdal/ogr/ogrsf_frmts/osm/ogrosmdatasource.cpp
# gdal.SetConfigOption('OSM_USE_CUSTOM_INDEXING', 'NO')

# large datasets require a lot of disk space, set temporary directory with
# enough free space
gdal.SetConfigOption('CPL_TMPDIR', settings.get('gdal').get('tempfile_dir'))

# fine tune memory allocation for tmp data, 4Gb should be enough for current
# admin_level extract
gdal.SetConfigOption(
    'OSM_MAX_TMPFILE_SIZE', settings.get('gdal').get('memory_limit')
)

# setup logging options
gdal.SetConfigOption('CPL_TIMESTAMP', 'ON')
gdal.PushErrorHandler('CPLLoggingErrorHandler')
gdal.SetConfigOption("CPL_LOG_ERRORS", 'ON')
gdal.SetConfigOption('CPL_DEBUG', settings.get('gdal').get('debug'))
gdal.SetConfigOption('CPL_LOG', settings.get('gdal').get('debug_file'))
