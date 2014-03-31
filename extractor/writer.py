import sys
from osgeo import ogr, osr


class FeatureWriter(object):
    """
    Writes features to SHP file
    """

    def __init__(
            self, filename, filetype='SHP', autoremove=True, srs_epsg=4326):

        self.filename = filename
        self.autoremove = autoremove

        # setup default SRS
        self.srs = osr.SpatialReference()
        self.srs.ImportFromEPSG(srs_epsg)

        if filetype == 'SHP':
            self.driver = ogr.GetDriverByName('ESRI Shapefile')
        else:
            raise NotImplemented

        # init layer
        self.createLayer()
        self.createFields()

    def createLayer(self):
        self.datasource = self.driver.CreateDataSource(self.filename)

        if self.datasource is None:
            print 'Datasource creation failed.\n'
            sys.exit(1)

        self.layer = self.datasource.CreateLayer(
            'boundary', self.srs, ogr.wkbMultiPolygon,
            options=['ENCODING=UTF-8']
        )

        if self.layer is None:
            print 'Layer creation failed.\n'
            sys.exit(1)

    def defineFields(self):
        name_def = ogr.FieldDefn('name', ogr.OFTString)
        name_def.SetWidth(254)

        adminlevel_def = ogr.FieldDefn('adminlevel', ogr.OFTString)
        adminlevel_def.SetWidth(254)

        return [name_def, adminlevel_def]

    def createFields(self):
        for field in self.defineFields():
            if self.layer.CreateField(field) != 0:
                print 'Creating field failed.\n'
                sys.exit(1)

    def saveFeature(self, feat):
        """
        simple save feature function
        """
        new_feat = ogr.Feature(self.layer.GetLayerDefn())

        new_feat.SetField('name', feat.GetField('name'))
        new_feat.SetField('adminlevel', feat.GetField('admin_level'))
        new_feat.SetGeometry(feat.GetGeometryRef())

        self.layer.CreateFeature(new_feat)
