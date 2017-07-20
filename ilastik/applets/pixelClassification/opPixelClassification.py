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
from builtins import range
import copy
from functools import partial

#SciPy
import numpy
#import IPython
import vigra

#lazyflow
from lazyflow.roi import determineBlockShape
from lazyflow.graph import Operator, InputSlot, OutputSlot, OperatorWrapper
from lazyflow.operators import OpValueCache, OpTrainClassifierBlocked, OpClassifierPredict,\
                               OpSlicedBlockedArrayCache, OpMultiArraySlicer2, \
                               OpPixelOperator, OpMaxChannelIndicatorOperator, OpCompressedUserLabelArray, OpFeatureMatrixCache
import ilastik_feature_selection
import numpy as np

from lazyflow.classifiers import ParallelVigraRfLazyflowClassifierFactory

#ilastik
from ilastik.applets.base.applet import DatasetConstraintError
from ilastik.utility.operatorSubView import OperatorSubView
from ilastik.utility import OpMultiLaneWrapper

#from PyQt5.QtCore import pyqtRemoveInputHook, pyqtRestoreInputHook

class OpPixelClassification( Operator ):
    """
    Top-level operator for pixel classification
    """
    name="OpPixelClassification"
    category = "Top-level"
    
    # Graph inputs
    
    InputImages = InputSlot(level=1) # Original input data.  Used for display only.
    PredictionMasks = InputSlot(level=1, optional=True) # Routed to OpClassifierPredict.PredictionMask.  See there for details.

    LabelInputs = InputSlot(optional = True, level=1) # Input for providing label data from an external source
    
    FeatureImages = InputSlot(level=1) # Computed feature images (each channel is a different feature)
    CachedFeatureImages = InputSlot(level=1) # Cached feature data.

    FreezePredictions = InputSlot(stype='bool')
    ClassifierFactory = InputSlot(value=ParallelVigraRfLazyflowClassifierFactory(100))

    PredictionsFromDisk = InputSlot(optional=True, level=1)

    PredictionProbabilities = OutputSlot(level=1) # Classification predictions (via feature cache for interactive speed)
    PredictionProbabilitiesUint8 = OutputSlot(level=1) # Same thing, but converted to uint8 first

    PredictionProbabilityChannels = OutputSlot(level=2) # Classification predictions, enumerated by channel
    SegmentationChannels = OutputSlot(level=2) # Binary image of the final selections.
    
    LabelImages = OutputSlot(level=1) # Labels from the user
    NonzeroLabelBlocks = OutputSlot(level=1) # A list if slices that contain non-zero label values
    Classifier = OutputSlot() # We provide the classifier as an external output for other applets to use

    CachedPredictionProbabilities = OutputSlot(level=1) # Classification predictions (via feature cache AND prediction cache)

    HeadlessPredictionProbabilities = OutputSlot(level=1) # Classification predictions ( via no image caches (except for the classifier itself )
    HeadlessUint8PredictionProbabilities = OutputSlot(level=1) # Same as above, but 0-255 uint8 instead of 0.0-1.0 float32
    HeadlessUncertaintyEstimate = OutputSlot(level=1) # Same as uncertaintly estimate, but does not rely on cached data.

    UncertaintyEstimate = OutputSlot(level=1)
    
    SimpleSegmentation = OutputSlot(level=1) # For debug, for now

    # GUI-only (not part of the pipeline, but saved to the project)
    LabelNames = OutputSlot()
    LabelColors = OutputSlot()
    PmapColors = OutputSlot()
    Bookmarks = OutputSlot(level=1)

    NumClasses = OutputSlot()

    def setupOutputs(self):
        self.LabelNames.meta.dtype = object
        self.LabelNames.meta.shape = (1,)
        self.LabelColors.meta.dtype = object
        self.LabelColors.meta.shape = (1,)
        self.PmapColors.meta.dtype = object
        self.PmapColors.meta.shape = (1,)

    def __init__( self, *args, **kwargs ):
        """
        Instantiate all internal operators and connect them together.
        """
        super(OpPixelClassification, self).__init__(*args, **kwargs)
        
        # Default values for some input slots
        self.FreezePredictions.setValue(True)
        self.LabelNames.setValue( [] )
        self.LabelColors.setValue( [] )
        self.PmapColors.setValue( [] )

        # SPECIAL connection: The LabelInputs slot doesn't get it's data  
        #  from the InputImages slot, but it's shape must match.
        self.LabelInputs.connect( self.InputImages )

        # Hook up Labeling Pipeline
        self.opLabelPipeline = OpMultiLaneWrapper( OpLabelPipeline, parent=self, broadcastingSlotNames=['DeleteLabel'] )
        self.opLabelPipeline.RawImage.connect( self.InputImages )
        self.opLabelPipeline.LabelInput.connect( self.LabelInputs )
        self.opLabelPipeline.DeleteLabel.setValue( -1 )
        self.LabelImages.connect( self.opLabelPipeline.Output )
        self.NonzeroLabelBlocks.connect( self.opLabelPipeline.nonzeroBlocks )

        # Hook up the Training operator
        self.opTrain = OpTrainClassifierBlocked( parent=self )
        self.opTrain.ClassifierFactory.connect( self.ClassifierFactory )
        self.opTrain.Labels.connect( self.opLabelPipeline.Output )
        self.opTrain.Images.connect( self.FeatureImages )
        self.opTrain.nonzeroLabelBlocks.connect( self.opLabelPipeline.nonzeroBlocks )

        # Hook up the Classifier Cache
        # The classifier is cached here to allow serializers to force in
        #   a pre-calculated classifier (loaded from disk)
        self.classifier_cache = OpValueCache( parent=self )
        self.classifier_cache.name = "OpPixelClassification.classifier_cache"
        self.classifier_cache.inputs["Input"].connect(self.opTrain.outputs['Classifier'])
        self.classifier_cache.inputs["fixAtCurrent"].connect( self.FreezePredictions )
        self.Classifier.connect( self.classifier_cache.Output )

        # Hook up the prediction pipeline inputs
        self.opPredictionPipeline = OpMultiLaneWrapper( OpPredictionPipeline, parent=self )
        self.opPredictionPipeline.FeatureImages.connect( self.FeatureImages )
        self.opPredictionPipeline.CachedFeatureImages.connect( self.CachedFeatureImages )
        self.opPredictionPipeline.Classifier.connect( self.classifier_cache.Output )
        self.opPredictionPipeline.FreezePredictions.connect( self.FreezePredictions )
        self.opPredictionPipeline.PredictionsFromDisk.connect( self.PredictionsFromDisk )
        self.opPredictionPipeline.PredictionMask.connect( self.PredictionMasks )

        # Feature Selection Stuff
        self.opFeatureMatrixCaches = OpMultiLaneWrapper(OpFeatureMatrixCache, parent=self)
        self.opFeatureMatrixCaches.LabelImage.connect(self.opLabelPipeline.Output)
        self.opFeatureMatrixCaches.FeatureImage.connect(self.FeatureImages)
        self.opFeatureMatrixCaches.LabelImage.setDirty()  # do I still need this?

        
        def _updateNumClasses(*args):
            """
            When the number of labels changes, we MUST make sure that the prediction image changes its shape (the number of channels).
            Since setupOutputs is not called for mere dirty notifications, but is called in response to setValue(),
            we use this function to call setValue().
            """
            numClasses = len(self.LabelNames.value)
            self.opTrain.MaxLabel.setValue( numClasses )
            self.opPredictionPipeline.NumClasses.setValue( numClasses )
            self.NumClasses.setValue( numClasses )
        self.LabelNames.notifyDirty( _updateNumClasses )

        # Prediction pipeline outputs -> Top-level outputs
        self.PredictionProbabilities.connect( self.opPredictionPipeline.PredictionProbabilities )
        self.PredictionProbabilitiesUint8.connect( self.opPredictionPipeline.PredictionProbabilitiesUint8 )
        self.CachedPredictionProbabilities.connect( self.opPredictionPipeline.CachedPredictionProbabilities )
        self.HeadlessPredictionProbabilities.connect( self.opPredictionPipeline.HeadlessPredictionProbabilities )
        self.HeadlessUint8PredictionProbabilities.connect( self.opPredictionPipeline.HeadlessUint8PredictionProbabilities )
        self.PredictionProbabilityChannels.connect( self.opPredictionPipeline.PredictionProbabilityChannels )
        self.SegmentationChannels.connect( self.opPredictionPipeline.SegmentationChannels )
        self.UncertaintyEstimate.connect( self.opPredictionPipeline.UncertaintyEstimate )
        self.SimpleSegmentation.connect( self.opPredictionPipeline.SimpleSegmentation )
        self.HeadlessUncertaintyEstimate.connect( self.opPredictionPipeline.HeadlessUncertaintyEstimate )

        def inputResizeHandler( slot, oldsize, newsize ):
            if ( newsize == 0 ):
                self.Bookmarks.resize(0)
                self.LabelImages.resize(0)
                self.NonzeroLabelBlocks.resize(0)
                self.PredictionProbabilities.resize(0)
                self.CachedPredictionProbabilities.resize(0)
        self.InputImages.notifyResized( inputResizeHandler )

        # Debug assertions: Check to make sure the non-wrapped operators stayed that way.
        assert self.opTrain.Images.operator == self.opTrain

        def handleNewInputImage( multislot, index, *args ):
            def handleInputReady(slot):
                self._checkConstraints( index )
                self.setupCaches( multislot.index(slot) )
            multislot[index].notifyReady(handleInputReady)
                
        self.InputImages.notifyInserted( handleNewInputImage )

        # If any feature image changes shape, we need to verify that the 
        #  channels are consistent with the currently cached classifier
        # Otherwise, delete the currently cached classifier.
        def handleNewFeatureImage( multislot, index, *args ):
            def handleFeatureImageReady(slot):
                def handleFeatureMetaChanged(slot):
                    if ( self.classifier_cache.fixAtCurrent.value and
                         self.classifier_cache.Output.ready() and 
                         slot.meta.shape is not None ):
                        classifier = self.classifier_cache.Output.value
                        channel_names = slot.meta.channel_names
                        if classifier and classifier.feature_names != channel_names:
                            self.classifier_cache.resetValue()
                slot.notifyMetaChanged(handleFeatureMetaChanged)
            multislot[index].notifyReady(handleFeatureImageReady)
                
        self.FeatureImages.notifyInserted( handleNewFeatureImage )

        def handleNewMaskImage( multislot, index, *args ):
            def handleInputReady(slot):
                self._checkConstraints( index )
            multislot[index].notifyReady(handleInputReady)        
        self.PredictionMasks.notifyInserted( handleNewMaskImage )

        # All input multi-slots should be kept in sync
        # Output multi-slots will auto-sync via the graph
        multiInputs = [s for s in list(self.inputs.values()) if s.level >= 1]
        for s1 in multiInputs:
            for s2 in multiInputs:
                if s1 != s2:
                    def insertSlot( a, b, position, finalsize ):
                        a.insertSlot(position, finalsize)
                    s1.notifyInserted( partial(insertSlot, s2 ) )
                    
                    def removeSlot( a, b, position, finalsize ):
                        a.removeSlot(position, finalsize)
                    s1.notifyRemoved( partial(removeSlot, s2 ) )

    def setupCaches(self, imageIndex):
        numImages = len(self.InputImages)
        inputSlot = self.InputImages[imageIndex]
