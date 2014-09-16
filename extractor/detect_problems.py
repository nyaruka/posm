#!/usr/bin/python2
# -*- coding: utf-8 -*-
import logging
import logging.config
LOG = logging.getLogger(__file__)

import argparse
import os
import sys

import rtree
import shapely.wkb
from shapely.prepared import prep

from POSMmanagement.settings import POSMSettings
from POSMmanagement.utils import is_file_readable

# setup logging, has to be after osmext.settings
from exposm.writer import AdminLevelWriter
from exposm.reader import AdminLevelReader
from exposm.utils import (
    check_bad_geom, intersect_geom, prepare_osm_id, create_GEOJSON,
    writeProblem
)


def main(settings):

    problems_datasource = create_GEOJSON('', 'problems.geojson')

    admin_level_data_path = os.path.join(
        settings.get('sources').get('data_directory'),
        '{}.pbf'.format(settings.get('sources').get('admin_levels_file'))
    )
    if not(is_file_readable(admin_level_data_path)):
        sys.exit(99)

    lyr_read = AdminLevelReader(admin_level_data_path)

    LOG.info('Detecting problems in the dataset...')
    for layer, feature in lyr_read.readData():
        # get data
        osm_id = prepare_osm_id(feature, layer)
        if not osm_id:
            continue
        geom_raw = feature.GetGeometryRef()

        bad_geom = check_bad_geom(geom_raw, osm_id)
        # BONKERS features usually crash QGIS, we need to skip those
        if bad_geom:
            writeProblem(problems_datasource, osm_id, bad_geom)
            continue

    # write geojson problems file
    problems_datasource = None


parser = argparse.ArgumentParser(
    description='Detect geometry problems in the dataset'
)

parser.add_argument(
    '--settings', default='settings.yaml',
    help='path to the settings file, default: settings.yaml'
)

if __name__ == '__main__':
    # parse the args, and call default function
    args = parser.parse_args()
    proj_settings = POSMSettings(args.settings)

    settings = proj_settings.get_settings()
    admin_levels = proj_settings.get_admin_levels()

    logging.config.dictConfig(settings.get('logging'))

    main(settings=settings)
