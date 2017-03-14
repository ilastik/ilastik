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
#Python
import sys
import logging

#SciPy
import numpy
import h5py

#lazyflow
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.roi import roiToSlice
from lazyflow.operators import OpSlicedBlockedArrayCache, OpMultiArraySlicer2
from lazyflow.operators import OpPixelFeaturesPresmoothed as OpPixelFeaturesPresmoothed_Original
from lazyflow.operators import OpPixelFeaturesInterpPresmoothed as OpPixelFeaturesPresmoothed_Interpolated
from lazyflow.operators.imgFilterOperators import OpPixelFeaturesPresmoothed as OpPixelFeaturesPresmoothed_Refactored
from lazyflow.operators import OpReorderAxes, OperatorWrapper

from ilastik.applets.base.applet import DatasetConstraintError

logger = logging.getLogger(__name__)

# Constants
ScalesList = [0.3, 0.7, 1.0, 1.6, 3.5, 5.0, 10.0]

# Map feature groups to lists of feature IDs
FeatureGroups = [ ( "Color/Intensity",   [ "GaussianSmoothing" ] ),
                  ( "Edge",    [ "LaplacianOfGaussian", "GaussianGradientMagnitude", "DifferenceOfGaussians" ] ),
                  ( "Texture", [ "StructureTensorEigenvalues", "HessianOfGaussianEigenvalues" ] ) ]

# Map feature IDs to feature names
FeatureNames = { 'GaussianSmoothing' : 'Gaussian Smoothing',
                 'LaplacianOfGaussian' : "Laplacian of Gaussian",
                 'GaussianGradientMagnitude' : "Gaussian Gradient Magnitude",
                 'DifferenceOfGaussians' : "Difference of Gaussians",
                 'StructureTensorEigenvalues' : "Structure Tensor Eigenvalues",
                 'HessianOfGaussianEigenvalues' : "Hessian of Gaussian Eigenvalues" }

def getFeatureIdOrder():
    featureIrdOrder = []
    for group, featureIds in FeatureGroups:
        featureIrdOrder += featureIds
    return featureIrdOrder