#        # Can't setup if all inputs haven't been set yet.
#        if numImages != len(self.FeatureImages) or \
#           numImages != len(self.CachedFeatureImages):
#            return
#        
#        self.LabelImages.resize(numImages)
        self.LabelInputs.resize(numImages)

        # Special case: We have to set up the shape of our label *input* according to our image input shape
        shapeList = list(self.InputImages[imageIndex].meta.shape)
        try:
            channelIndex = self.InputImages[imageIndex].meta.axistags.index('c')
            shapeList[channelIndex] = 1
        except:
            pass
        self.LabelInputs[imageIndex].meta.shape = tuple(shapeList)
        self.LabelInputs[imageIndex].meta.axistags = inputSlot.meta.axistags

    def _checkConstraints(self, laneIndex):
        """
        Ensure that all input images have the same number of channels.
        """
        if not self.InputImages[laneIndex].ready():
            return

        thisLaneTaggedShape = self.InputImages[laneIndex].meta.getTaggedShape()

        # Find a different lane and use it for comparison
        validShape = thisLaneTaggedShape
        for i, slot in enumerate(self.InputImages):
            if slot.ready() and i != laneIndex:
                validShape = slot.meta.getTaggedShape()
                break

        if 't' in thisLaneTaggedShape:
            del thisLaneTaggedShape['t']
        if 't' in validShape:
            del validShape['t']

        if validShape['c'] != thisLaneTaggedShape['c']:
            raise DatasetConstraintError(
                 "Pixel Classification",
                 "All input images must have the same number of channels.  "\
                 "Your new image has {} channel(s), but your other images have {} channel(s)."\
                 .format( thisLaneTaggedShape['c'], validShape['c'] ) )
            
        if len(validShape) != len(thisLaneTaggedShape):
            raise DatasetConstraintError(
                 "Pixel Classification",
                 "All input images must have the same dimensionality.  "\
                 "Your new image has {} dimensions (including channel), but your other images have {} dimensions."\
                 .format( len(thisLaneTaggedShape), len(validShape) ) )
        
        mask_slot = self.PredictionMasks[laneIndex]
        input_shape = self.InputImages[laneIndex].meta.shape
        if mask_slot.ready() and mask_slot.meta.shape[:-1] != input_shape[:-1]:
            raise DatasetConstraintError(
                 "Pixel Classification",
                 "If you supply a prediction mask, it must have the same shape as the input image."\
                 "Your input image has shape {}, but your mask has shape {}."\
                 .format( input_shape, mask_slot.meta.shape ) )
    
    def setInSlot(self, slot, subindex, roi, value):
        # Nothing to do here: All inputs that support __setitem__
        #   are directly connected to internal operators.
        pass

    def propagateDirty(self, slot, subindex, roi):
        # Nothing to do here: All outputs are directly connected to 
        #  internal operators that handle their own dirty propagation.
        pass

    def addLane(self, laneIndex):
        numLanes = len(self.InputImages)
        assert numLanes == laneIndex, "Image lanes must be appended."        
        self.InputImages.resize(numLanes+1)
        self.Bookmarks.resize(numLanes+1)
        self.Bookmarks[numLanes].setValue([]) # Default value
        
    def removeLane(self, laneIndex, finalLength):
        self.InputImages.removeSlot(laneIndex, finalLength)
        self.Bookmarks.removeSlot(laneIndex, finalLength)

    def getLane(self, laneIndex):
        return OperatorSubView(self, laneIndex)

    def importLabels(self, laneIndex, slot):
        # Load the data into the cache
        new_max = self.getLane( laneIndex ).opLabelPipeline.opLabelArray.ingestData( slot )

        # Add to the list of label names if there's a new max label
        old_names = self.LabelNames.value
        old_max = len(old_names)
        if new_max > old_max:
            new_names = old_names + ["Label {}".format(x) for x in range(old_max+1, new_max+1)]
            self.LabelNames.setValue(new_names)

            # Make some default colors, too
            # FIXME: take the colors from default16_new
            from volumina import colortables
            default_colors = colortables.default16_new
            
            label_colors = self.LabelColors.value
            pmap_colors = self.PmapColors.value
            
            self.LabelColors.setValue( label_colors + default_colors[old_max:new_max] )
            self.PmapColors.setValue( pmap_colors + default_colors[old_max:new_max] )

    def mergeLabels(self, from_label, into_label):
        for laneIndex in range(len(self.InputImages)):
            self.getLane( laneIndex ).opLabelPipeline.opLabelArray.mergeLabels(from_label, into_label)

    def clearLabel(self, label_value):
        for laneIndex in range(len(self.InputImages)):
            self.getLane( laneIndex ).opLabelPipeline.opLabelArray.clearLabel(label_value)

