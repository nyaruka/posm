# -*- coding: utf-8 -*-
import logging
LOG = logging.getLogger(__file__)

import subprocess
import os
import sys

from .utils import proc_exec, is_file_readable


class OSMmanagement():

    def __init__(self, settings, verbose=False):
        self.settings = settings.get_settings()
        self.verbose = verbose
        self.osmFile = self.settings.get('sources').get('data_file')
        self.workDir = self.settings.get('sources').get('data_directory')
        self.dataURL = self.settings.get('sources').get('data_url')
        self.polyFile = self.settings.get('sources').get('poly_file')
        self.admin_levels_file = (
            self.settings.get('sources').get('admin_levels_file')
        )

    def downloadOSM(self):

        curDir = os.getcwd()
        os.chdir(self.workDir)

        outputfile = '{}.pbf'.format(self.osmFile)

        command = ['wget', '-nv', '-S', '-c', self.dataURL, '-O', outputfile]
        LOG.debug('Command: %s', ' '.join(command))

        proc = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            shell=False
        )

        LOG.info('Downloading OSM data file to %s', self.workDir)
        msg = proc_exec(proc, self.verbose)

        if proc.returncode != 0:
            LOG.error('OSM data file download process has not exited cleanly!')
            LOG.error(msg)
            sys.exit(99)

        if msg.find('HTTP/1.1 416 Requested Range Not Satisfiable') > 0:
            LOG.info(
                'File %s already exists in %s', outputfile, self.workDir
            )
        elif msg.find('HTTP/1.1 200 OK'):
            LOG.info(
                'OSM data file downloaded successfully to %s', self.workDir
            )
        else:
            LOG.error('Unknown response message', msg)
            sys.exit(99)

        # revert to the old directory
        os.chdir(curDir)

    def convertOSMtoO5M(self):
        curDir = os.getcwd()
        os.chdir(self.workDir)

        datafile = '{}.o5m'.format(self.osmFile)
        command = [
            './osmconvert', '-v', '{}.pbf'.format(self.osmFile),
            '-o={}'.format(datafile)
        ]
        LOG.debug('Command: %s', ' '.join(command))
        proc = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            shell=False
        )
        # execute the process ... .wait()
        LOG.info('Converting OSM data file to %s', datafile)
        msg = proc_exec(proc, self.verbose)

        if proc.returncode != 0:
            LOG.error('OSM PBF to O5M file conversion has not exited cleanly!')
            LOG.error(msg)
            sys.exit(99)

        os.chdir(curDir)

    def updateOSM(self):
        curDir = os.getcwd()
        if self.polyFile:
            polyfile_path = os.path.abspath(self.polyFile)

            if not(is_file_readable(polyfile_path)):
                LOG.error('File "%s" is not readable', polyfile_path)
                sys.exit(99)

        os.chdir(self.workDir)
        datafile = '{}.o5m'.format(self.osmFile)

        if self.polyFile:
            command = [
                './osmupdate', '-v', datafile, 'new.{}'.format(datafile),
                '-B={}'.format(polyfile_path)
            ]
            LOG.debug('Command: %s', ' '.join(command))

            proc = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                shell=False
            )
            LOG.info(
                'Updating OSM data file %s ... with polyfile %s',
                datafile, polyfile_path
            )
        else:
            command = [
                './osmupdate', '-v', datafile, 'new.{}'.format(datafile)
            ]
            LOG.debug('Command: %s', ' '.join(command))

            proc = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                shell=False
            )
            LOG.info('Updating OSM data file %s ...', datafile)

        msg = proc_exec(proc, self.verbose)

        if proc.returncode != 0:
            LOG.error('OSM update has not exited cleanly!')
            LOG.error(msg)
            sys.exit(99)

        # rename updated file
        os.rename('new.{}'.format(datafile), datafile)
        os.chdir(curDir)

    def extractAdminLevels(self):
        curDir = os.getcwd()
        os.chdir(self.workDir)
        datafile = '{}.o5m'.format(self.osmFile)

        command = [
            './osmfilter', '-v', datafile, '--keep=admin_level',
            '-o={}.o5m'.format(self.admin_levels_file)
        ]
        LOG.debug('Command: %s', ' '.join(command))

        proc = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            shell=False
        )
        LOG.info('Extracting "admin_levels" from OSM file %s ...', datafile)

        # execute the process ... .wait()
        msg = proc_exec(proc, self.verbose)

        if proc.returncode != 0:
            LOG.error('OSM filter has not exited cleanly!')
            LOG.error(msg)
            sys.exit(99)

        os.chdir(curDir)

    def convertO5MtoPBF(self):
        curDir = os.getcwd()
        os.chdir(self.workDir)
        datafile = '{}.o5m'.format(self.admin_levels_file)
        new_datafile = '{}.pbf'.format(self.admin_levels_file)

        command = [
            './osmconvert', '-v', datafile, '-o={}'.format(new_datafile)
        ]
        LOG.debug('Command: %s', ' '.join(command))

        proc = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            shell=False
        )
        LOG.info('Converting %s to %s ...', datafile, new_datafile)

        # execute the process ... .wait()
        msg = proc_exec(proc, self.verbose)

        if proc.returncode != 0:
            LOG.error('OSM convert has not exited cleanly!')
            LOG.error(msg)
            sys.exit(99)

        os.chdir(curDir)
