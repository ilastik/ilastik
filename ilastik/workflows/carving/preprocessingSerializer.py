from ilastik.applets.base.appletSerializer import AppletSerializer, getOrCreateGroup, deleteIfPresent
from cylemon.segmentation import MSTSegmentor
import h5py
import numpy
import os

class PreprocessingSerializer( AppletSerializer ):
    def __init__(self, preprocessingTopLevelOperator, *args, **kwargs):
        super(PreprocessingSerializer, self).__init__(*args, **kwargs)
        self._o = preprocessingTopLevelOperator 
        self.caresOfHeadless = True
        
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
                deleteIfPresent(preproc, "watershed_source")
                deleteIfPresent(preproc, "invert_watershed_source")
                deleteIfPresent(preproc, "graph")
                
                preproc.create_dataset("sigma",data= opPre.initialSigma)
                preproc.create_dataset("filter",data= opPre.initialFilter)
                ws_source = str(opPre.WatershedSource.value)
                assert isinstance( ws_source, str ), "WatershedSource was {}, but it should be a string.".format( ws_source )
                preproc.create_dataset("watershed_source", data=ws_source)                 
                preproc.create_dataset("invert_watershed_source", data=opPre.InvertWatershedSource.value)
                
                preprocgraph = getOrCreateGroup(preproc, "graph")
                mst.saveH5G(preprocgraph)
            
            opPre._unsavedData = False
            
    def _deserializeFromHdf5(self, topGroup, groupVersion, hdf5File, projectFilePath,headless = False):
        
        assert "sigma" in topGroup.keys()
        assert "filter" in topGroup.keys()
        
        sigma = topGroup["sigma"].value
        sfilter = topGroup["filter"].value
        try:
            watershed_source = str(topGroup["watershed_source"].value)
            invert_watershed_source = bool(topGroup["invert_watershed_source"].value)
        except KeyError:
            watershed_source = None
            invert_watershed_source = False
        
        if "graph" in topGroup.keys():
            graphgroup = topGroup["graph"]
        else:
            assert "graphfile" in topGroup.keys()
            #feature: load preprocessed graph from file
            filePath = topGroup["graphfile"].value
            if not os.path.exists(filePath):
                if headless:
                    raise RuntimeError("Could not find data at " + filePath)
                filePath = self.repairFile(filePath,"*.h5")
            graphgroup = h5py.File(filePath,"r")["graph"]
            
        for opPre in self._o.innerOperators:
            
            opPre.initialSigma = sigma
            opPre.Sigma.setValue(sigma)
            if watershed_source:
                opPre.WatershedSource.setValue( watershed_source )
                opPre.InvertWatershedSource.setValue( invert_watershed_source )
            opPre.initialFilter = sfilter
            opPre.Filter.setValue(sfilter)
            
            mst = MSTSegmentor.loadH5G(graphgroup)
            opPre._prepData = numpy.array([mst])
        
            
            opPre._dirty = False
            opPre.applet.writeprotected = True
            
            opPre.PreprocessedData.setDirty()
            opPre.enableDownstream(True)
           
    def isDirty(self):
        for opPre in self._o.innerOperators:            
            if opPre._unsavedData:
                return True
        return False
    
    #this is present only for the serializer AppletInterface
    def unload(self):
        pass
    
