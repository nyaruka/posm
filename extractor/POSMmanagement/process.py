# -*- coding: utf-8 -*-
import logging
LOG = logging.getLogger(__file__)

import subprocess
import psycopg2
import sys

from .utils import proc_exec


class ProcessManagement():

    def __init__(self, settings, verbose=False):
        self.verbose = verbose
        self.settings = settings.get_settings()
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
        msg = proc_exec(proc, self.verbose)

        if proc.returncode != 0:
            LOG.error('Admin level processing has not exited cleanly!')
            LOG.error(msg)
            sys.exit(99)

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

        except psycopg2.ProgrammingError, e:
            LOG.error('Unhandeld error: (%s) %s', e.pgcode, e.pgerror)
            raise e

        cur.execute('SELECT osm_id FROM all_geom order by osm_id asc')
        osm_ids = cur.fetchall()
        cur.execute('SELECT count(osm_id) FROM all_geom')
        total = cur.fetchone()[0]
        try:
            for idx, osm_id in enumerate(osm_ids):
                LOG.debug(
                    'Creating topology for %s ... (%s/%s)',
                    osm_id[0], idx+1, total
                )
                cur.execute(
                    "set search_path = \"$user\", 'public', 'topology';"
                )
                cur.execute('select create_base_topology_for_id(%s);', osm_id)
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
        msg = proc_exec(proc, self.verbose)

        if proc.returncode != 0:
            LOG.error('Converting to geojson has not exited cleanly!')
            LOG.error(msg)
            sys.exit(99)
