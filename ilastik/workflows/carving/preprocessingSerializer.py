from __future__ import absolute_import
###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
#		   http://ilastik.org/license.html
###############################################################################
from ilastik.applets.base.appletSerializer import AppletSerializer, getOrCreateGroup, deleteIfPresent
import h5py
import numpy
import os

from .watershed_segmentor import WatershedSegmentor

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
                deleteIfPresent(preproc, "watershed_source")
                deleteIfPresent(preproc, "invert_watershed_source")
                deleteIfPresent(preproc, "graph")
                
                preproc.create_dataset("sigma",data= opPre.initialSigma)
                preproc.create_dataset("filter",data= opPre.initialFilter)
                ws_source = str(opPre.WatershedSource.value)
                assert isinstance( ws_source, str ), "WatershedSource was {}, but it should be a string.".format( ws_source )
                preproc.create_dataset("watershed_source", data=ws_source.encode('utf-8'))
                preproc.create_dataset("invert_watershed_source", data=opPre.InvertWatershedSource.value)
                
                preprocgraph = getOrCreateGroup(preproc, "graph")
                mst.saveH5G(preprocgraph)
            
            opPre._unsavedData = False
            
    def _deserializeFromHdf5(self, topGroup, groupVersion, hdf5File, projectFilePath, headless=False):
        
        assert "sigma" in list(topGroup.keys())
        assert "filter" in list(topGroup.keys())
        
        sigma = topGroup["sigma"].value
        sfilter = topGroup["filter"].value
        try:
            watershed_source = str(topGroup["watershed_source"].value.decode('utf-8'))
            invert_watershed_source = bool(topGroup["invert_watershed_source"].value)
        except KeyError:
            watershed_source = None
            invert_watershed_source = False
        
        if "graph" in list(topGroup.keys()):
            graphgroup = topGroup["graph"]
        else:
            assert "graphfile" in list(topGroup.keys())
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
            
            mst = WatershedSegmentor(h5file=graphgroup)
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
    
