import ilastiktools
import gc

from lazyflow.roi import getIntersectingBlocks, getBlockBounds, roiFromShape, roiToSlice, enlargeRoiForHalo, TinyVector
from lazyflow.utility.timer import timeLogged

import logging
logger = logging.getLogger(__name__)


class WatershedSegmentor(object):
    def __init__(self, labels, h5file=None):
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

        if h5file is None:
            self.supervoxelUint32 = labels
            ndim = self.supervoxelUint32.value.squeeze().ndim
            if ndim == 3:
                self.gridSegmentor = ilastiktools.GridSegmentor_3D_UInt32()
            elif ndim == 2:
                self.gridSegmentor = ilastiktools.GridSegmentor_2D_UInt32()
            else:
                raise RuntimeError("internal error")

            self.gridSegmentor.init()
            self.nodeNum = self.gridSegmentor.nodeNum()
            self.hasSeg = False
        else:
            self.supervoxelUint32 = labels
            ndim = self.supervoxelUint32.value.squeeze().ndim
            if ndim == 3:
                self.gridSegmentor = ilastiktools.GridSegmentor_3D_UInt32()
            elif ndim == 2:
                self.gridSegmentor = ilastiktools.GridSegmentor_2D_UInt32()
            else:
                raise RuntimeError("internal error")

            self.nodeNum = h5file.attrs["numNodes"]

            graphS = h5file['graph'][:]
            edgeWeights = h5file['edgeWeights'][:]
            nodeSeeds = h5file['nodeSeeds'][:]
            resultSegmentation = h5file['resultSegmentation'][:]

            # TODO: remove after preprocess fixed                
            #if(self.supervoxelUint32.squeeze().ndim == 3):
            #    self.gridSegmentor.preprocessingFromSerialization(labels=self.supervoxelUint32,
            #        serialization=graphS, edgeWeights=edgeWeights, nodeSeeds=nodeSeeds, 
            #        resultSegmentation=resultSegmentation)
            #else:
            #    self.gridSegmentor.preprocessingFromSerialization(labels=self.supervoxelUint32.squeeze(),
            #        serialization=graphS, edgeWeights=edgeWeights, nodeSeeds=nodeSeeds, 
            #        resultSegmentation=resultSegmentation)

            self.gridSegmentor.initFromSerialization(serialization=graphS,
                edgeWeights=edgeWeights, nodeSeeds=nodeSeeds,
                resultSegmentation=resultSegmentation)

            self.hasSeg = resultSegmentation.max()>0

    @timeLogged(logger, logging.INFO)
    def preprocess(self, labels, volume_features, roi_stop):
        assert not self.hasSeg, "gridSegmentor was finalized; cannot preprocess."
        self.gridSegmentor.preprocessing(labels=labels, weightArray=volume_features, roiEnd=roi_stop)
        self.nodeNum = self.gridSegmentor.nodeNum()

    @timeLogged(logger, logging.INFO)
    def run(self, unaries, prios = None, noBiasBelow = 0, **kwargs):
        self.gridSegmentor.run(float(prios[1]),float(noBiasBelow))
        seg = self.gridSegmentor.getSuperVoxelSeg()
        self.hasSeg = True

    def clearSegmentation(self):
        self.gridSegmentor.clearSegmentation()

    def setSeeds(self, fgSeeds, bgSeeds):
        self.gridSegmentor.clearSeeds()

        # TODO: handle iterating over labels correctly - read labels blockwise -  see opPreprocessing.execute for example
        labels = self.supervoxelUint32.value[0,...,0]
        labels_roi_begin = TinyVector([0] * len(labels.shape))
        self.gridSegmentor.addSeeds(labels=labels, labelsOffset=labels_roi_begin,
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