class OpFeatureSelectionNoCache(Operator):
    """
    The top-level operator for the feature selection applet for headless workflows.
    """
    name = "OpFeatureSelection"
    category = "Top-level"

    ScalesList = ScalesList
    FeatureGroups = FeatureGroups
    FeatureNames = FeatureNames

    MinimalFeatures = numpy.zeros( (len(FeatureNames), len(ScalesList)), dtype=bool )
    MinimalFeatures[0,0] = True

    # Multiple input images
    InputImage = InputSlot()

    # The following input slots are applied uniformly to all input images
    Scales = InputSlot( value=ScalesList ) # The list of possible scales to use when computing features
    FeatureIds = InputSlot( value=getFeatureIdOrder() ) # The list of features to compute
    SelectionMatrix = InputSlot( value=MinimalFeatures ) # A matrix of bools indicating which features to output.
                                                       # The matrix rows correspond to feature types in the order specified by the FeatureIds input.
                                                       #  (See OpPixelFeaturesPresmoothed for the available feature types.)
                                                       # The matrix columns correspond to the scales provided in the Scales input,
                                                       #  which requires that the number of matrix columns must match len(Scales.value)

    FeatureListFilename = InputSlot(stype="str", optional=True)
    
    # Features are presented in the channels of the output image
    # Output can be optionally accessed via an internal cache.
    # (Training a classifier benefits from caching, but predicting with an existing classifier does not.)
    OutputImage = OutputSlot()

    FeatureLayers = OutputSlot(level=1) # For the GUI, we also provide each feature as a separate slot in this multislot

    # For ease of development and testing, the underlying feature computation implementation 
    #  can be switched via a constructor argument.  These are the possible choices.
    FilterImplementations = ['Original', 'Refactored', 'Interpolated']
    
    def __init__(self, filter_implementation, *args, **kwargs):
        super(OpFeatureSelectionNoCache, self).__init__(*args, **kwargs)

        # Create the operator that actually generates the features
        if filter_implementation == 'Original':
            self.opPixelFeatures = OpPixelFeaturesPresmoothed_Original(parent=self)
            logger.debug("Using ORIGINAL filters")
        elif filter_implementation == 'Refactored':
            self.opPixelFeatures = OpPixelFeaturesPresmoothed_Refactored(parent=self)
        elif filter_implementation == 'Interpolated':
            self.opPixelFeatures = OpPixelFeaturesPresmoothed_Interpolated(parent=self)
            self.opPixelFeatures.InterpolationScaleZ.setValue(2)
            logger.debug("Using INTERPOLATED filters")
        else:
            raise RuntimeError("Unknown filter implementation option: {}".format( filter_implementation ))

        # Connect our internal operators to our external inputs 
        self.opPixelFeatures.Scales.connect( self.Scales )
        self.opPixelFeatures.FeatureIds.connect( self.FeatureIds )
        self.opReorderIn = OpReorderAxes(parent=self)
        self.opReorderIn.Input.connect(self.InputImage)
        self.opPixelFeatures.Input.connect(self.opReorderIn.Output)
        self.opReorderOut = OpReorderAxes(parent=self)
        self.opReorderOut.Input.connect(self.opPixelFeatures.Output)
        self.opReorderLayers = OperatorWrapper(OpReorderAxes, parent=self,
                                               broadcastingSlotNames=["AxisOrder"])
        self.opReorderLayers.Input.connect(self.opPixelFeatures.Features)

        # We don't connect SelectionMatrix here because we want to 
        #  check it for errors (See setupOutputs)
        # self.opPixelFeatures.SelectionMatrix.connect( self.SelectionMatrix )

        self.WINDOW_SIZE = self.opPixelFeatures.WINDOW_SIZE

    def setupOutputs(self):
        # drop non-channel singleton axes
        allAxes = 'txyzc'
        ts = self.InputImage.meta.getTaggedShape()
        oldAxes = "".join(ts.keys())
        newAxes = "".join([a for a in allAxes
                           if a in ts and ts[a] > 1 or a == 'c'])
        self.opReorderIn.AxisOrder.setValue(newAxes)
        self.opReorderOut.AxisOrder.setValue(oldAxes)
        self.opReorderLayers.AxisOrder.setValue(oldAxes)
        
        # Get features from external file
        if self.FeatureListFilename.ready() and len(self.FeatureListFilename.value) > 0:
                  
            self.OutputImage.disconnect()
            self.FeatureLayers.disconnect()
            
            axistags = self.InputImage.meta.axistags
                
            with h5py.File(self.FeatureListFilename.value,'r') as f:
                dset_names = []
                f.visit(dset_names.append)
                if len(dset_names) != 1:
                    sys.stderr.write("Input external features HDF5 file should have exactly 1 dataset.\n")
                    sys.exit(1)                
                
                dset = f[dset_names[0]]
                chnum = dset.shape[-1]
                shape = dset.shape
                dtype = dset.dtype.type
            
            # Set the metadata for FeatureLayers. Unlike OutputImage and CachedOutputImage, 
            # FeatureLayers has one slot per channel and therefore the channel dimension must be 1.
            self.FeatureLayers.resize(chnum)
            for i in range(chnum):
                self.FeatureLayers[i].meta.shape    = shape[:-1]+(1,)
                self.FeatureLayers[i].meta.dtype    = dtype
                self.FeatureLayers[i].meta.axistags = axistags 
                self.FeatureLayers[i].meta.display_mode = 'default' 
                self.FeatureLayers[i].meta.description = "feature_channel_"+str(i)
            
            self.OutputImage.meta.shape    = shape
            self.OutputImage.meta.dtype    = dtype 
            self.OutputImage.meta.axistags = axistags
            
        else:
            # Set the new selection matrix and check if it creates an error.
            selections = self.SelectionMatrix.value
            self.opPixelFeatures.Matrix.setValue( selections )
            invalid_scales = self.opPixelFeatures.getInvalidScales()
            if invalid_scales:
                msg = "Some of your selected feature scales are too large for your dataset.\n"\
                      "Choose smaller scales (sigma) or use a larger dataset.\n"\
                      "The invalid scales are: {}".format( invalid_scales )                      
                raise DatasetConstraintError( "Feature Selection", msg )
            
            # Connect our external outputs to our internal operators
            self.OutputImage.connect( self.opReorderOut.Output )
            self.FeatureLayers.connect( self.opReorderLayers.Output )

    def propagateDirty(self, slot, subindex, roi):
        # Output slots are directly connected to internal operators
        pass
    
    def execute(self, slot, subindex, rroi, result):
        if len(self.FeatureListFilename.value) == 0:
            return
        
        # Set the channel corresponding to the slot(subindex) of the feature layers
        if slot == self.FeatureLayers:
            rroi.start[-1] = subindex[0]
            rroi.stop[-1] = subindex[0] + 1 
            
        key = roiToSlice(rroi.start, rroi.stop)
        
        # Read features from external file
        with h5py.File(self.FeatureListFilename.value, 'r') as f:
            dset_names = []
            f.visit(dset_names.append)
            
            if len(dset_names) != 1:
                sys.stderr.write("Input external features HDF5 file should have exactly 1 dataset.")
                return 
                
            dset = f[dset_names[0]]              
            result[...] = dset[key]
                        
        return result
    

