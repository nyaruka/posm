# -*- coding: utf-8 -*-
import logging
LOG = logging.getLogger(__file__)

import subprocess
import os
import errno
import sys

from .utils import proc_exec, is_directory_writable, is_file_readable


class ProjectManagement():

    def __init__(self, settings, verbose=False):
        self.verbose = verbose
        self.settings = settings.get_settings()
        self.workDir = self.settings.get('sources').get('data_directory')
        self.osmFile = self.settings.get('sources').get('data_file')
        self.polyFile = self.settings.get('sources').get('poly_file')

    def cutExtract(self, planet_osm):
        curDir = os.getcwd()

        osm_originPath = os.path.normpath(os.path.abspath(planet_osm))
        if not(is_file_readable(osm_originPath)):
            LOG.error('File "%s" is not readable', osm_originPath)
            sys.exit(99)

        if self.polyFile:
            polyfile_path = os.path.abspath(self.polyFile)

            if not(is_file_readable(polyfile_path)):
                LOG.error('File "%s" is not readable', polyfile_path)
                sys.exit(99)

        os.chdir(self.workDir)

        osm_file_path = os.path.normpath(
            os.path.join(self.workDir, '{}.o5m'.format(self.osmFile))
        )
        print(osm_file_path, osm_originPath)
        if (os.path.exists(osm_file_path) and
                os.path.samefile(osm_file_path, osm_originPath)):
            LOG.error((
                'Planet.osm file and destination file can\'t be the same file:'
                ' %s = %s'
            ), osm_originPath, osm_file_path)
            sys.exit(99)

        command = [
            './osmconvert', '-v', osm_originPath,
            '-B={}'.format(polyfile_path), '-o={}'.format(osm_file_path)
        ]
        LOG.debug('Command: %s', ' '.join(command))

        proc = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            shell=False
        )

        # execute the process ... .wait()
        LOG.info(
            'Cutting %s from %s using %s...', self.osmFile, osm_originPath,
            polyfile_path
        )
        msg = proc_exec(proc, self.verbose)

        if proc.returncode != 0:
            LOG.error('Extract cutting has not exited cleanly!')
            LOG.error(msg)
            sys.exit(99)
        os.chdir(curDir)

    def initDirectory(self):
        curDir = os.getcwd()

        if not(is_directory_writable(self.workDir)):
            LOG.info('Creating directory %s', self.workDir)
            try:
                os.makedirs(self.workDir)
            except OSError as exc:
                if exc.errno == errno.EEXIST and os.path.isdir(self.workDir):
                    # directory already exists...
                    pass
                else:
                    LOG.error(str(exc))
                    sys.exit(99)

        os.chdir(self.workDir)

        self._compile_osmconvert()
        self._compile_osmupdate()
        self._compile_osmfilter()

        os.chdir(curDir)

    def _compile_osmconvert(self):
        command1 = ['wget', '-O', '-', 'http://m.m.i24.cc/osmconvert.c']
        command2 = ['cc', '-x', 'c', '-', '-lz', '-O3', '-o', 'osmconvert']
        LOG.debug('Command: %s', ' '.join(command1))
        LOG.debug('Command: %s', ' '.join(command2))

        proc1 = subprocess.Popen(
            command1, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            shell=False
        )
        proc2 = subprocess.Popen(
            command2, stdin=proc1.stdout, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        proc1.stdout.close()
        # execute the process ... .wait()
        LOG.info('Downloading and compiling osmconvert...')
        msg = proc_exec(proc2, self.verbose)

        if proc2.returncode != 0:
            LOG.error('Osmconvert not compiled!')
            LOG.error(msg)
            sys.exit(99)

    def _compile_osmfilter(self):
        command1 = ['wget', '-O', '-', 'http://m.m.i24.cc/osmfilter.c']
        command2 = ['cc', '-x', 'c', '-', '-O3', '-o', 'osmfilter']
        LOG.debug('Command: %s', ' '.join(command1))
        LOG.debug('Command: %s', ' '.join(command2))

        proc1 = subprocess.Popen(
            command1, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            shell=False
        )
        proc2 = subprocess.Popen(
            command2, stdin=proc1.stdout, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        proc1.stdout.close()
        # execute the process ... .wait()
        LOG.info('Downloading and compiling osmfilter...')
        msg = proc_exec(proc2, self.verbose)

        if proc2.returncode != 0:
            LOG.error('Osmfilter not compiled!')
            LOG.error(msg)
            sys.exit(99)

    def _compile_osmupdate(self):
        command1 = ['wget', '-O', '-', 'http://m.m.i24.cc/osmupdate.c']
        command2 = ['cc', '-x', 'c', '-', '-O3', '-o', 'osmupdate']
        LOG.debug('Command: %s', ' '.join(command1))
        LOG.debug('Command: %s', ' '.join(command2))

        proc1 = subprocess.Popen(
            command1, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            shell=False
        )
        proc2 = subprocess.Popen(
            command2, stdin=proc1.stdout, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        proc1.stdout.close()
        # execute the process ... .wait()
        LOG.info('Downloading and compiling osmupdate...')
        msg = proc_exec(proc2, self.verbose)

        if proc2.returncode != 0:
            LOG.error('Osmupdate not compiled!')
            LOG.error(msg)
            sys.exit(99)