class OpLabelPipeline( Operator ):
    RawImage = InputSlot()
    LabelInput = InputSlot()
    DeleteLabel = InputSlot()
    
    Output = OutputSlot()
    nonzeroBlocks = OutputSlot()
    
    def __init__(self, *args, **kwargs):
        super( OpLabelPipeline, self ).__init__( *args, **kwargs )
        
        self.opLabelArray = OpCompressedUserLabelArray( parent=self )
        self.opLabelArray.Input.connect( self.LabelInput )
        self.opLabelArray.eraser.setValue(100)

        self.opLabelArray.deleteLabel.connect( self.DeleteLabel )

        # Connect external outputs to their internal sources
        self.Output.connect( self.opLabelArray.Output )
        self.nonzeroBlocks.connect( self.opLabelArray.nonzeroBlocks )
    
    def setupOutputs(self):
        tagged_shape = self.RawImage.meta.getTaggedShape()
        # labels are created for one channel (i.e. the label) and only in the
        # current time slice, so we can set both c and t to 1
        tagged_shape['c'] = 1
        if 't' in tagged_shape:
            tagged_shape['t'] = 1
        
        # Aim for blocks that are roughly 20px
        block_shape = determineBlockShape( list(tagged_shape.values()), 40**3 )
        self.opLabelArray.blockShape.setValue( block_shape )

    def setInSlot(self, slot, subindex, roi, value):
        # Nothing to do here: All inputs that support __setitem__
        #   are directly connected to internal operators.
        pass

    def execute(self, slot, subindex, roi, result):
        assert False, "Shouldn't get here.  Output is assigned a value in setupOutputs()"

    def propagateDirty(self, slot, subindex, roi):
        # Our output changes when the input changed shape, not when it becomes dirty.
        pass    

