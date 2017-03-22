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
#           http://ilastik.org/license.html
###############################################################################
import os
import numpy as np
import vigra

from lazyflow.graph import Graph
from lazyflow.operators import OpLabelVolume
from lazyflow.utility import Timer
from lazyflow.operators.opReorderAxes import OpReorderAxes
from lazyflow.operators.opBlockedArrayCache import OpBlockedArrayCache 
from lazyflow.request import Request, RequestPool
from lazyflow.request.threadPool import ThreadPool

from functools import partial

from ilastik.applets.objectExtraction.opObjectExtraction import OpAdaptTimeListRoi, OpRegionFeatures, OpObjectExtraction


from ilastik.plugins import pluginManager
from ilastik.applets.dataSelection.opDataSelection import OpDataSelection, DatasetInfo

from lazyflow.operators.ioOperators import OpStreamingHdf5Reader, OpStreamingUfmfReader
import lazyflow

from lazyflow.utility import RoiRequestBatch
from lazyflow.roi import roiFromShape
from lazyflow.graph import Operator, InputSlot, OutputSlot

from lazyflow.utility import Memory

import h5py

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning) 

import logging
logger = logging.getLogger(__name__)

NAME = "Standard Object Features"

FEATURES = {
    NAME : {
        "Count" : {},
        "RegionCenter" : {},
        "Coord<Principal<Kurtosis>>" : {},
        "Coord<Minimum>" : {},
        "Coord<Maximum>" : {},
    }
}

# Cleanup functions (used in vigra_objfeats.py)
def cleanup_key(k):
    return k.replace(' ', '')

def cleanup_value(val, nObjects, isGlobal):
    """ensure that the value is a numpy array with the correct shape."""
    val = np.asarray(val)

    if val.ndim == 0 or isGlobal:
        # repeat the global values for all the objects 
        scalar = val.reshape((1,))[0]
        val = np.zeros((nObjects, 1), dtype=val.dtype)
        val[:, 0] = scalar
    
    if val.ndim == 1:
        val = val.reshape(-1, 1)
   
    if val.ndim > 2:
        val = val.reshape(val.shape[0], -1)

    assert val.shape[0] == nObjects
    # remove background
    val = val[1:]
    return val

def cleanup(d, nObjects, features):
    result = dict((cleanup_key(k), cleanup_value(v, nObjects, "Global" in k)) for k, v in d.iteritems())
    newkeys = set(result.keys()) & set(features)
    return dict((k, result[k]) for k in newkeys)

def binaryImage():
    frameNum = 500
    
    img = np.zeros((frameNum, 100, 100, 1), dtype=np.float32)
    
    for frame in range(frameNum):
        img[frame,  0:10,  0:10, 0] = 1
        img[frame, 20:30, 20:30, 0] = 1
        img[frame, 40:45, 40:45, 0] = 1
        img[frame, 60:80, 60:80, 0] = 1

    img = img.view(vigra.VigraArray)
    img.axistags = vigra.defaultAxistags('txyc')

    return img

def rawImage():
    frameNum = 500
    
    img = np.zeros((frameNum, 100, 100, 1), dtype=np.float32)
    
    for frame in range(frameNum):
        img[frame,  0:10,  0:10, 0] = 200
        img[frame, 20:30, 20:30, 0] = 100
        img[frame, 40:45, 40:45, 0] = 150
        img[frame, 60:80, 60:80, 0] = 75


    img = img.view(vigra.VigraArray)
    img.axistags = vigra.defaultAxistags('txyc')

    return img

# Simple object extraction operator (No overhead)
class OpObjectFeaturesSimplified(Operator):
    RawVol = InputSlot()
    BinaryVol = InputSlot()
    Features = OutputSlot()
        
    def setupOutputs(self):
        taggedOutputShape = self.BinaryVol.meta.getTaggedShape()
        self.Features.meta.shape = (taggedOutputShape['t'],)
        self.Features.meta.axistags = vigra.defaultAxistags('t')
        self.Features.meta.dtype = object # Storing feature dicts
        
    def execute(self, slot, subindex, roi, result):
        t_ind = self.RawVol.meta.axistags.index('t')
        
        for res_t_ind, t in enumerate(xrange(roi.start[t_ind], roi.stop[t_ind])):
            result[res_t_ind] = self._computeFeatures(t_ind, t)
    
    def propagateDirty(self, slot, subindex):
        pass # Nothing to do...
    
    def _computeFeatures(self, t_ind, t):
        roi = [slice(None) for i in range(len(self.RawVol.meta.shape))]
        roi[t_ind] = slice(t, t+1)
        roi = tuple(roi)  
        
        rawVol = self.RawVol(roi).wait()
        binaryVol = self.BinaryVol(roi).wait() 
        
        # Connected components
        labelVol = vigra.analysis.labelImageWithBackground(binaryVol.squeeze(), background_value=int(0))
        
        # Compute features
        features = ['Count', 'Coord<Minimum>', 'RegionCenter', 'Coord<Principal<Kurtosis>>', 'Coord<Maximum>'] 
        res = vigra.analysis.extractRegionFeatures(rawVol.squeeze().astype(np.float32), labelVol.squeeze().astype(np.uint32), features, ignoreLabel=0)
    
        # Cleanup results (as done in vigra_objfeats)
        local_features = [x for x in features if "Global<" not in x]
        nobj = res[local_features[0]].shape[0]   
        return cleanup(res, nobj, features)     


