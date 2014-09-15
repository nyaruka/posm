#!/usr/bin/python2
# -*- coding: utf-8 -*-
import logging
LOG = logging.getLogger(__file__)
import logging.config

import argparse

from POSMmanagement.db import DBManagement
from POSMmanagement.settings import POSMSettings
from POSMmanagement.osmdata import OSMmanagement
from POSMmanagement.process import ProcessManagement
from POSMmanagement.project import ProjectManagement


def update_data(args):
    # initialize settings
    proj_settings = POSMSettings(args.settings, verbose=args.verbose)

    osm_man = OSMmanagement(proj_settings, verbose=args.verbose)
    osm_man.updateOSM()
    osm_man.extractAdminLevels()
    osm_man.convertO5MtoPBF()


def extract_and_simplify(args):
    # initialize settings
    proj_settings = POSMSettings(args.settings, verbose=args.verbose)

    ext_sim = ProcessManagement(proj_settings, verbose=args.verbose)
    ext_sim.processAdminLevels(args.settings)
    ext_sim.deconstructGeometry()
    ext_sim.createBaseTopology()
    ext_sim.simplifyAdminLevels(args.tolerance)
    ext_sim.convertToGeoJson(args.settings)


def run_all(args):
    update_data(args)
    extract_and_simplify(args)


def download_OSM(args):
    proj_settings = POSMSettings(args.settings, verbose=args.verbose)
    osm_man = OSMmanagement(proj_settings, verbose=args.verbose)
    osm_man.downloadOSM(args.data_url)
    osm_man.convertOSMtoO5M()


def create_DB(args):
    proj_settings = POSMSettings(args.settings, verbose=args.verbose)
    db_man = DBManagement(proj_settings, verbose=args.verbose)
    db_man.createDatabase()


def init_dir(args):
    proj_settings = POSMSettings(args.settings, verbose=args.verbose)
    proj_man = ProjectManagement(proj_settings, verbose=args.verbose)
    proj_man.initDirectory()


def cut_data(args):
    proj_settings = POSMSettings(args.settings, verbose=args.verbose)
    proj_man = ProjectManagement(proj_settings, verbose=args.verbose)
    proj_man.cutExtract(args.planetOSM)


# add
parser = argparse.ArgumentParser(description='Manage common POSM tasks')
subparsers = parser.add_subparsers(title='Tasks')

# run_all
parser_run_all = subparsers.add_parser(
    'run_all', help='updateOSM data, extractAdminLevels, simplifyAdminLevels'
)
parser_run_all.add_argument(
    '--tolerance', type=float, default=0.001,
    help=(
        'Tolerance parameter for DouglasPeucker simplification algorithm '
        '(default: 0.001)'
    )
)
parser_run_all.set_defaults(func=run_all)

# update_data
parser_update_data = subparsers.add_parser(
    'update_data', help='updateOSM data'
)

parser_update_data.set_defaults(func=update_data)

# extract_and_simplify
parser_ext_sim = subparsers.add_parser(
    'extract_and_simplify', help='extractAdminLevels, simplifyAdminLevels'
)
parser_ext_sim.add_argument(
    '--tolerance', type=float, default=0.001,
    help=(
        'Tolerance parameter for DouglasPeucker simplification algorithm '
        '(default: 0.001)'
    )
)
parser_ext_sim.set_defaults(func=extract_and_simplify)

# download_OSM
parser_download_OSM = subparsers.add_parser(
    'download_OSM',
    help='downloads OSM data'
)
parser_download_OSM.add_argument('data_url', help='OSM data http URI')

parser_download_OSM.set_defaults(func=download_OSM)

# create_DB
parser_create_DB = subparsers.add_parser(
    'create_DB',
    help='creates new PostGIS database and load functions'
)
parser_create_DB.set_defaults(func=create_DB)

# init_dir
parser_init_dir = subparsers.add_parser(
    'init_dir', help='initializes empty data directory'
)

parser_init_dir.set_defaults(func=init_dir)

# cut_data
parser_cut_data = subparsers.add_parser(
    'cut_data', help='cuts OSM data from the planet osm file'
)
parser_cut_data.add_argument(
    'planetOSM', help='Full path of the planetOSM file in O5M format'
)
parser_cut_data.set_defaults(func=cut_data)


# script arguments
parser.add_argument(
    '--verbose', action='store_true', default=False,
    help='show verbose execution messages'
)

parser.add_argument(
    '--settings', default='settings.yaml',
    help='path to the settings file, default: settings.yaml'
)


if __name__ == '__main__':
    # parse the args, and call default function
    args = parser.parse_args()

    proj_settings = POSMSettings(args.settings, verbose=args.verbose)
    settings = proj_settings.get_settings()

    # setup logging, has to be after osmext.settings
    logging.config.dictConfig(settings.get('logging'))

    args.func(args)