class OpPredictionPipelineNoCache(Operator):
    """
    This contains only the cacheless parts of the prediction pipeline, for easy use in headless workflows.
    """
    FeatureImages = InputSlot()
    PredictionMask = InputSlot(optional=True)
    Classifier = InputSlot()
    PredictionsFromDisk = InputSlot( optional=True )
    NumClasses = InputSlot()
    
    HeadlessPredictionProbabilities = OutputSlot() # drange is 0.0 to 1.0
    HeadlessUint8PredictionProbabilities = OutputSlot() # drange 0 to 255
    SimpleSegmentation = OutputSlot()
    HeadlessUncertaintyEstimate = OutputSlot()

    def __init__(self, *args, **kwargs):
        super( OpPredictionPipelineNoCache, self ).__init__( *args, **kwargs )

        # Random forest prediction using the raw feature image slot (not the cached features)
        # This would be bad for interactive labeling, but it's good for headless flows 
        #  because it avoids the overhead of cache.        
        self.cacheless_predict = OpClassifierPredict( parent=self )
        self.cacheless_predict.name = "OpClassifierPredict (Cacheless Path)"
        self.cacheless_predict.Classifier.connect(self.Classifier) 
        self.cacheless_predict.Image.connect(self.FeatureImages) # <--- Not from cache
        self.cacheless_predict.LabelsCount.connect(self.NumClasses)
        self.cacheless_predict.PredictionMask.connect(self.PredictionMask)
        self.HeadlessPredictionProbabilities.connect(self.cacheless_predict.PMaps)

        # Alternate headless output: uint8 instead of float.
        # Note that drange is automatically updated.        
        self.opConvertToUint8 = OpPixelOperator( parent=self )
        self.opConvertToUint8.Input.connect( self.cacheless_predict.PMaps )
        self.opConvertToUint8.Function.setValue( lambda a: (255*a).astype(numpy.uint8) )
        self.HeadlessUint8PredictionProbabilities.connect( self.opConvertToUint8.Output )

        self.opArgmaxChannel = OpArgmaxChannel( parent=self )
        self.opArgmaxChannel.Input.connect( self.cacheless_predict.PMaps )
        self.SimpleSegmentation.connect( self.opArgmaxChannel.Output )
        
        # Create a layer for uncertainty estimate
        self.opUncertaintyEstimator = OpEnsembleMargin( parent=self )
        self.opUncertaintyEstimator.Input.connect( self.cacheless_predict.PMaps )
        self.HeadlessUncertaintyEstimate.connect( self.opUncertaintyEstimator.Output )

    def setupOutputs(self):
        pass

    def execute(self, slot, subindex, roi, result):
        assert False, "Shouldn't get here.  Output is assigned a value in setupOutputs()"

    def propagateDirty(self, slot, subindex, roi):
        # Our output changes when the input changed shape, not when it becomes dirty.
        pass

