import logging
logger = logging.getLogger(__file__)

from osgeo import ogr


class FeatureReader(object):
    """
    Reads features from OSM file
    """

    attr_filter = ''

    def __init__(self, filename):
        self.filename = filename

        self.datasource = ogr.Open(self.filename)
        logger.debug('Opening datasource: %s', self.filename)

    def setFilter(self):
        nLayerCount = self.datasource.GetLayerCount()
        # set attribute filters - due to a bug in OSM driver when using
        # OGR_INTERLEAVED_READING
# http://lists.osgeo.org/pipermail/gdal-dev/2014-January/037804.html
# http://trac.osgeo.org/gdal/changeset/26784/trunk/gdal/ogr/ogrsf_frmts/osm
        for iLayer in xrange(nLayerCount):
            lyr = self.datasource.GetLayer(iLayer)
            lyr.SetAttributeFilter(self.attr_filter)

    def test_conformity(self, layer, feature):
        """
        There may be a special case where we need to test if feature conforms
        to specific rules
        """
        return True

    def readData(self):
        # prepare for the layer/feature iteration
        nLayerCount = self.datasource.GetLayerCount()
        thereIsDataInLayer = True

        self.setFilter()
        # simple feature counter
        featureCount = 0

        while thereIsDataInLayer:
            thereIsDataInLayer = False

            # read data from layers using OGR_INTERLEAVED_READING method
            for iLayer in xrange(nLayerCount):
                lyr = self.datasource.GetLayer(iLayer)
                # read next Feature
                feat = lyr.GetNextFeature()
                while(feat is not None):
                    # continue reading features from this layer
                    thereIsDataInLayer = True

                    # if the feature conforms to the feature test then yield
                    if self.test_conformity(lyr, feat):
                        featureCount += 1
                        if featureCount % 1000 == 0:
                            logger.info('Features read: %s', featureCount)

                        # yield feature
                        yield (lyr.GetName(), feat)

                    # force feature removal - required for INTERLEAVED_READING
                    feat = None
                    # get the next feature
                    feat = lyr.GetNextFeature()

        # total features
        logger.info('Total features read: %s', featureCount)


class AdminLevelReader(FeatureReader):
    """
    Specific admin_level reader
    """
    attr_filter = 'admin_level!=\'\''

    def test_conformity(self, layer, feature):
        # if layer has admin_level, use this feature
        if layer.GetLayerDefn().GetFieldIndex('admin_level') >= 0:
            if feature.GetField('boundary') == 'administrative':
                return True
            else:
                logger.debug(
                    'Feature %s, boundary tag value: %s',
                    feature.GetField('osm_id'), feature.GetField('boundary')
                )
                return False
        else:
            return False
