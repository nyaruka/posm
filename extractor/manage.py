#!/usr/bin/python2
# -*- coding: utf-8 -*-
import logging
import logging.config

import urwid
import yaml

from exposm.settings import settings

# setup logging, has to be after osmext.settings
logging.config.dictConfig(settings.get('logging'))
LOG = logging.getLogger(__file__)


class PosmSettings():
    settings = {}

    def __init__(self, settingsFile):
        self.settingsFile = settingsFile
        self.readSettings()

    def readSettings(self):
        LOG.debug('Reading settings from %s', self.settingsFile)
        with open(self.settingsFile, 'r') as tmpfile:
            self.settings.update(yaml.load(tmpfile))
        self.decodeDBConnection()

    def decodeDBConnection(self):
        db_conn = self.settings.get('exposm').get('postgis')
        self.db_params = dict(
            (sett.split('=') for sett in db_conn.split(':')[1].split(' '))
        )

    def encodeDBConnection(self):
        db_conn = ' '.join(
            ('='.join(param) for param in self.db_params.items())
        )
        return 'PG:{}'.format(db_conn)

    def updateDB(self, key, value):
        self.db_params.update([(key, '\'{}\''.format(value))])

    def writeSettings(self):
        # update db settings
        self.settings['exposm']['postgis'] = self.encodeDBConnection()

        # write settings to yaml
        LOG.debug('Writing settings to %s', self.settingsFile)
        with file(self.settingsFile, 'w') as tmpfile:
            yaml.dump(self.settings, tmpfile, indent=4)


if __name__ == '__main__':
    proj_settings = PosmSettings('settings.yaml')
    proj_settings.updateDB('host', 'localhost')
    proj_settings.writeSettings()