class OpArgmaxChannel( Operator ):
    """
    At each pixel output the index of the channel with the highest value.
    NOTE: The index is incremented, so the returned channel indexes are 1-based (not 0-based).
    """
    Input = InputSlot()
    Output = OutputSlot()
    
    def setupOutputs(self):
        self.Output.meta.assignFrom( self.Input.meta )
        self.Output.meta.dtype = numpy.uint8 # Assumes no more than 255 channels
        self.Output.meta.shape = self.Input.meta.shape[:-1] + (1,)
        assert self.Input.meta.getAxisKeys()[-1] == 'c'
        assert self.Input.meta.shape[-1] <= 255
    
    def execute(self, slot, subindex, roi, result):
        # Request all input channels
        start = tuple(roi.start)
        stop = tuple(roi.stop[:-1]) + (self.Input.meta.shape[-1],)
        data = self.Input(start, stop).wait()
        
        result[:] = numpy.argmax( data, axis=-1 )[...,numpy.newaxis] # numpy.argmax drops the channel axis.
        result[:] += 1 # Class labels start at 1
        return result

    def propagateDirty(self, slot, subindex, roi):
        roi = roi.copy()
        roi.start[-1] = 0
        roi.stop[-1] = 1
        self.Output.setDirty( roi.start, roi.stop )        

