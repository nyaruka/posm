# -*- coding: utf-8 -*-
import logging
LOG = logging.getLogger(__file__)

import subprocess
import psycopg2
# from multiprocessing.dummy import Pool


class ProcessManagement():

    def __init__(self, settings):
        self.settings = settings.settings
        self.db_params = settings.db_params

    def processAdminLevels(self):
        command = [
            'python', 'extract.py'
        ]
        LOG.debug('Command: %s', ' '.join(command))

        proc = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            shell=False
        )
        # execute the process ... .wait()
        LOG.info(
            'Processing admin levels %s',
            self.settings.get('sources').get('osm_data_file')
        )
        msg = ''.join(proc.communicate())

        if proc.returncode != 0:
            LOG.error('Admin level processing has not exited cleanly!')
            LOG.error(msg)

    def deconstructGeometry(self):
        conn = psycopg2.connect(**self.db_params)

        cur = conn.cursor()
        try:
            cur.execute("set search_path = \"$user\", 'public', 'topology';")
            LOG.info('Deconstructing geometry...')
            cur.execute('select deconstruct_geometry();')
            conn.commit()

        except psycopg2.ProgrammingError, e:
            LOG.error('Unhandeld error: (%s) %s', e.pgcode, e.pgerror)
            raise e

        cur.close()
        conn.close()

    def createBaseTopology(self):
        conn = psycopg2.connect(**self.db_params)

        cur = conn.cursor()
        try:
            cur.execute("set search_path = \"$user\", 'public', 'topology';")
            LOG.info('Initializing topology...')
            cur.execute('select init_base_topology();')
            LOG.info('Creating topology...')
            cur.execute('select create_base_topology();')
            conn.commit()

        except psycopg2.ProgrammingError, e:
            LOG.error('Unhandeld error: (%s) %s', e.pgcode, e.pgerror)
            raise e

        cur.close()
        conn.close()

    def simplifyAdminLevels(self, tolerance=0.001):
        conn = psycopg2.connect(**self.db_params)

        cur = conn.cursor()
        try:
            cur.execute("set search_path = \"$user\", 'public', 'topology';")
            LOG.info('Simplifying admin_levels ...')
            cur.execute('select simplify_dissolve(%s);', (tolerance,))
            conn.commit()

        except psycopg2.ProgrammingError, e:
            LOG.error('Unhandeld error: (%s) %s', e.pgcode, e.pgerror)
            raise e

        cur.close()
        conn.close()

    def convertToGeoJson(self, *args):
        if len(args) > 0:
            command = ['python', 'generate_geojson.py', '--rm']
            command += [arg for arg in args]
        else:
            command = [
                'python', 'generate_geojson.py', '--rm', '--all'
            ]

        LOG.debug('Command: %s', ' '.join(command))
        proc = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            shell=False
        )
        # execute the process ... .wait()
        LOG.info('Converting to geojson ... exported_geojson.zip')
        msg = ''.join(proc.communicate())

        if proc.returncode != 0:
            LOG.error('Converting to geojson has not exited cleanly!')
            LOG.error(msg)

    # def createBaseTopologyParallel(self):
    #     conn = psycopg2.connect(**self.db_params)

    #     conn.set_isolation_level(
    #         psycopg2.extensions.ISOLATION_LEVEL_SERIALIZABLE
    #     )
    #     tpool = Pool(8)

    #     def process_osm_id(osm_id):
    #         conn = psycopg2.connect(**self.db_params)
    #         cur = conn.cursor()
    #         try:
    #             LOG.info('Started creating topology for ... %s', osm_id[0])
    #             cur.execute(
    #                 "set search_path = \"$user\", 'public', 'topology';"
    #             )
    #             cur.execute('select create_base_topology_for_id(%s);', osm_id)
    #             LOG.info('Created topology for ... %s', osm_id[0])

    #         except psycopg2.ProgrammingError, e:
    #             LOG.error('Unhandeld error: (%s) %s', e.pgcode, e.pgerror)
    #             raise e
    #         conn.commit()
    #         cur.close()
    #         conn.close()

    #     cur = conn.cursor()
    #     try:
    #         cur.execute("set search_path = \"$user\", 'public', 'topology';")
    #         LOG.info('Initializing topology...')
    #         cur.execute('select init_base_topology();')
    #     except psycopg2.ProgrammingError, e:
    #         LOG.error('Unhandeld error: (%s) %s', e.pgcode, e.pgerror)
    #         raise e
    #     conn.commit()
    #     cur.execute('SELECT osm_id FROM all_geom order by osm_id asc')

    #     osm_ids = cur.fetchall()

    #     tpool.map(process_osm_id, osm_ids)
    #     tpool.close()
    #     tpool.join()

    #     conn.close()