# Object extraction running time comparison
class ObjectExtractionTimeComparison(object):
    def __init__(self):
        # Set memory and number of threads here
        #lazyflow.request.Request.reset_thread_pool(2)
        #Memory.setAvailableRam(500*1024**2)
        
        binary_img = binaryImage()
        raw_img = rawImage()
        
        g = Graph()     
        
        # Reorder axis operators 
        self.op5Raw = OpReorderAxes(graph=g)
        self.op5Raw.AxisOrder.setValue("txyzc")
        #self.op5Raw.Input.connect(self.opReaderRaw.OutputImage)#self.opReaderRaw.OutputImage)
        self.op5Raw.Input.setValue(raw_img)
        
        self.op5Binary = OpReorderAxes(graph=g)
        self.op5Binary.AxisOrder.setValue("txyzc")
        #self.op5Binary.Input.connect(self.opReaderBinary.OutputImage)
        self.op5Binary.Input.setValue(binary_img)
        
        # Cache operators
        self.opCacheRaw = OpBlockedArrayCache(graph=g)
        self.opCacheRaw.Input.connect(self.op5Raw.Output)
        self.opCacheRaw.BlockShape.setValue(  (1,)+self.op5Raw.Output.meta.shape[1:] )
         
        self.opCacheBinary = OpBlockedArrayCache(graph=g)
        self.opCacheBinary.Input.connect(self.op5Binary.Output)        
        self.opCacheBinary.BlockShape.setValue(  (1,)+self.op5Binary.Output.meta.shape[1:] )
        
        # Label volume operator   
        self.opLabel = OpLabelVolume(graph=g)
        self.opLabel.Input.connect(self.op5Binary.Output)
        #self.opLabel.Input.connect(self.opCacheBinary.Output)
        
        # Object extraction
        self.opObjectExtraction = OpObjectExtraction(graph=g)
        self.opObjectExtraction.RawImage.connect(self.op5Raw.Output)
        self.opObjectExtraction.BinaryImage.connect(self.op5Binary.Output) 
        self.opObjectExtraction.Features.setValue(FEATURES)
           
         
        # Simplified object features operator (No overhead)
        self.opObjectFeaturesSimp = OpObjectFeaturesSimplified(graph=g)
        self.opObjectFeaturesSimp.RawVol.connect(self.opCacheRaw.Output) 
        self.opObjectFeaturesSimp.BinaryVol.connect(self.opCacheBinary.Output) 

    def run(self):
        
#         # Load caches beforehand (To remove overhead of reading frames)
#         with Timer() as timerCaches:    
#             rawVol = self.opCacheRaw.Output([]).wait()
#             binaryVol = self.opCacheBinary.Output([]).wait()
#              
#         print "Caches took {} secs".format(timerCaches.seconds())
#          
#         del rawVol
#         del binaryVol
    
        # Profile object extraction simplified
        print "\nStarting object extraction simplified (single-thread, without cache)"
             
        with Timer() as timerObjectFeaturesSimp:
            featsObjectFeaturesSimp = self.opObjectFeaturesSimp.Features([]).wait()
                 
        print "Simplified object extraction took: {} seconds".format(timerObjectFeaturesSimp.seconds())     
        
        # Profile object extraction optimized
        print "\nStarting object extraction (multi-thread, without cache)"
          
        with Timer() as timerObjectExtraction:
            featsObjectExtraction = self.opObjectExtraction.RegionFeatures([]).wait()
              
        print "Object extraction took: {} seconds".format(timerObjectExtraction.seconds()) 
    
        # Profile for basic multi-threaded feature computation 
        # just a multi-threaded loop that labels volumes and extract object features directly (No operators, no plugin system, no overhead, just a loop)
        featsBasicFeatureComp = dict.fromkeys( range(self.op5Raw.Output.meta.shape[0]), None)
            
        print "\nStarting basic multi-threaded feature computation"
        pool = RequestPool()    
        for t in range(0, self.op5Raw.Output.meta.shape[0], 1):
            pool.add( Request( partial(self._computeObjectFeatures, t, featsBasicFeatureComp) ) )
                 
        with Timer() as timerBasicFeatureComp:
            pool.wait()
                 
        print "Basic multi-threaded feature extraction took: {} seconds".format( timerBasicFeatureComp.seconds() )                 

    
    # Compute object features for single frame        
    def _computeObjectFeatures(self, t, result):
        roi = [slice(None) for i in range(len(self.op5Raw.Output.meta.shape))]
        roi[0] = slice(t, t+1)
        roi = tuple(roi)

#         rawVol = self.opCacheRaw.Output(roi).wait()
#         binaryVol = self.opCacheBinary.Output(roi).wait()

        rawVol = self.op5Raw.Output(roi).wait()
        binaryVol = self.op5Binary.Output(roi).wait()
                            
        features = ['Count', 'Coord<Minimum>', 'RegionCenter', 'Coord<Principal<Kurtosis>>', 'Coord<Maximum>'] 
        
        for i in range(t,t+1):
            labelVol = vigra.analysis.labelImageWithBackground(binaryVol[i-t].squeeze(), background_value=int(0))
            res = vigra.analysis.extractRegionFeatures(rawVol[i-t].squeeze().astype(np.float32), labelVol.squeeze().astype(np.uint32), features, ignoreLabel=0)
            
            # Cleanup results (as done in vigra_objfeats)
            local_features = [x for x in features if "Global<" not in x]
            nobj = res[local_features[0]].shape[0]   
            result[i] = cleanup(res, nobj, features)


if __name__ == '__main__':
    
    # Run object extraction comparison
    objectExtractionTimeComparison = ObjectExtractionTimeComparison()
    objectExtractionTimeComparison.run()