class OpPredictionPipeline(OpPredictionPipelineNoCache):
    """
    This operator extends the cacheless prediction pipeline above with additional outputs for the GUI.
    (It uses caches for these outputs, and has an extra input for cached features.)
    """        
    FreezePredictions = InputSlot()
    CachedFeatureImages = InputSlot()

    PredictionProbabilities = OutputSlot()
    CachedPredictionProbabilities = OutputSlot()

    PredictionProbabilitiesUint8 = OutputSlot()
    
    PredictionProbabilityChannels = OutputSlot( level=1 )
    SegmentationChannels = OutputSlot( level=1 )
    UncertaintyEstimate = OutputSlot()

    def __init__(self, *args, **kwargs):
        super(OpPredictionPipeline, self).__init__( *args, **kwargs )

        # Random forest prediction using CACHED features.
        self.predict = OpClassifierPredict( parent=self )
        self.predict.name = "OpClassifierPredict"
        self.predict.Classifier.connect(self.Classifier) 
        self.predict.Image.connect(self.CachedFeatureImages)
        self.predict.PredictionMask.connect(self.PredictionMask)
        self.predict.LabelsCount.connect( self.NumClasses )
        self.PredictionProbabilities.connect( self.predict.PMaps )

        # Alternate headless output: uint8 instead of float.
        # Note that drange is automatically updated.        
        self.opConvertToUint8 = OpPixelOperator( parent=self )
        self.opConvertToUint8.Input.connect( self.predict.PMaps )
        self.opConvertToUint8.Function.setValue( lambda a: (255*a).astype(numpy.uint8) )
        self.PredictionProbabilitiesUint8.connect( self.opConvertToUint8.Output )

        # Prediction cache for the GUI
        self.prediction_cache_gui = OpSlicedBlockedArrayCache( parent=self )
        self.prediction_cache_gui.name = "prediction_cache_gui"
        self.prediction_cache_gui.inputs["fixAtCurrent"].connect( self.FreezePredictions )
        self.prediction_cache_gui.inputs["Input"].connect( self.predict.PMaps )
        self.CachedPredictionProbabilities.connect(self.prediction_cache_gui.Output )

        # Also provide each prediction channel as a separate layer (for the GUI)
        self.opPredictionSlicer = OpMultiArraySlicer2( parent=self )
        self.opPredictionSlicer.name = "opPredictionSlicer"
        self.opPredictionSlicer.Input.connect( self.prediction_cache_gui.Output )
        self.opPredictionSlicer.AxisFlag.setValue('c')
        self.PredictionProbabilityChannels.connect( self.opPredictionSlicer.Slices )
        
        self.opSegmentor = OpMaxChannelIndicatorOperator( parent=self )
        self.opSegmentor.Input.connect( self.prediction_cache_gui.Output )

        self.opSegmentationSlicer = OpMultiArraySlicer2( parent=self )
        self.opSegmentationSlicer.name = "opSegmentationSlicer"
        self.opSegmentationSlicer.Input.connect( self.opSegmentor.Output )
        self.opSegmentationSlicer.AxisFlag.setValue('c')
        self.SegmentationChannels.connect( self.opSegmentationSlicer.Slices )

        # Create a layer for uncertainty estimate
        self.opUncertaintyEstimator = OpEnsembleMargin( parent=self )
        self.opUncertaintyEstimator.Input.connect( self.prediction_cache_gui.Output )

        # Cache the uncertainty so we get zeros for uncomputed points
        self.opUncertaintyCache = OpSlicedBlockedArrayCache( parent=self )
        self.opUncertaintyCache.name = "opUncertaintyCache"
        self.opUncertaintyCache.Input.connect( self.opUncertaintyEstimator.Output )
        self.opUncertaintyCache.fixAtCurrent.connect( self.FreezePredictions )
        self.UncertaintyEstimate.connect( self.opUncertaintyCache.Output )

    def setupOutputs(self):
        # Set the blockshapes for each input image separately, depending on which axistags it has.
        axisOrder = [ tag.key for tag in self.FeatureImages.meta.axistags ]
        blocksize = 64
        blockDimsX = { 't' : (1,1),
                       'z' : (blocksize,blocksize),
                       'y' : (blocksize,blocksize),
                       'x' : (1,1),
                       'c' : (100, 100) }

        blockDimsY = { 't' : (1,1),
                       'z' : (blocksize,blocksize),
                       'y' : (1,1),
                       'x' : (blocksize,blocksize),
                       'c' : (100,100) }

        blockDimsZ = { 't' : (1,1),
                       'z' : (1,1),
                       'y' : (blocksize,blocksize),
                       'x' : (blocksize,blocksize),
                       'c' : (100,100) }

        blockShapeX = tuple( blockDimsX[k][1] for k in axisOrder )
        blockShapeY = tuple( blockDimsY[k][1] for k in axisOrder )
        blockShapeZ = tuple( blockDimsZ[k][1] for k in axisOrder )

        self.prediction_cache_gui.BlockShape.setValue( (blockShapeX, blockShapeY, blockShapeZ) )
        self.opUncertaintyCache.BlockShape.setValue( (blockShapeX, blockShapeY, blockShapeZ) )

        assert self.opConvertToUint8.Output.meta.drange == (0,255)

