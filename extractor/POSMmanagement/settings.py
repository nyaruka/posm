import logging
LOG = logging.getLogger(__file__)

import sys
import yaml
import gdal

from .utils import is_file_readable


class POSMSettings():
    settings = {}
    admin_levels = {}

    def __init__(self, settingsFile, verbose=False):
        self.settingsFile = settingsFile
        self._readSettings()
        self.verbose = verbose

    def _readSettings(self):
        LOG.debug('Reading settings from %s', self.settingsFile)
        if not(is_file_readable(self.settingsFile)):
            LOG.error('File "%s" is not readable', self.settingsFile)
            sys.exit(99)

        with open(self.settingsFile, 'r') as tmpfile:
            self.settings.update(yaml.load(tmpfile))
        self._decodeDBConnection()
        self._readAdminLevels()
        self._setupGDAL()

    def get_settings(self):
        return self.settings

    def get_admin_levels(self):
        return self.admin_levels

    def _readAdminLevels(self):
        admin_levels_file = open('admin_mapping.yaml', 'rb')
        self.admin_levels.update(yaml.load(admin_levels_file))

    def _setupGDAL(self):
        # required for OSM data format
        gdal.SetConfigOption('OGR_INTERLEAVED_READING', 'YES')
        # set 'OSM_CONFIG_fILE'
        gdal.SetConfigOption(
            'OSM_CONFIG_FILE',
            self.settings.get('sources').get('osm_config_file')
        )

        # large datasets require a lot of disk space, set temporary directory
        # with enough free space
        gdal.SetConfigOption(
            'CPL_TMPDIR', self.settings.get('gdal').get('tempfile_dir')
        )

        # fine tune memory allocation for tmp data, 4Gb should be enough for
        # current admin_level extract
        gdal.SetConfigOption(
            'OSM_MAX_TMPFILE_SIZE',
            self.settings.get('gdal').get('memory_limit')
        )

        # setup logging options
        gdal.SetConfigOption('CPL_TIMESTAMP', 'ON')
        gdal.PushErrorHandler('CPLLoggingErrorHandler')
        gdal.SetConfigOption("CPL_LOG_ERRORS", 'ON')
        gdal.SetConfigOption(
            'CPL_DEBUG', self.settings.get('gdal').get('debug')
        )
        gdal.SetConfigOption(
            'CPL_LOG', self.settings.get('gdal').get('debug_file')
        )

        # postgresql driver specific settings

        gdal.SetConfigOption('PG_USE_COPY', 'YES')

    def _decodeDBConnection(self):
        db_conn = self.settings.get('exposm').get('postgis')
        self.db_params = {key: val.strip('\'') for key, val in (
            sett.split('=') for sett in db_conn.split(':')[1].split(' '))
        }
        LOG.debug('DBparams: %s', self.db_params)

    def _encodeDBConnection(self):
        db_conn = ' '.join(
            ('='.join(param) for param in self.db_params.items())
        )
        return 'PG:{}'.format(db_conn)

    def updateDB(self, key, value):
        self.db_params.update([(key, '\'{}\''.format(value))])

    def writeSettings(self):
        # update db settings
        self.settings['exposm']['postgis'] = self._encodeDBConnection()

        # write settings to yaml
        LOG.debug('Writing settings to %s', self.settingsFile)
        with file(self.settingsFile, 'w') as tmpfile:
            yaml.dump(self.settings, tmpfile, indent=4)
