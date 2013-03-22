from ilastik.applets.base.appletSerializer import AppletSerializer, getOrCreateGroup, deleteIfPresent
from cylemon.segmentation import MSTSegmentor
import h5py
import numpy

class PreprocessingSerializer( AppletSerializer ):
    def __init__(self, preprocessingTopLevelOperator, *args, **kwargs):
        super(PreprocessingSerializer, self).__init__(*args, **kwargs)
        self._o = preprocessingTopLevelOperator 
        
    def _serializeToHdf5(self, topGroup, hdf5File, projectFilePath):
        preproc = topGroup
        
        for opPre in self._o.innerOperators:
            mst = opPre._prepData[0]
            
            if mst is not None:
                
                #The values to be saved for sigma and filter are the
                #values of the last valid preprocess
                #!These may differ from the current settings!
                
                deleteIfPresent(preproc, "sigma")
                deleteIfPresent(preproc, "filter")
                deleteIfPresent(preproc, "graph")
                
                preproc.create_dataset("sigma",data= opPre.initialSigma)
                preproc.create_dataset("filter",data= opPre.initialFilter)
                 
                preprocgraph = getOrCreateGroup(preproc, "graph")
                mst.saveH5G(preprocgraph)
            
            opPre._unsavedData = False
            
    def _deserializeFromHdf5(self, topGroup, groupVersion, hdf5File, projectFilePath):
        
        assert "sigma" in topGroup.keys()
        assert "filter" in topGroup.keys()
        
        sigma = topGroup["sigma"].value
        sfilter = topGroup["filter"].value
        
        if "graph" in topGroup.keys():
            graphgroup = topGroup["graph"]
        else:
            assert "graphfile" in topGroup.keys()
            #feature: load preprocessed graph from file
            graphgroup = h5py.File(topGroup["graphfile"].value,"r")["graph"]
            
        
        for opPre in self._o.innerOperators:
            
            opPre.initialSigma = sigma
            opPre.Sigma.setValue(sigma)
            opPre.initialFilter = sfilter
            opPre.Filter.setValue(sfilter)
            
            mst = MSTSegmentor.loadH5G(graphgroup)
            opPre._prepData = numpy.array([mst])
        
            opPre.enableDownstream(True)
            opPre._dirty = False
            opPre.applet.writeprotected = True
            
            opPre.PreprocessedData.setDirty()
            
           
    def isDirty(self):
        for opPre in self._o.innerOperators:            
            if opPre._unsavedData:
                return True
        return False
    
    #this is present only for the serializer AppletInterface
    def unload(self):
        pass
    