class OpEnsembleMargin(Operator):
    """
    Produces a pixelwise measure of the uncertainty of the pixelwise predictions.
    
    Uncertainty is negatively proportional to the difference between the 
    highest two probabilities at every pixel.
    """
    Input = InputSlot()
    Output = OutputSlot()

    def setupOutputs(self):
        self.Output.meta.assignFrom(self.Input.meta)
        taggedShape = self.Input.meta.getTaggedShape()
        taggedShape['c'] = 1
        self.Output.meta.shape = tuple(taggedShape.values())
        
    def execute(self, slot, subindex, roi, result):
        # If there's only 1 channel, there's zero uncertainty
        if self.Input.meta.getTaggedShape()['c'] <= 1:
            result[:] = 0
            return

        roi = copy.copy(roi)
        taggedShape = self.Input.meta.getTaggedShape()
        chanAxis = self.Input.meta.axistags.index('c')
        roi.start[chanAxis] = 0
        roi.stop[chanAxis] = taggedShape['c']
        pmap = self.Input.get(roi).wait()

        # Sort along channel axis so the every pixel's channels are sorted lowest to highest.
        pmap.sort(axis=self.Input.meta.axistags.index('c'))
        pmap = pmap.view(vigra.VigraArray)
        pmap.axistags = self.Input.meta.axistags

        # Subtract the highest channel from the second-highest channel.
        res = pmap.bindAxis('c', -1) - pmap.bindAxis('c', -2)
        res = res.withAxes( *list(taggedShape.keys()) ).view(numpy.ndarray)
        
        # Subtract from 1 to make this an "uncertainty" measure, not a "certainty" measure
        # e.g. predictions of .99 and .01 -> low uncertainty (0.98)
        # e.g. predictions of .51 and .49 -> high uncertainty (0.02)
        result[...] = (1-res)
        return result 

    def propagateDirty(self, inputSlot, subindex, roi):
        roi = roi.copy()
        chanAxis = self.Input.meta.axistags.index('c')
        roi.start[chanAxis] = 0
        roi.stop[chanAxis] = 1
        self.Output.setDirty( roi )

class OpFilterFeatureSelection(Operator):
    FeatureLabelMatrix = InputSlot(level=1)
    FilterMethod = InputSlot(optional=True)
    NumberOfSelectedFeatures = InputSlot()

    SelectedFeatureIDs = OutputSlot()

    def setupOutputs(self):
        # the output slot should maybe contain the internal feature IDs or a bool list of len(internal_feature_ids)
        self.SelectedFeatureIDs.meta.shape = (1,)
        self.SelectedFeatureIDs.meta.dtype = list
        self._filter_method = "ICAP"
        feature_label_matrix = self.FeatureLabelMatrix[0].value
        labels = feature_label_matrix[:, 0]  # first row is labels
        data = feature_label_matrix[:, 1:]  # the rest is data
        self.feature_selector = ilastik_feature_selection.filter_feature_selection.FilterFeatureSelection(data, labels.astype("int"), self._filter_method)

        if self.FilterMethod.connected():
            self._filter_method = self.FilterMethod.value

    def execute(self, slot, subindex, roi, result):

        selected_features = self.feature_selector.run(self.NumberOfSelectedFeatures.value)

        # selected_features_names = [self.FeatureImages[0].meta['channel_names'][i] for i in selected_features]
        # how do I convert feature names to internal feature IDs?

        result = [selected_features]
        return result

    def propagateDirty(self, slot, subindex, roi):
        self.SelectedFeatureIDs.setDirty()

