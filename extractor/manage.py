#!/usr/bin/python2
# -*- coding: utf-8 -*-
import logging
import logging.config

import urwid
import yaml
import psycopg2

from exposm.settings import settings

# setup logging, has to be after osmext.settings
logging.config.dictConfig(settings.get('logging'))
LOG = logging.getLogger(__file__)


class DBManagement():
    extensions = ['postgis', 'postgis_topology']

    def __init__(self, db_params):
        self.db_params = db_params

    def dropDatabase(self):
        old_db = self.db_params.get('dbname')
        self.db_params.update({'dbname': 'template1'})
        conn = psycopg2.connect(**self.db_params)

        # change the transaction isolation level
        conn.set_isolation_level(
            psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT
        )
        cur = conn.cursor()

        try:
            LOG.info('Dropping database: %s', old_db)
            cur.execute('DROP DATABASE {};'.format(old_db))
            conn.commit()
        except psycopg2.ProgrammingError, e:
            if e.pgcode == '3D000':
                # database does not exist
                LOG.error(e.pgerror)
                conn.rollback()

        cur.close()
        conn.close()
        self.db_params.update({'dbname': old_db})

    def createDatabase(self):
        new_db = self.db_params.get('dbname')
        self.db_params.update({'dbname': 'template1'})
        conn = psycopg2.connect(**self.db_params)

        # change the transaction isolation level
        conn.set_isolation_level(
            psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT
        )
        cur = conn.cursor()

        try:
            LOG.info('Creating database: %s', new_db)
            cur.execute('CREATE DATABASE {};'.format(new_db))
            conn.commit()
        except psycopg2.ProgrammingError, e:
            if e.pgcode == '42P04':
                # database already exist
                LOG.error(e.pgerror)
                conn.rollback()
            else:
                LOG.error('Unhandeld error: (%s) %s', e.pgcode, e.pgerror)
                raise e

        cur.close()
        conn.close()
        self.db_params.update({'dbname': new_db})

        self._initDB()

    def _initDB(self):
        conn = psycopg2.connect(**self.db_params)

        # change the transaction isolation level
        # conn.set_isolation_level(
        #     psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT
        # )
        cur = conn.cursor()
        for ext in self.extensions:
            try:
                LOG.debug('Creating extension: %s', ext)
                cur.execute('CREATE EXTENSION {}'.format(ext))
                conn.commit()
            except psycopg2.ProgrammingError, e:
                LOG.error('Unhandeld error: (%s) %s', e.pgcode, e.pgerror)
                raise e

        # create POSM DB functions
        with open('./postgis_sql/proc_functions.sql', 'rb') as sqlfunc:
            sqlcode = sqlfunc.read()

            try:
                LOG.debug('Creating POSM DB functions...')
                cur.execute(sqlcode)
                conn.commit()
            except psycopg2.ProgrammingError, e:
                LOG.error('Unhandeld error: (%s) %s', e.pgcode, e.pgerror)
                raise e

        cur.close()
        conn.close()


class PosmSettings():
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


if __name__ == '__main__':
    proj_settings = PosmSettings('settings.yaml')
    # proj_settings.updateDB('host', 'localhost')
    # proj_settings.writeSettings()
    db_man = DBManagement(proj_settings.db_params)
    db_man.dropDatabase()
    db_man.createDatabase()
