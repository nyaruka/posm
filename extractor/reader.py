import logging
logger = logging.getLogger(__file__)

from osgeo import ogr


class FeatureReader(object):
    """
    Reads features from OSM file
    """

    def __init__(self, filename):
        self.filename = filename

        self.datasource = ogr.Open(self.filename)
        logger.debug('Opening datasource: %s', self.filename)

    def readData(self):
        # prepare for the layer/feature iteration
        nLayerCount = self.datasource.GetLayerCount()
        thereIsDataInLayer = True

        # simple feature counter
        featureCount = 0

        while thereIsDataInLayer:
            thereIsDataInLayer = False
            # set attribute filters - due to a bug in OSM driver when using
            # OGR_INTERLEAVED_READING
# http://lists.osgeo.org/pipermail/gdal-dev/2014-January/037804.html
# http://trac.osgeo.org/gdal/changeset/26784/trunk/gdal/ogr/ogrsf_frmts/osm
            for iLayer in xrange(nLayerCount):
                lyr = self.datasource.GetLayer(iLayer)
                lyr.SetAttributeFilter('admin_level!=\'\'')

            # read data from layers using OGR_INTERLEAVED_READING method
            for iLayer in xrange(nLayerCount):
                lyr = self.datasource.GetLayer(iLayer)
                # read next Feature
                feat = lyr.GetNextFeature()
                while(feat is not None):
                    # continue reading features from this layer
                    thereIsDataInLayer = True

                    try:
                        # test if feature has 'admin_level' tag
                        # TODO: there is probably a nicer way to do this,
                        # check the API
                        feat.GetField('admin_level')
                    except:
                        # no 'admin_level' tag - do nothing
                        pass
                    else:
                        # has 'admin_level' tag - yield feature
                        featureCount += 1
                        if featureCount % 1000 == 0:
                            logger.info('Features read: %s', featureCount)

                        # yield feature
                        yield feat

                    # force feature removal - required for INTERLEAVED_READING
                    feat.Destroy()
                    # get the next feature
                    feat = lyr.GetNextFeature()

        # total features
        logger.info('Total features read: %s', featureCount)
