#!/usr/bin/python2
# -*- coding: utf-8 -*-

import sys
from osgeo import ogr, gdal, osr

# setup default SRS
srs = osr.SpatialReference()
srs.ImportFromEPSG(4326)

# required for OSM data format
gdal.SetConfigOption('OGR_INTERLEAVED_READING', 'YES')
# set 'OSM_CONFIG_fILE'
gdal.SetConfigOption(
    'OSM_CONFIG_FILE', 'boundary.ini'
)
# this option is required when parsing large datasets, at least in my
# environment, I got lots of "Cannot read node ..." error messages
# http://svn.osgeo.org/gdal/trunk/gdal/ogr/ogrsf_frmts/osm/ogrosmdatasource.cpp
gdal.SetConfigOption('OSM_USE_CUSTOM_INDEXING', 'NO')

# large datasets require a lot of disk space, set temporary directory with
# enough free space
gdal.SetConfigOption('CPL_TMPDIR', '/tmp')

# setup logging options
gdal.SetConfigOption('CPL_TIMESTAMP', 'ON')
gdal.SetConfigOption('CPL_DEBUG', 'ON')
gdal.SetConfigOption('CPL_LOG', '/tmp/gdal_log.log')
gdal.PushErrorHandler('CPLLoggingErrorHandler')
# gdal.SetConfigOption("CPL_LOG_ERRORS", 'ON')


# filename = '/data/australia-oceania-latest.osm.pbf'
# filename = '/data/africa-latest.osm.pbf'
# filename = '/go_video/planet-latest.osm.pbf'
# filename = '/go_video/asia-latest.osm.pbf'
#filename = '/go_video/north-america-latest.osm.pbf'
filename = './pbf/nigeria-latest.osm.pbf'


# define the 'output layer'
drv_save = ogr.GetDriverByName('ESRI Shapefile')
#ds_save = drv_save.CreateDataSource('/data/north_america6.shp')
ds_save = drv_save.CreateDataSource('./out/nigeria.shp')

lyr_save = ds_save.CreateLayer(
    'boundary', srs, ogr.wkbMultiPolygon, options=['ENCODING=UTF-8']
)

if lyr_save is None:
    print 'Layer creation failed.\n'
    sys.exit(1)

field_defn = ogr.FieldDefn('name', ogr.OFTString)
field_defn.SetWidth(254)

if lyr_save.CreateField(field_defn) != 0:
    print 'Creating Name field failed.\n'
    sys.exit(1)

field_defn = ogr.FieldDefn('adminlevel', ogr.OFTString)
field_defn.SetWidth(254)

if lyr_save.CreateField(field_defn) != 0:
    print 'Creating admin_level field failed.\n'
    sys.exit(1)


# open the datasource
ds = ogr.Open(filename)


def save_feature(feat):
    """
    simple save feature function
    """
    new_feat = ogr.Feature(lyr_save.GetLayerDefn())

    new_feat.SetField('name', feat.GetField('name'))
    new_feat.SetField('adminlevel', feat.GetField('admin_level'))
    new_feat.SetGeometry(feat.GetGeometryRef())

    lyr_save.CreateFeature(new_feat)


# prepare for the layer/feature iteration
nLayerCount = ds.GetLayerCount()
thereIsDataInLayer = True

while thereIsDataInLayer:
    thereIsDataInLayer = False
    # set attribute filters - due to a bug in OSM driver when using
    # OGR_INTERLEAVED_READING
    # http://lists.osgeo.org/pipermail/gdal-dev/2014-January/037804.html
    # http://trac.osgeo.org/gdal/changeset/26784/trunk/gdal/ogr/ogrsf_frmts/osm
    for iLayer in xrange(nLayerCount):
        lyr = ds.GetLayer(iLayer)
        filter_ok = lyr.SetAttributeFilter("admin_level = '4'")

    # read data from layers using OGR_INTERLEAVED_READING method
    for iLayer in xrange(nLayerCount):
        lyr = ds.GetLayer(iLayer)
        # read next Feature
        feat = lyr.GetNextFeature()
        while(feat is not None):
            # continue reading features from this layer
            thereIsDataInLayer = True

            try:
                # test if feature has 'admin_level' tag
                # TODO: there is probably a nicer way to do this, check the API
                feat.GetField('admin_level')
            except:
                # no 'admin_level' tag - do nothing
                pass
            else:
                # has 'admin_level' tag - save feature to the new layer
                save_feature(feat)

            # force feature removal - required for INTERLEAVED_READING
            feat.Destroy()
            # get the next feature
            feat = lyr.GetNextFeature()

# destroy datasources - forces save
ds.Destroy()
ds_save.Destroy()
