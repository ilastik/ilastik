import vigra
from vigra import graphs as vgraph
#from vigra import ilastiktools
import ilastiktools
import numpy
from lazyflow.roi import roiToSlice, sliceToRoi


class WatershedSegmentor(object):
    # TODO: class OpWatershedSegmentor(Operator)
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
            ndim  = 3
            # TODO: keep reference to labels slot?
            self.supervoxelUint32 = labels
            self.volumeFeat = volume_feat.squeeze()
            if self.volumeFeat.ndim == 3:
                self.gridSegmentor = ilastiktools.GridSegmentor_3D_UInt32()
                self.gridSegmentor.init()

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

            # TODO: keep reference to labels slot? make labels a slot.
            '''
            #h5file = h5py.File(fname)
            #self.supervoxelUint32 = h5file['labels'][:]
            source = OpStreamingHdf5Reader(graph=graph)
            source.Hdf5File.setValue(h5file)
            source.InternalPath.setValue(gname)

            op = OpCompressedCache( parent=None, graph=graph )
            op.BlockShape.setValue( [128, 128, 128] )
            op.Input.connect( source.OutputImage )
            '''
            self.supervoxelUint32 = labels

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

    def preprocess(self, labels, volume_features, roi_stop):
        assert not self.hasSeg, "gridSegmentor was finalized; cannot preprocess."
        self.gridSegmentor.preprocessing(labels=labels, weightArray=volume_features, roiEnd=roi_stop)
        self.nodeNum = self.gridSegmentor.nodeNum()

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
                                    fgSeeds=fgSeeds, bgSeeds=bgSeeds)

    def addSeeds(self, roi, brushStroke):
        if isinstance(self.gridSegmentor, ilastiktools.GridSegmentor_3D_UInt32):
            roiBegin  = roi.start[1:4]
            roiEnd  = roi.stop[1:4]
        else:
            roiBegin  = roi.start[1:3]
            roiEnd  = roi.stop[1:3]

        # TODO: why not this version?
        #roiSlice = roiToSlice( roi.start, roi.stop )
        #roiShape = [s.stop-s.start for s in roiSlice]
        #brushStroke = brushStroke.reshape(roiShape)[0,...,0]
      
        roiShape = [e-b for b,e in zip(roiBegin,roiEnd)]
        brushStroke = brushStroke.reshape(roiShape)

        labels = self.supervoxelUint32(roiSlice).wait()[0,...,0]
        self.gridSegmentor.addSeedBlock(labels=labels, brushStroke=brushStroke)

    def getVoxelSegmentation(self, roi, out = None):
        # TODO: Handle 2D case correctly (do we need all the roi* calculations; why not use roi directly?
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
        # labels = self.supervoxelUint32(roiShape.toSlice()).wait()[0,...,0]
        #roiSlice = roiToSlice( roi.start, roi.stop )
        #labels = self.supervoxelUint32(roiSlice).wait()[0,...,0]

        labels = self.supervoxelUint32(roi.toSlice()).wait()[0,...,0]
        return self.gridSegmentor.getSegmentation(labels=labels, out=out)

    def getSuperVoxelSeg(self):
        return self.gridSegmentor.getSuperVoxelSeg()

    def getSuperVoxelSeeds(self):
        return self.gridSegmentor.getSuperVoxelSeeds()

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

        g.attrs["numNodes"] = self.nodeNum

        gridSeg = self.gridSegmentor
        g.create_dataset("graph", data = gridSeg.serializeGraph())
        g.create_dataset("edgeWeights", data = gridSeg.getEdgeWeights())
        g.create_dataset("nodeSeeds", data = gridSeg.getNodeSeeds())
        g.create_dataset("resultSegmentation", data = gridSeg.getResultSegmentation())
        
        g.file.flush()


    def setResulFgObj(self, fgNodes):
        self.gridSegmentor.setResulFgObj(fgNodes)
