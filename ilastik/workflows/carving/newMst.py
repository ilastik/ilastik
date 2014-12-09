import vigra
from vigra import graphs as vgraph
import numpy


class NewSegmentor(object):
    def __init__(self, labels, volume_feat, edgeWeightFunctor, progressCallback):
        iEdgeMap = vgraph.implicitMeanEdgeMap

        self.object_names = dict()
        self.regionVol = labels
        with vigra.Timer("computeRag"):
            self.labels = numpy.squeeze(labels)
            self.labels = numpy.require(self.labels, dtype=numpy.uint32)
            self.volume_feat = numpy.squeeze(volume_feat)
            self.volume_feat = numpy.require(self.volume_feat, dtype=numpy.float32)

            self.shape = self.labels.shape
            self.nDim = len(self.shape)
            self.gridGraph = vgraph.gridGraph(self.shape)
            self.rag = vgraph.regionAdjacencyGraph(self.gridGraph, self.labels)

            self.numNodes = self.rag.nodeNum
        with vigra.Timer("accumulate edge features"):
            print self.volume_feat.shape, self.volume_feat.dtype
            gridGraphEdgeMap = iEdgeMap(self.rag.baseGraph, self.volume_feat) 
            self.edgeCuesMean = self.rag.accumulateEdgeFeatures(gridGraphEdgeMap)

            print "min", self.edgeCuesMean.min()
            print "max", self.edgeCuesMean.max()

            self.edgeCuesMean = 1.0 - numpy.exp(-0.001*self.edgeCuesMean)

            print "min", self.edgeCuesMean.min()
            print "max", self.edgeCuesMean.max()


        with vigra.Timer("alloc maps"):
            self.uncertainty = numpy.zeros((self.rag.nodeNum,),numpy.uint8)
            if(self.nDim == 2):
                self.segmentation =  numpy.zeros(self.shape + (1,),numpy.uint32)
                self.seeds =  numpy.zeros(self.shape + (1,1),numpy.uint32)
            else:
                self.segmentation =  numpy.zeros(self.shape ,numpy.uint32)
                self.seeds =  numpy.zeros(self.shape + (1,),numpy.uint32)
            #self.regionCenter = calcRegionCenters(self._regionVol, self.rag.nodeNum)
            #self.regionSize = calcRegionSizes(self._regionVol, self.rag.nodeNum)


    def run(self, unaries, prios = None, uncertainty="exchangeCount",
            moving_average = False, noBiasBelow = 0, **kwargs):
            
        backgroundPrior = float(prios[1])
        seeds = numpy.squeeze(self.seeds)
        self.accSeeds = self.rag.accumulateSeeds(seeds)

        print "unaries",unaries.shape, unaries.min(),unaries.max()


        # node weighted watersheds
        

        labelsNodeWeighted  = vgraph.edgeWeightedWatersheds(self.rag, self.edgeCuesMean, self.accSeeds,backgroundBias=backgroundPrior, backgroundLabel=1)

        seg = self.rag.projectLabelsToBaseGraph(labelsNodeWeighted)
        print "seg is done",self.nDim
        print seg.shape
        print numpy.unique(seg)
        if self.nDim == 2:
            self.segmentation[:,:,0] = seg
        else :
            self.segmentation[:,:,:] = seg




    def saveH5(self, filename, groupname, mode="w"):
        print "saving segmentor to %r[%r] ..." % (filename, groupname)
        f = h5py.File(filename, mode)
        try:
            f.create_group(groupname)
        except:
            pass
        h5g = f[groupname]
        self.saveH5G(h5g)

    def saveH5G(self, h5g):
        """        g = h5g
                g.attrs["numNodes"] = self.numNodes
                g.attrs["edgeWeightFunctor"] = self._edgeWeightFunctor
                g.create_dataset("labels", data = self.regionVol)



                cdef np.ndarray[dtype=np.int32_t, ndim = 2] indices = np.ndarray((self.graph.maxArcId()+1,2),dtype=np.int32)
                cdef np.ndarray[dtype=np.float32_t, ndim = 1] data = np.ndarray((self.graph.maxArcId()+1,),dtype=np.float32)
                cdef NodeIt node
                cdef OutArcIt arcit
                cdef int a,b,i

                node = NodeIt(deref(self.graph))
                i = 0
                while node != INVALID:
                    arcit = OutArcIt(deref(self.graph),Node(node))
                    while arcit != INVALID:
                        a = self.graph.id(self.graph.source(arcit))
                        b = self.graph.id(self.graph.target(arcit))
                        indices[i,0] = a
                        indices[i,1] = b
                        data[i] = deref(self.arcMap)[arcit]
                        i += 1
                        inc(arcit)
                    inc(node)
                
                g.create_dataset("coo_indices",data=indices)
                g.create_dataset("coo_data",data=data)
                g.create_dataset("regions", data=self._regionVol)
                g.create_dataset("regionCenter", data=self._regionCenter)
                g.create_dataset("regionSize", data=self._regionSize)
                g.create_dataset("seeds",data = self._seeds)
                g.create_dataset("objects",data = self._objects)

                sg = g.create_group("objects_seeds")
                
                g.file.flush()
                
                # delete old attributes
                for k in sg.attrs.keys():
                    del sg.attrs[k]
                  

                # insert new attributes
                for k,v in self.object_names.items():
                      print "   -> saving object %r with Nr=%r" % (k,v)
                      sg.attrs[k] = v
                      og = sg.create_group(k)
                      og.create_dataset("foreground", data = self.object_seeds_fg[k])
                      og.create_dataset("background", data = self.object_seeds_bg[k])

                if self._rawData is not None:
                    g.create_dataset("raw",data=self._rawData)

                g.file.flush()
                print "   done"
        """
        pass
