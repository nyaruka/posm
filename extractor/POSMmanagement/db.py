import logging
LOG = logging.getLogger(__file__)

import psycopg2


class DBManagement():
    extensions = ['postgis', 'postgis_topology']

    def __init__(self, settings, verbose=False):
        self.settings = settings.get_settings()
        self.db_params = settings.db_params

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
        except psycopg2.ProgrammingError as e:
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
        except psycopg2.ProgrammingError as e:
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
            except psycopg2.ProgrammingError as e:
                LOG.error('Unhandeld error: (%s) %s', e.pgcode, e.pgerror)
                raise e

        # create POSM DB functions
        with open('./postgis_sql/proc_functions.sql', 'rb') as sqlfunc:
            sqlcode = sqlfunc.read()

            try:
                LOG.debug('Creating POSM DB functions...')
                cur.execute(sqlcode)
                conn.commit()
            except psycopg2.ProgrammingError as e:
                LOG.error('Unhandeld error: (%s) %s', e.pgcode, e.pgerror)
                raise e

        cur.close()
        conn.close()
