import ilastiktools
import h5py
import numpy


class WatershedSegmentor(object):
    def __init__(self, labels = None, volume_feat = None, edgeWeightFunctor = None, progressCallback = None,
                 h5file = None):
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
                self.gridSegmentor.preprocessing(self.supervoxelUint32,self.volumeFeat)

            elif self.volumeFeat.ndim == 2:
                ndim = 2
                self.gridSegmentor = ilastiktools.GridSegmentor_2D_UInt32()
                self.gridSegmentor.preprocessing(self.supervoxelUint32.squeeze(),self.volumeFeat)

            else:
                raise RuntimeError("internal error")


            
            # fixe! which of both??!
            self.nodeNum = self.gridSegmentor.nodeNum()
            self.numNodes = self.nodeNum
       
            self.hasSeg = False
        else:
            self.numNodes = h5file.attrs["numNodes"]
            self.nodeNum = self.numNodes
            self.supervoxelUint32 = h5file['labels'][:]
            if(self.supervoxelUint32.squeeze().ndim == 3):
                self.gridSegmentor = ilastiktools.GridSegmentor_3D_UInt32()
            else:
                self.gridSegmentor = ilastiktools.GridSegmentor_2D_UInt32()
            graphS = h5file['graph'][:]
            edgeWeights = h5file['edgeWeights'][:]
            nodeSeeds = h5file['nodeSeeds'][:]
            resultSegmentation = h5file['resultSegmentation'][:]

           
            if(self.supervoxelUint32.squeeze().ndim == 3):
                self.gridSegmentor.preprocessingFromSerialization(labels=self.supervoxelUint32,
                    serialization=graphS, edgeWeights=edgeWeights, nodeSeeds=nodeSeeds, 
                    resultSegmentation=resultSegmentation)
            else:
                self.gridSegmentor.preprocessingFromSerialization(labels=self.supervoxelUint32.squeeze(),
                    serialization=graphS, edgeWeights=edgeWeights, nodeSeeds=nodeSeeds, 
                    resultSegmentation=resultSegmentation)

            self.hasSeg = resultSegmentation.max()>0

    def run(self, unaries, prios = None, uncertainty="exchangeCount",
            moving_average = False, noBiasBelow = 0, **kwargs):
        self.gridSegmentor.run(float(prios[1]),float(noBiasBelow))
        seg = self.gridSegmentor.getSuperVoxelSeg()
        self.hasSeg = True

    def clearSegmentation(self):
        self.gridSegmentor.clearSegmentation()

    def addSeeds(self, roi, brushStroke):
        if isinstance(self.gridSegmentor, ilastiktools.GridSegmentor_3D_UInt32):
            roiBegin  = roi.start[1:4]
            roiEnd  = roi.stop[1:4]
        else:
            roiBegin  = roi.start[1:3]
            roiEnd  = roi.stop[1:3]

        roiShape = [e-b for b,e in zip(roiBegin,roiEnd)]
        brushStroke = brushStroke.reshape(roiShape)
        self.gridSegmentor.addSeeds(brushStroke=brushStroke,roiBegin=roiBegin, 
                                    roiEnd=roiEnd, maxValidLabel=2)

    def getVoxelSegmentation(self, roi):
        if isinstance(self.gridSegmentor, ilastiktools.GridSegmentor_3D_UInt32):
            roiBegin  = roi.start[1:4]
            roiEnd  = roi.stop[1:4]
            return self.gridSegmentor.getSegmentation(roiBegin=roiBegin,roiEnd=roiEnd)
        else:
            roiBegin  = roi.start[1:3]
            roiEnd  = roi.stop[1:3]
            return self.gridSegmentor.getSegmentation(roiBegin=roiBegin,roiEnd=roiEnd)[:,:,None]


    def setSeeds(self,fgSeeds, bgSeeds):
        self.gridSegmentor.setSeeds(fgSeeds, bgSeeds)

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
        g.create_dataset("labels",
                         data=self.supervoxelUint32,
                         compression='gzip',
                         compression_opts=4)

        gridSeg = self.gridSegmentor
        g.create_dataset("graph", data = gridSeg.serializeGraph())
        g.create_dataset("edgeWeights", data = gridSeg.getEdgeWeights())
        g.create_dataset("nodeSeeds", data = gridSeg.getNodeSeeds())
        g.create_dataset("resultSegmentation", data = gridSeg.getResultSegmentation())
        
        g.file.flush()


    def setResulFgObj(self, fgNodes):
        self.gridSegmentor.setResulFgObj(fgNodes)