class OpFeatureSelection( OpFeatureSelectionNoCache ):
    """
    This is the top-level operator of the feature selection applet when used in a GUI.
    It provides an extra output for cached data.
    """
    BypassCache = InputSlot(value=False)
    CachedOutputImage = OutputSlot()

    def __init__(self, *args, **kwargs):
        super( OpFeatureSelection, self).__init__( *args, **kwargs )

        # Create the cache
        self.opPixelFeatureCache = OpSlicedBlockedArrayCache(parent=self)
        self.opPixelFeatureCache.name = "opPixelFeatureCache"
        self.opPixelFeatureCache.BypassModeEnabled.connect( self.BypassCache )

        # Connect the cache to the feature output
        self.opPixelFeatureCache.Input.connect(self.OutputImage)
        self.opPixelFeatureCache.fixAtCurrent.setValue(False)

    def change_feature_cache_size(self):
        curr_size = self.opPixelFeatureCache.BlockShape.value
        a = [list(i) for i in curr_size]
        a[2][3] = 1
        c = [tuple(i) for i in a]
        c = tuple(c)
        self.opPixelFeatureCache.BlockShape.setValue(c)

    def setupOutputs(self):
        super( OpFeatureSelection, self ).setupOutputs()

        if self.FeatureListFilename.ready() and len(self.FeatureListFilename.value) > 0:
            self.CachedOutputImage.disconnect()            
            self.CachedOutputImage.meta.assignFrom(self.OutputImage.meta)
        
        else:
            # We choose block shapes that have only 1 channel because the channels may be 
            #  coming from different features (e.g different filters) and probably shouldn't be cached together.
            blockDimsX = { 't' : (1,1),
                           'z' : (256,256),
                           'y' : (256,256),
                           'x' : (32,32),
                           'c' : (1000,1000) }  # Overestimate number of feature channels: 
                                                # Cache block dimensions will be clipped to the size of the actual feature image
    
            blockDimsY = { 't' : (1,1),
                           'z' : (256,256),
                           'y' : (32,32),
                           'x' : (256,256),
                           'c' : (1000,1000) }
    
            blockDimsZ = { 't' : (1,1),
                           'z' : (32,32),
                           'y' : (256,256),
                           'x' : (256,256),
                           'c' : (1000,1000) }
            
            axisOrder = [ tag.key for tag in self.InputImage.meta.axistags ]
            blockShapeX = tuple( blockDimsX[k][1] for k in axisOrder )
            blockShapeY = tuple( blockDimsY[k][1] for k in axisOrder )
            blockShapeZ = tuple( blockDimsZ[k][1] for k in axisOrder )
    
            # Configure the cache        
            self.opPixelFeatureCache.BlockShape.setValue( (blockShapeX, blockShapeY, blockShapeZ) )

            # Connect external output to internal output
            self.CachedOutputImage.connect( self.opPixelFeatureCache.Output )