class OpWrapperFeatureSelection(Operator):
    FeatureLabelMatrix = InputSlot(level=1)
    WrapperMethod = InputSlot(optional=True)  # "SFS", "BFS", or "SBE"
    Classifier = InputSlot(optional=True)  # not used. In the future it should be possible to plug in a classifier here.
    # Default classifier it sklearn random forest
    EvaluationFunction = InputSlot(optional=True)  # if this is not connected then we use a default
    ComplexityPenalty = InputSlot(optional=True)

    SelectedFeatureIDs = OutputSlot()

    def setupOutputs(self):
        if self.WrapperMethod.connected():
            self._wrapper_method = self.WrapperMethod.value
        else:
            self._wrapper_method = "SFS"

        if self.Classifier.connected():
            self._classifier = self.Classifier.value
        else:
            from sklearn import ensemble
            self._classifier = ensemble.RandomForestClassifier(n_estimators=100, n_jobs=-1)

        if self.EvaluationFunction.connected():
            self._evaluation_fct = self.EvaluationFunction.value
        else:
            if self.ComplexityPenalty.connected():
                complexity_penalty = self.ComplexityPenalty.value
            else:
                complexity_penalty = 0.07 # default
            self._evaluator = ilastik_feature_selection.wrapper_feature_selection.EvaluationFunction(self._classifier, complexity_penalty = complexity_penalty)
            self._evaluation_fct = self._evaluator.evaluate_feature_set_size_penalty

        # the output slot should maybe contain the internal feature IDs or a bool list of len(internal_feature_ids)
        self.SelectedFeatureIDs.meta.shape = (1,)
        self.SelectedFeatureIDs.meta.dtype = list

    def execute(self, slot, subindex, roi, result):

        feature_label_matrix = self.FeatureLabelMatrix[0].value

        labels = feature_label_matrix[:, 0]  # first row is labels
        data = feature_label_matrix[:, 1:]  # the rest is data


        feature_selector = ilastik_feature_selection.wrapper_feature_selection.WrapperFeatureSelection(data,
                                                                                               labels.astype("int"),
                                                                                               self._evaluation_fct, self._wrapper_method)


        selected_features = feature_selector.run(overshoot=3)[0]

        # selected_features_names = [self.FeatureImages[0].meta['channel_names'][i] for i in selected_features]

        result = [selected_features]
        return result

    def propagateDirty(self, slot, subindex, roi):
        self.SelectedFeatureIDs.setDirty()

class OpGiniFeatureSelection(Operator):
    FeatureLabelMatrix = InputSlot(level=1)
    NumberOfSelectedFeatures = InputSlot()

    SelectedFeatureIDs = OutputSlot()

    def setupOutputs(self):
        # the output slot should maybe contain the internal feature IDs or a bool list of len(internal_feature_ids)
        self.SelectedFeatureIDs.meta.shape = (1,)
        self.SelectedFeatureIDs.meta.dtype = list

    def execute(self, slot, subindex, roi, result):

        feature_label_matrix = self.FeatureLabelMatrix[0].value

        labels = feature_label_matrix[:, 0]  # first row is labels
        data = feature_label_matrix[:, 1:]  # the rest is data

        from sklearn import ensemble
        rf = ensemble.RandomForestClassifier(n_estimators = 100, n_jobs = -1)
        rf.fit(data, labels)
        importances = rf.feature_importances_

        result = [np.argsort(importances)[-self.NumberOfSelectedFeatures.value:].astype("int")]

        # this was an attempt to use Jaime's recursive feature elimination using gini importance. It provided worse
        # results than simply choosing the k best features according to their importance, maybe I have a bug??
        ''' removed_features = np.array([])
        remaining_features = np.arange(data.shape[1])

        pyqtRemoveInputHook()
        import IPython
        IPython.embed()
        pyqtRestoreInputHook()

        for i in range(data.shape[1]):
            sorted_importances = np.argsort(importances)
            removed_features = np.append(removed_features, [remaining_features[sorted_importances[0]]])
            remaining_features = remaining_features[remaining_features != sorted_importances[0]]

            rf.fit(data[:, remaining_features], labels)
            importances = rf.feature_importances_

        result = [removed_features[- self.NumberOfSelectedFeatures.value:].astype("int")]
        '''
        return result

    def propagateDirty(self, slot, subindex, roi):
        self.SelectedFeatureIDs.setDirty()
