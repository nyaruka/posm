# -*- coding: utf-8 -*-
import logging
LOG = logging.getLogger(__file__)

import subprocess
import os


class OSMmanagement():

    def __init__(self):
        self._readUpdateconfig()
        self.osmFile = self.config.get('PLANET_OSM')
        self.workDir = self.config.get('WORKING_DIRECTORY')

    def _readUpdateconfig(self):
        # read auto update settigns
        with open('auto_update_osm.conf', 'r') as conf:
            self.config = {
                key: val.strip('"') for key, val in (
                    line.split('=') for line in conf.read().split('\n')
                    if line != ''
                )
            }

    def downloadOSM(self):

        curDir = os.getcwd()
        os.chdir(self.workDir)

        outputfile = '{}.pbf'.format(self.osmFile)

        command = [
            'wget', '-nv', '-S', '-c', self.config.get('DATA_URL'), '-O',
            outputfile
        ]
        LOG.debug('Command: %s', ' '.join(command))

        proc = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            shell=False
        )
        # execute the process ... .wait()
        LOG.info('Downloading OSM data file to %s', self.workDir)
        msg = ''.join(proc.communicate())

        if proc.returncode != 0:
            LOG.error('OSM data file download process has not exited cleanly!')
            LOG.error(msg)

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
        msg = ''.join(proc.communicate())

        if proc.returncode != 0:
            LOG.error('OSM PBF to O5M file conversion has not exited cleanly!')
            LOG.error(msg)

        os.chdir(curDir)

    def updateOSM(self, polyfile=None):
        curDir = os.getcwd()
        polyfile_path = os.path.abspath(polyfile)

        os.chdir(self.workDir)
        datafile = '{}.o5m'.format(self.osmFile)

        if polyfile:
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

        # execute the process ... .wait()
        msg = ''.join(proc.communicate())

        if proc.returncode != 0:
            LOG.error('OSM update has not exited cleanly!')
            LOG.error(msg)

        # rename updated file
        os.rename('new.{}'.format(datafile), datafile)
        os.chdir(curDir)

    def extractAdminLevels(self):
        curDir = os.getcwd()
        os.chdir(self.workDir)
        datafile = '{}.o5m'.format(self.osmFile)

        command = [
            './osmfilter', '-v', datafile, '--keep=admin_level',
            '-o=admin_levels.o5m'
        ]
        LOG.debug('Command: %s', ' '.join(command))

        proc = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            shell=False
        )
        LOG.info('Extracting "admin_levels" from OSM file %s ...', datafile)

        # execute the process ... .wait()
        msg = ''.join(proc.communicate())

        if proc.returncode != 0:
            LOG.error('OSM filter has not exited cleanly!')
            LOG.error(msg)

        os.chdir(curDir)

    def convertO5MtoPBF(self, filename):
        curDir = os.getcwd()
        os.chdir(self.workDir)
        datafile = '{}.o5m'.format(filename)
        new_datafile = '{}.pbf'.format(filename)

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
        msg = ''.join(proc.communicate())

        if proc.returncode != 0:
            LOG.error('OSM convert has not exited cleanly!')
            LOG.error(msg)

        os.chdir(curDir)
