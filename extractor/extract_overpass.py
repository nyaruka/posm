#!/usr/bin/python2
# -*- coding: utf-8 -*-
import logging
import logging.config

from osgeo import ogr

LOG = logging.getLogger(__file__)

import argparse
import sys
import zipfile
import tempfile
import glob
import subprocess

import rtree
import shapely.wkb
from shapely.prepared import prep
from decimal import Decimal

from POSMmanagement.settings import POSMSettings
from POSMmanagement.utils import is_file_readable

# setup logging, has to be after osmext.settings
import requests
from exposm.writer import AdminLevelWriter
from exposm.reader import GEOJSONAdminLevelReader
from exposm.utils import (
    check_bad_geom, intersect_geom, create_GEOJSON,
    writeProblem
)

import xml.etree.ElementTree as ET
import json
import time

def download_from_overpass(relation_ids, level=0, country=""):
    geojson = dict(
        type="FeatureCollection",
        features=[],
    )

    children = []
    for relation_id in relation_ids:
        print(f" * Fetching data for {relation_id}")

        # first query for the metadata from overpass
        query = f"""
        [timeout:3600];
        relation({relation_id});
        out geom;
        """
        metadata = requests.get("http://overpass-api.de/api/interpreter", data=query)
        root = ET.fromstring(metadata.content)

        # build our list of children
        relation_children = [el.get("ref") for el in root.findall('./relation/member[@type="relation"][@role="subarea"]')]
        children += relation_children

        # get our admin level
        admin_level = root.find('./relation/tag[@k="admin_level"]').get("v")

        # and our names in local and English
        name = root.find('./relation/tag[@k="name"]').get("v")

        if country == "":
            country = name

        with open("feature.osm", "w") as f:
            f.write(str(metadata.content))

        # convert to geojson
        converted = subprocess.check_output(["/Users/nicp/.nvm/versions/node/v12.16.1/bin/osmtogeojson", "feature.osm"])
        features = json.loads(converted)
        found = False
        for feature in features["features"]:
            if feature["id"] == f"relation/{relation_id}":
                feature["properties"]["osm_id"] = f"{relation_id}"
                feature["properties"]["name_en"] = feature["properties"].get("name_en", name)
                geojson["features"].append(feature)
                found = True

        if not found:
            raise Exception(f"unable to find feature {relation_id} in generated geojson")

        time.sleep(5)

    # write our file out
    filename = f"{country.lower()}_{level}.geojson"
    with open(filename, "w") as f:
        f.write(json.dumps(geojson, indent="  "))

    files = [filename]
    # export our children if we have any
    if children:
        files += download_from_overpass(children, level=level+1, country=country)

    return files


