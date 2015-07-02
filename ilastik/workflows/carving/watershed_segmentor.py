import vigra
from vigra import graphs as vgraph
#from vigra import ilastiktools
import ilastiktools
import numpy


class WatershedSegmentor(object):
    def __init__(self, h5file = None):
        self.object_names = dict()
        self.objects = dict()
        self.object_seeds_fg = dict()
        self.object_seeds_bg = dict()
        self.object_seeds_fg_voxels = dict()
        self.object_seeds_bg_voxels = dict()
        self.bg_priority =dict()
        self.no_bias_below = dict()
        self.object_lut = dict()
        self.hasSeg = False

        if h5file is None:
            ndim  = 3
            self.supervoxelUint32 = labels
            self.volumeFeat = volume_feat.squeeze()
            if self.volumeFeat.ndim == 3:
                self.gridSegmentor = ilastiktools.GridSegmentor_3D_UInt32()
                self.gridSegmentor.init()
                # TODO: remove?
                #self.supervoxelUint32 = labels
                #self.volumeFeat = volume_feat.squeeze()

            elif self.volumeFeat.ndim == 2:
                ndim = 2
                self.gridSegmentor = ilastiktools.GridSegmentor_2D_UInt32()
                self.gridSegmentor.init()
                # TODO: remove after preprocess fixed                
                #self.gridSegmentor.preprocessing(self.supervoxelUint32.squeeze(),self.volumeFeat)

            else:
                raise RuntimeError("internal error")

            self.nodeNum = self.gridSegmentor.nodeNum()
            self.hasSeg = False
        else:
            self.nodeNum = h5file.attrs["numNodes"]

            # TODO: remove?
            #self.supervoxelUint32 = h5file['labels'][:]

            if(self.supervoxelUint32.squeeze().ndim == 3):
                self.gridSegmentor = ilastiktools.GridSegmentor_3D_UInt32()
            else:
                self.gridSegmentor = ilastiktools.GridSegmentor_2D_UInt32()

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

    def preprocess(self, labels, volume_features):
        self.gridSegmentor.preprocessing(labels=labels, edgeWeights=volume_features)

    def run(self, unaries, prios = None, uncertainty="exchangeCount",
            moving_average = False, noBiasBelow = 0, **kwargs):
        self.gridSegmentor.run(float(prios[1]),float(noBiasBelow))
        seg = self.gridSegmentor.getSuperVoxelSeg()
        self.hasSeg = True

    def clearSegmentation(self):
        self.gridSegmentor.clearSegmentation()

    def setSeeds(self, fgSeeds, bgSeeds):
        self.gridSegmentor.clearSeeds()

        # TODO: handle iterating over labels correctly
        # see opPreprocessing.execute for example

        self.gridSegmentor.addSeeds(labels=labels, labelsOffset=labels_roi_begin,
                                    fgSeeds, bgSeeds)

    def addSeeds(self, roi, brushStroke):
        if isinstance(self.gridSegmentor, ilastiktools.GridSegmentor_3D_UInt32):
            roiBegin  = roi.start[1:4]
            roiEnd  = roi.stop[1:4]
        else:
            roiBegin  = roi.start[1:3]
            roiEnd  = roi.stop[1:3]

        roiShape = [e-b for b,e in zip(roiBegin,roiEnd)]
        brushStroke = brushStroke.reshape(roiShape)

        # TODO: handle labels roi correctly
        # see opPreprocessing.execute for example

        self.gridSegmentor.addSeedBlock(labels=labels, brushStroke=brushStroke)

    def getVoxelSegmentation(self, roi, out = None):
        if isinstance(self.gridSegmentor, ilastiktools.GridSegmentor_3D_UInt32):
            roiBegin  = roi.start[1:4]
            roiEnd  = roi.stop[1:4]
            # TODO: remove?
            #return self.gridSegmentor.getSegmentation(roiBegin=roiBegin,roiEnd=roiEnd, out=out)
        else:
            roiBegin  = roi.start[1:3]
            roiEnd  = roi.stop[1:3]
            # TODO: remove?
            #return self.gridSegmentor.getSegmentation(roiBegin=roiBegin,roiEnd=roiEnd, out=out)[:,:,None]

        roiShape = [e-b for b,e in zip(roiBegin,roiEnd)]

        # TODO: handle labels roi correctly
        # see opPreprocessing.execute for example

        return self.gridSegmentor.getSegmentation(labels=labels, out=out)

    def getSuperVoxelSeg(self):
        return  self.gridSegmentor.getSuperVoxelSeg()

    def getSuperVoxelSeeds(self):
        return  self.gridSegmentor.getSuperVoxelSeeds()

    def saveH5(self, filename, groupname, mode="w"):
        f = h5py.File(filename, mode)
        try:
            f.create_group(groupname)
        except:
            pass
        h5g = f[groupname]
        self.saveH5G(h5g)

    def saveH5G(self, h5g):
        g = h5g

        g.attrs["numNodes"] = self.numNodes
        # TODO: save labels blockwise
        '''
        g.create_dataset("labels",
                         data=self.supervoxelUint32,
                         compression='gzip',
                         compression_opts=4)
        '''

        gridSeg = self.gridSegmentor
        g.create_dataset("graph", data = gridSeg.serializeGraph())
        g.create_dataset("edgeWeights", data = gridSeg.getEdgeWeights())
        g.create_dataset("nodeSeeds", data = gridSeg.getNodeSeeds())
        g.create_dataset("resultSegmentation", data = gridSeg.getResultSegmentation())
        
        g.file.flush()


    def setResulFgObj(self, fgNodes):
        self.gridSegmentor.setResulFgObj(fgNodes)
