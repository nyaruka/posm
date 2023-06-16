# -*- coding: utf-8 -*-
import logging
LOG = logging.getLogger(__file__)

import subprocess
import psycopg2
import sys
import os

from .utils import proc_exec


class ProcessManagement():

    def __init__(self, settings, verbose=False):
        self.verbose = verbose
        self.settings = settings.get_settings()
        self.db_params = settings.db_params

    def processAdminLevels(self, settings_file):
        command = [
            'python', 'extract.py', '--settings', settings_file,
            '--problems_as_geojson'
        ]
        LOG.debug('Command: %s', ' '.join(command))

        # execute the process ... .wait()
        admin_level_data_path = os.path.join(
            self.settings.get('sources').get('data_directory'),
            '{}.pbf'.format(
                self.settings.get('sources').get('admin_levels_file')
            )
        )

        LOG.info(
            'Processing admin levels %s', admin_level_data_path
        )
        exit_code, msg = proc_exec(command, self.verbose)

        # if exit_code != 0:
        #     LOG.error('Admin level processing has not exited cleanly!')
        #     LOG.error(msg)
        #     sys.exit(99)

    def processAdminLevelsGADM(self, settings_file):
        command = [
            'python', 'extract_gadm.py', '--settings', settings_file,
            '--problems_as_geojson'
        ]
        LOG.debug('Command: %s', ' '.join(command))

        exit_code, msg = proc_exec(command, self.verbose)

        if exit_code != 0:
            LOG.error('Admin level processing has not exited cleanly!')
            LOG.error(msg)
            sys.exit(99)

    def processAdminLevelsGEOJSON(self, settings_file):
        command = [
            'python', 'extract_geojson.py', '--settings', settings_file,
            '--problems_as_geojson'
        ]
        LOG.debug('Command: %s', ' '.join(command))

        exit_code, msg = proc_exec(command, self.verbose)
        if exit_code != 0:
            LOG.error('Admin level processing has not exited cleanly!')
            LOG.error(msg)
            sys.exit(99)

    def processAdminLevelsOverpass(self, settings_file, relation_id):
        command = [
            'python', 'extract_overpass.py', '--settings', settings_file,
            '--problems_as_geojson', relation_id,
        ]
        LOG.debug('Command: %s', ' '.join(command))

        exit_code, msg = proc_exec(command, self.verbose)
        if exit_code != 0:
            LOG.error('Admin level processing has not exited cleanly!')
            LOG.error(msg)
            sys.exit(99)

    def snapToGrid(self, grid_size=0.00005):
        conn = psycopg2.connect(**self.db_params)
        cur = conn.cursor()
        try:
            cur.execute("set search_path = \"$user\", 'public', 'topology';")
            print('Snapping to grid ...')
            cur.execute('update admin_level_0 set wkb_geometry = st_snaptogrid(wkb_geometry, %s)', (grid_size,))
            cur.execute('update admin_level_1 set wkb_geometry = st_snaptogrid(wkb_geometry, %s)', (grid_size,))
            cur.execute('update admin_level_2 set wkb_geometry = st_snaptogrid(wkb_geometry, %s)', (grid_size,))
            cur.execute('update admin_level_3 set wkb_geometry = st_snaptogrid(wkb_geometry, %s)', (grid_size,))
            conn.commit()

        except psycopg2.ProgrammingError as e:
            print('Unhandeld error: (%s) %s', e.pgcode, e.pgerror)
            raise e

        cur.close()
        conn.close()

    def deconstructGeometry(self):
        conn = psycopg2.connect(**self.db_params)

        cur = conn.cursor()
        try:
            cur.execute("set search_path = \"$user\", 'public', 'topology';")
            LOG.info('Deconstructing geometry...')
            cur.execute('select deconstruct_geometry();')
            conn.commit()

        except psycopg2.ProgrammingError as e:
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

        except psycopg2.ProgrammingError as e:
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
        except psycopg2.ProgrammingError as e:
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

        except psycopg2.ProgrammingError as e:
            LOG.error('Unhandeld error: (%s) %s', e.pgcode, e.pgerror)
            raise e

        cur.close()
        conn.close()

    def convertToGeoJson(self, settings_file, *args):
        if len(args) > 0:
            command = [
                'python', 'generate_geojson.py', '--rm', '--settings',
                settings_file
            ]
            command += [arg for arg in args]
        else:
            command = [
                'python', 'generate_geojson.py', '--rm', '--all', '--settings',
                settings_file
            ]

        LOG.debug('Command: %s', ' '.join(command))
        # execute the process ... .wait()
        LOG.info('Converting to geojson ... exported_geojson.zip')
        exit_code, msg = proc_exec(command, self.verbose)

        if exit_code != 0:
            LOG.error('Converting to geojson has not exited cleanly!')
            LOG.error(msg)
            sys.exit(99)
