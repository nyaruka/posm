import logging
logger = logging.getLogger(__file__)

import sys
import os.path
from osgeo import ogr, osr

from .settings import settings


class FeatureWriter(object):
    """
    Writes features to SHP file
    """

    @classmethod
    def create_shp(cls, filename, *args, **kwargs):
        """
        Stores data to a SHP file (on disk)
        """
        shpWriter = cls(*args, **kwargs)

        shpWriter.filename = os.path.join(
            settings.get('exposm').get('shp_output_directory'),
            '{}.shp'.format(filename)
        )

        shpWriter.driver = ogr.GetDriverByName('ESRI Shapefile')

        shpWriter.createSHPLayer()
        return shpWriter

    @classmethod
    def create_postgis(cls, layer_name, *args, **kwargs):
        """
        Stores data to a POSTGIS database
        """

        postgisWriter = cls(*args, **kwargs)

        postgisWriter.layer_name = layer_name

        postgisWriter.database = settings.get('exposm').get('postgis')

        postgisWriter.driver = ogr.GetDriverByName('PostgreSQL')

        postgisWriter.createPOSTGISLayer()
        return postgisWriter

    def __init__(self, autoremove=True, srs_epsg=4326):

        self.autoremove = autoremove

        # setup default SRS
        self.srs = osr.SpatialReference()
        self.srs.ImportFromEPSG(srs_epsg)

    def createPOSTGISLayer(self):
        self.datasource = ogr.Open(self.database)

        if self.datasource is None:
            logger.critical('Datasource creation failed.')
            sys.exit(1)

        self.layer = self.datasource.CreateLayer(
            self.layer_name, self.srs, ogr.wkbMultiPolygon,
            options=['OVERWRITE=YES']
        )

        if self.layer is None:
            logger.critical('Layer creation failed.')
            sys.exit(1)

        logger.info('Layer created: %s', self.layer_name)
        self.createFields()

    def createSHPLayer(self):
        self.datasource = self.driver.CreateDataSource(self.filename)

        if self.datasource is None:
            logger.critical('Datasource creation failed.')
            sys.exit(1)

        self.layer = self.datasource.CreateLayer(
            'boundary', self.srs, ogr.wkbMultiPolygon,
            options=['ENCODING=UTF-8']
        )

        if self.layer is None:
            logger.critical('Layer creation failed.')
            sys.exit(1)

        logger.info('Layer created: %s', self.filename)
        self.createFields()

    def defineFields(self):
        raise NotImplementedError

    def createFields(self):
        for field in self.defineFields():
            if self.layer.CreateField(field) != 0:
                logger.error('Creating field failed.')
                sys.exit(1)

    def saveFeature(self, feature_data, feature_geom):
        """
        simple save feature function
        """
        new_feat = ogr.Feature(self.layer.GetLayerDefn())

        for field in feature_data:
            new_feat.SetField(field[0], field[1])

        # set geometry for the feature
        new_feat.SetGeometry(feature_geom)
        # add feature to the layer
        self.layer.CreateFeature(new_feat)

        new_feat = None


class AdminLevelWriter(FeatureWriter):
    """
    Define fields specific for the admin_level features
    """

    def defineFields(self):
        id_def = ogr.FieldDefn('osm_id', ogr.OFTString)
        id_def.SetWidth(254)

        name_def = ogr.FieldDefn('name', ogr.OFTString)
        name_def.SetWidth(254)

        name_en_def = ogr.FieldDefn('name_en', ogr.OFTString)
        name_en_def.SetWidth(254)

        adminlevel_def = ogr.FieldDefn('adminlevel', ogr.OFTInteger)
        # adminlevel_def.SetWidth(254)

        iso3166_def = ogr.FieldDefn('iso3166', ogr.OFTString)
        iso3166_def.SetWidth(254)

        is_in_def = ogr.FieldDefn('is_in', ogr.OFTString)
        is_in_def.SetWidth(254)

        return [
            id_def, name_def, name_en_def, adminlevel_def, iso3166_def,
            is_in_def
        ]


class DiscardFeatureWriter(FeatureWriter):
    """
    Define fields specific for the discarded features
    """

    def defineFields(self):
        id_def = ogr.FieldDefn('osm_id', ogr.OFTString)
        id_def.SetWidth(254)

        name_def = ogr.FieldDefn('name', ogr.OFTString)
        name_def.SetWidth(254)

        adminlevel_def = ogr.FieldDefn('adminlevel', ogr.OFTInteger)
        # adminlevel_def.SetWidth(254)

        reason_def = ogr.FieldDefn('reason', ogr.OFTString)
        reason_def.SetWidth(254)

        return [id_def, name_def, adminlevel_def, reason_def]