def main(settings, problems_geojson, relation_id):

    if problems_geojson:
        problems_datasource = create_GEOJSON('', 'problems.geojson')

    files = download_from_overpass([relation_id])

    adm_0_temp = set()
    adm_1_temp = set()
    adm_2_temp = set()

    unusable_features = set()
    # setup index
    spat_index_0 = rtree.index.Index()
    # extract countries
    admin_level_0 = {}

    lyr_save = AdminLevelWriter.create_postgis('admin_level_0', settings)
    lyr_read = GEOJSONAdminLevelReader(files[0])

    feature_id = 0

    LOG.info('Started exporting admin_level_0 boundaries!')
    for layer, feature in lyr_read.readData():
        osm_id = feature.GetField("osm_id")
        name = feature.GetField('name')
        name_en = feature.GetField('name_en')

        geom_raw = ogr.ForceToMultiPolygon(feature.GetGeometryRef())

        feature_data = (
            ('osm_id', osm_id),
            ('name', name),
            ('name_en', name_en),
            ('adminlevel', 0),
            ('iso3166', osm_id),
            ('is_in', None)
        )

        bad_geom = check_bad_geom(geom_raw, osm_id)
        # BONKERS features usually crash QGIS, we need to skip those
        if bad_geom:
            # add bad geom to the list
            unusable_features.add(osm_id)
            # skip further processing
            if problems_geojson:
                writeProblem(problems_datasource, osm_id, bad_geom)
            continue

        geom = shapely.wkb.loads(geom_raw.ExportToWkb())

        lyr_save.saveFeature(feature_data, geom_raw)
        admin_level_0.update({osm_id: prep(geom)})
        spat_index_0.insert(
            feature_id, geom.envelope.bounds, obj=osm_id
        )
        LOG.debug('Index %s, record %s', feature_id, osm_id)

        feature_id += 1

    lyr_read.datasource = None
    lyr_save.datasource = None

    # write geojson problems file
    if problems_geojson:
        problems_datasource = None

    # extract states
    admin_level_1 = {}
    # create index
    spat_index_1 = rtree.index.Index()

    feature_id = 0

    level1_file = files[1]
    print(f"Opening {level1_file}")

    lyr_save = AdminLevelWriter.create_postgis('admin_level_1', settings)
    lyr_read = GEOJSONAdminLevelReader(level1_file)

    for layer, feature in lyr_read.readData():
        osm_id = feature.GetField("osm_id")
        name = feature.GetField('name')
        name_en = feature.GetField('name_en')

        geom_raw = ogr.ForceToMultiPolygon(feature.GetGeometryRef())

        if osm_id in unusable_features:
            # skip this feature
            LOG.debug(
                'Feature previously marked as unusable: %s, skipping', osm_id
            )
            continue

        geom = shapely.wkb.loads(geom_raw.ExportToWkb())

        # check spatial relationship
        # representative point is guaranteed within polygon
        geom_repr = geom.representative_point()
        # check index intersection

        is_in = intersect_geom(geom_repr, spat_index_0, admin_level_0)

        if not(is_in):
            # if we can't determine relationship, skip this feature
            LOG.info('Missing country information ... %s', osm_id)
            continue

        feature_data = (
            ('osm_id', osm_id),
            ('name', name),
            ('name_en', name_en),
            ('adminlevel', 1),
            ('iso3166', None),
            ('is_in', is_in)
        )

        lyr_save.saveFeature(feature_data, geom_raw)
        admin_level_1.update({osm_id: prep(geom)})
        spat_index_1.insert(
            feature_id, geom.envelope.bounds, obj=osm_id
        )
        LOG.debug('Index %s, record %s', feature_id, osm_id)

        feature_id += 1

        adm_1_temp.add(osm_id)

    lyr_read.datasource = None
    lyr_save.datasource = None

    lyr_save = AdminLevelWriter.create_postgis('admin_level_2', settings)
    level2_file = files[2] if len(files) >= 3 else None
    if level2_file is not None:
        lyr_read = GEOJSONAdminLevelReader(level2_file)

        for layer, feature in lyr_read.readData():
            osm_id = feature.GetField("osmid")
            name = feature.GetField('name')
            name_en = feature.GetField('name_en')

            geom_raw = ogr.ForceToMultiPolygon(feature.GetGeometryRef())

            if osm_id in unusable_features:
                # skip this feature
                LOG.debug(
                    'Feature previously marked as unusable: %s, skipping', osm_id
                )
                continue

            geom = shapely.wkb.loads(geom_raw.ExportToWkb())

            # representative point is guaranteed within polygon
            geom_repr = geom.representative_point()

            is_in = intersect_geom(geom_repr, spat_index_0, admin_level_0)

            is_in_state = intersect_geom(geom_repr, spat_index_1, admin_level_1)

            if not(is_in_state):
                # if we can't determine relationship, skip this feature
                LOG.info('Missing state information ... %s', osm_id)
                continue

            feature_data = (
                ('osm_id', osm_id),
                ('name', name),
                ('name_en', name_en),
                ('adminlevel', 2),
                ('iso3166', None),
                ('is_in', is_in_state)
            )

            lyr_save.saveFeature(feature_data, geom_raw)
            adm_2_temp.add(osm_id)

        lyr_read.datasource = None
        lyr_save.datasource = None


parser = argparse.ArgumentParser(description='Extract admin levels (GEOJSON)')

parser.add_argument(
    '--settings', default='settings.yaml',
    help='path to the settings file, default: settings.yaml'
)

parser.add_argument(
    '--problems_as_geojson', action='store_true', default=False,
    help='Generate problems.geojson in the current directory'
)

parser.add_argument(
    'relation_id',
    help="Relation ID of the country to extract from overpass"
)

if __name__ == '__main__':
    # parse the args, and call default function
    args = parser.parse_args()
    proj_settings = POSMSettings(args.settings)

    settings = proj_settings.get_settings()

    logging.config.dictConfig(settings.get('logging'))

    main(
        settings=settings, problems_geojson=args.problems_as_geojson, relation_id=args.relation_id,
    )
