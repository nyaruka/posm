import logging
LOG = logging.getLogger(__file__)

import yaml


class POSMSettings():
    settings = {}

    def __init__(self, settingsFile):
        self.settingsFile = settingsFile
        self._readSettings()

    def _readSettings(self):
        LOG.debug('Reading settings from %s', self.settingsFile)
        with open(self.settingsFile, 'r') as tmpfile:
            self.settings.update(yaml.load(tmpfile))
        self._decodeDBConnection()

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
