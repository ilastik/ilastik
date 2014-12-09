import vigra
from vigra import graphs as vgraph
import numpy


class NewSegmentor(object):
    def __init__(self, labels, volume_feat, edgeWeightFunctor, progressCallback):
        iEdgeMap = vgraph.implicitMeanEdgeMap


        with vigra.Timer("computeRag"):
            self.labels = numpy.squeeze(labels)
            self.labels = numpy.require(self.labels, dtype=numpy.uint32)
            self.volume_feat = numpy.squeeze(volume_feat)
            self.volume_feat = numpy.require(self.volume_feat, dtype=numpy.float32)

            self.shape = self.labels.shape
            self.gridGraph = vgraph.gridGraph(self.shape)
            self.rag = vgraph.regionAdjacencyGraph(self.gridGraph, self.labels)

            self.numNodes = self.rag.nodeNum
        with vigra.Timer("accumulate edge features"):
            print self.volume_feat.shape, self.volume_feat.dtype
            gridGraphEdgeMap = iEdgeMap(self.rag.baseGraph, self.volume_feat) 
            self.edgeCuesMean = self.rag.accumulateEdgeFeatures(gridGraphEdgeMap)


        with vigra.Timer("alloc maps"):
            self.uncertainty = numpy.zeros((self.rag.nodeNum,),numpy.uint8)
            self.segmentation =  numpy.zeros(self.shape + (1,),numpy.uint32)
            self.seeds =  numpy.zeros(self.shape + (1,1),numpy.uint32)
            #self.regionCenter = calcRegionCenters(self._regionVol, self.rag.nodeNum)
            #self.regionSize = calcRegionSizes(self._regionVol, self.rag.nodeNum)


    def run(self, unaries, prios = None, uncertainty="exchangeCount",
            moving_average = False, noBiasBelow = 0, **kwargs):
        

        print "accumulate seeds"
        seeds = numpy.squeeze(self.seeds)
        self.accSeeds = self.rag.accumulateSeeds(seeds)


        print "unique seeds",numpy.unique(self.accSeeds)
        # node weighted watersheds
        

        print "cues",self.edgeCuesMean.shape, self.edgeCuesMean.dtype
        print "seeds",seeds.shape, seeds.dtype

        labelsNodeWeighted  = vgraph.edgeWeightedWatersheds(self.rag, self.edgeCuesMean, self.accSeeds)

        seg = self.rag.projectLabelsToBaseGraph(labelsNodeWeighted)
        print "seg is done"
        print seg.shape
        print numpy.unique(seg)
        self.segmentation[:,:,0] = seg