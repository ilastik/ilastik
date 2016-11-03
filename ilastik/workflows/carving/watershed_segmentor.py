import ilastiktools
import gc

from lazyflow.roi import getIntersectingBlocks, getBlockBounds, roiFromShape, TinyVector
from lazyflow.utility.timer import timeLogged

import logging
logger = logging.getLogger(__name__)


class WatershedSegmentor(object):
    def __init__(self, labels, blockSize, prepGrp=None, graphGrp=None):
        self.object_names = dict()
        self.objects = dict()
        self.object_seeds_fg = dict()
        self.object_seeds_bg = dict()
        self.object_seeds_fg_voxels = dict()
        self.object_seeds_bg_voxels = dict()
        self.bg_priority = dict()
        self.no_bias_below = dict()
        self.object_lut = dict()
        self.hasSeg = False
        self._blockSize = blockSize

        def isSegmentorValid(prepGrp, graphGrp):
            if not prepGrp or not graphGrp:
                return False

            # require valid watershed labels cache
            watershedGrp = prepGrp.require_group('watershed_labels')
            watershedValid = len(watershedGrp.keys()) > 0 and \
                                'cache_valid' in watershedGrp.attrs.keys() and \
                                watershedGrp.attrs['cache_valid']

            # require valid graph
            graphValid = 'numNodes' in graphGrp.attrs.keys() and \
                         'graph' in graphGrp.keys() and \
                         'edgeWeights' in graphGrp.keys() and \
                         'nodeSeeds' in  graphGrp.keys() and \
                         'resultSegmentation' in graphGrp.keys()

            return watershedValid and graphValid

        # create segmentor
        self.supervoxelUint32 = labels
        ndim = len(filter(lambda x:x,(TinyVector(self.supervoxelUint32.meta.shape) > 1)))
        if ndim == 3:
            self.gridSegmentor = ilastiktools.GridSegmentor_3D_UInt32()
        elif ndim == 2:
            # TODO: labels and filters are 3D; they would need to be 2D to use GridSegmentor_2D
            #self.gridSegmentor = ilastiktools.GridSegmentor_2D_UInt32()
            self.gridSegmentor = ilastiktools.GridSegmentor_3D_UInt32()
        else:
            raise RuntimeError("internal error")

        # initialize segmentor
        if isSegmentorValid(prepGrp, graphGrp):
            self.nodeNum = graphGrp.attrs['numNodes']

            graphS = graphGrp['graph'][:]
            edgeWeights = graphGrp['edgeWeights'][:]
            nodeSeeds = graphGrp['nodeSeeds'][:]
            resultSegmentation = graphGrp['resultSegmentation'][:]

            self.gridSegmentor.initFromSerialization(serialization=graphS,
                                                     edgeWeights=edgeWeights,
                                                     nodeSeeds=nodeSeeds,
                                                     resultSegmentation=resultSegmentation)

            self.hasSeg = resultSegmentation.max() > 0
        else :
            self.gridSegmentor.init()
            self.nodeNum = self.gridSegmentor.nodeNum()
            self.hasSeg = False


    @timeLogged(logger, logging.INFO)
    def preprocess(self, labels, volume_features, roi_stop):
        assert not self.hasSeg, "gridSegmentor was finalized; cannot preprocess."
        assert not self.gridSegmentor.isFinalized(), "gridSegmentor was finalized; cannot preprocess."
        self.gridSegmentor.preprocessing(labels=labels, weightArray=volume_features, roiEnd=roi_stop)
        self.nodeNum = self.gridSegmentor.nodeNum()

    def finalize(self):
        self.gridSegmentor.finalize()

    @timeLogged(logger, logging.INFO)
    def run(self, unaries, prios = None, noBiasBelow = 0, **kwargs):
        self.gridSegmentor.run(float(prios[1]),float(noBiasBelow))
        seg = self.gridSegmentor.getSuperVoxelSeg()
        self.hasSeg = True

    def clearSegmentation(self):
        self.gridSegmentor.clearSegmentation()

    def setSeeds(self, fgSeeds, bgSeeds):
        self.gridSegmentor.clearSeeds()

        bsz = self._blockSize
        block_shape = (1,bsz,bsz,bsz,1)
        block_starts = getIntersectingBlocks( block_shape, roiFromShape(self.supervoxelUint32.meta.shape) )
        for b_id, block in enumerate(block_starts):
            labels_roi = getBlockBounds(self.supervoxelUint32.meta.shape,block_shape, block)
            labels = self.supervoxelUint32(*labels_roi).wait()[0, ..., 0]
            labels_roi_begin = TinyVector(labels_roi[0][1:-1])
            self.gridSegmentor.addSeeds(labels=labels,
                                        labelsOffset=labels_roi_begin,
                                        fgSeeds=fgSeeds, bgSeeds=bgSeeds)

    def addSeeds(self, roi, brushStroke):
        roiShape = [s.stop-s.start for s in roi.toSlice()]
        brushStroke = brushStroke.reshape(roiShape)[0,...,0]

        labels = self.supervoxelUint32(roi.toSlice()).wait()[0,...,0]
        self.gridSegmentor.addSeedBlock(labels=labels, brushStroke=brushStroke)

    @timeLogged(logger, logging.INFO)
    def getVoxelSegmentation(self, roi, out = None):
        labels = self.supervoxelUint32(roi.toSlice()).wait()[0,...,0]
        return self.gridSegmentor.getSegmentation(labels=labels, out=out)

    def getSuperVoxelSeg(self):
        return self.gridSegmentor.getSuperVoxelSeg()

    def getSuperVoxelSeeds(self):
        return self.gridSegmentor.getSuperVoxelSeeds()

    @timeLogged(logger, logging.INFO)
    def saveH5(self, filename, groupname, mode="w"):
        f = h5py.File(filename, mode)
        try:
            f.create_group(groupname)
        except:
            pass
        h5g = f[groupname]
        self.saveH5G(h5g)

    @timeLogged(logger, logging.INFO)
    def saveH5G(self, h5g):
        g = h5g
        gridSeg = self.gridSegmentor

        if not gridSeg.isFinalized():
            logger.warning(
                "GridSegmentor must be finalized prior to saving graph: '{}'.  File a bug report.".format(
                    g.file.filename))
            gridSeg.finalize()

        def saveDataArray(group_name, data_array):
            gc.collect()
            logger.info( "  serializing {}... ".format(group_name) )
            logger.info( "  saving {} - dtype:{} min/max:({},{}) size:{} shape:{}".format(
                group_name,
                data_array.dtype, data_array.min(), data_array.max(), data_array.size, data_array.shape ))
            g.create_dataset(group_name, data = data_array)
            logger.info( "    flushing... " )
            g.file.flush()


        logger.info( "Saving Watershed Segmentor: group://{}{} - has seg: {} ".format(
                     g.file.filename, g.name, self.hasSeg) )
        logger.info( "  mst: nodes: {} (max id: {}), edges: {} (max id: {})".format(
                        gridSeg.nodeNum(), gridSeg.maxNodeId(),
                        gridSeg.edgeNum(), gridSeg.maxEdgeId()) )

        logger.info( "  saving numNodes: {} ".format( self.nodeNum ))
        g.attrs["numNodes"] = self.nodeNum

        saveDataArray("graph", gridSeg.serializeGraph())
        saveDataArray("edgeWeights", gridSeg.getEdgeWeights())
        saveDataArray("nodeSeeds", gridSeg.getNodeSeeds())
        saveDataArray("resultSegmentation", gridSeg.getResultSegmentation())

        logger.info( "  flushing... " )
        g.file.flush()
        gc.collect()
        logger.info( "  Finished Saving. " )


    def setResulFgObj(self, fgNodes):
        self.gridSegmentor.setResulFgObj(fgNodes)
