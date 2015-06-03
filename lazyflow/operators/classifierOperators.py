###############################################################################
#   lazyflow: data flow based lazy parallel computation framework
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the Lesser GNU General Public License
# as published by the Free Software Foundation; either version 2.1
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# See the files LICENSE.lgpl2 and LICENSE.lgpl3 for full text of the
# GNU Lesser General Public License version 2.1 and 3 respectively.
# This information is also available on the ilastik web site at:
#		   http://ilastik.org/license/
###############################################################################
#Python
import copy
import logging
traceLogger = logging.getLogger("TRACE." + __name__)

#SciPy
import numpy

#lazyflow
from lazyflow.graph import Operator, InputSlot, OutputSlot, OrderedSignal, OperatorWrapper
from lazyflow.roi import sliceToRoi, roiToSlice, getIntersection, roiFromShape, nonzero_bounding_box, enlargeRoiForHalo
from lazyflow.utility import Timer
from lazyflow.classifiers import LazyflowVectorwiseClassifierABC, LazyflowVectorwiseClassifierFactoryABC, \
                                 LazyflowPixelwiseClassifierABC, LazyflowPixelwiseClassifierFactoryABC

from opFeatureMatrixCache import OpFeatureMatrixCache
from opConcatenateFeatureMatrices import OpConcatenateFeatureMatrices

logger = logging.getLogger(__name__)

class OpTrainClassifierBlocked(Operator):
    """
    Owns two child training operators, for 'vectorwise' and 'pixelwise' classifier types.
    Chooses which one to use based on the type of ClassifierFactory provided as input.
    """
    Images = InputSlot(level=1)
    Labels = InputSlot(level=1)
    ClassifierFactory = InputSlot()
    nonzeroLabelBlocks = InputSlot(level=1)
    MaxLabel = InputSlot()
    
    Classifier = OutputSlot()
    
    def __init__(self, *args, **kwargs):
        super(OpTrainClassifierBlocked, self).__init__(*args, **kwargs)
        self.progressSignal = OrderedSignal()
        self._mode = None
        
        # Fully connect the vectorwise training operator
        self._opVectorwiseTrain = OpTrainVectorwiseClassifierBlocked( parent=self )
        self._opVectorwiseTrain.Images.connect( self.Images )
        self._opVectorwiseTrain.Labels.connect( self.Labels )
        self._opVectorwiseTrain.ClassifierFactory.connect( self.ClassifierFactory )
        self._opVectorwiseTrain.nonzeroLabelBlocks.connect( self.nonzeroLabelBlocks )
        self._opVectorwiseTrain.MaxLabel.connect( self.MaxLabel )
        self._opVectorwiseTrain.progressSignal.subscribe( self.progressSignal )

        # Fully connect the pixelwise training operator
        self._opPixelwiseTrain = OpTrainPixelwiseClassifierBlocked( parent=self )            
        self._opPixelwiseTrain.Images.connect( self.Images )
        self._opPixelwiseTrain.Labels.connect( self.Labels )
        self._opPixelwiseTrain.ClassifierFactory.connect( self.ClassifierFactory )
        self._opPixelwiseTrain.nonzeroLabelBlocks.connect( self.nonzeroLabelBlocks )
        self._opPixelwiseTrain.MaxLabel.connect( self.MaxLabel )
        self._opPixelwiseTrain.progressSignal.subscribe( self.progressSignal )
        
    def setupOutputs(self):
        # Construct an inner operator depending on the type of classifier we'll be creating.
        classifier_factory = self.ClassifierFactory.value        
        if issubclass( type(classifier_factory), LazyflowVectorwiseClassifierFactoryABC ):
            new_mode = 'vectorwise'
        elif issubclass( type(classifier_factory), LazyflowPixelwiseClassifierFactoryABC ):
            new_mode = 'pixelwise'
        else:
            raise Exception("Unknown classifier factory type: {}".format( type(classifier_factory) ) )
        
        if new_mode == self._mode:
            return
        
        self.Classifier.disconnect()
        self._mode = new_mode
        
        if self._mode == 'vectorwise':
            self.Classifier.connect( self._opVectorwiseTrain.Classifier )
        elif self._mode == 'pixelwise':
            self.Classifier.connect( self._opPixelwiseTrain.Classifier )

    def execute(self, slot, subindex, roi, result):
        assert False, "Shouldn't get here..."

    def propagateDirty(self, slot, subindex, roi):
        pass

class OpTrainPixelwiseClassifierBlocked(Operator):
    Images = InputSlot(level=1)
    Labels = InputSlot(level=1)
    ClassifierFactory = InputSlot()
    nonzeroLabelBlocks = InputSlot(level=1)
    MaxLabel = InputSlot()
    
    Classifier = OutputSlot()

    def __init__(self, *args, **kwargs):
        super(OpTrainPixelwiseClassifierBlocked, self).__init__(*args, **kwargs)
        self.progressSignal = OrderedSignal()
    
    def setupOutputs(self):
        for slot in list(self.Images) + list(self.Labels):
            assert slot.meta.getAxisKeys()[-1] == 'c', \
                "This opearator assumes channel is the last axis."
        
        self.Classifier.meta.dtype = object
        self.Classifier.meta.shape = (1,)

        # Special metadata for downstream operators using the classifier
        self.Classifier.meta.classifier_factory = self.ClassifierFactory.value

    def cleanUp(self):
        self.progressSignal.clean()
        super( OpTrainPixelwiseClassifierBlocked, self ).cleanUp()

    def execute(self, slot, subindex, roi, result):
        classifier_factory = self.ClassifierFactory.value
        assert issubclass(type(classifier_factory), LazyflowPixelwiseClassifierFactoryABC), \
            "Factory is of type {}, which does not satisfy the LazyflowPixelwiseClassifierFactoryABC interface."\
            "".format( type(classifier_factory) )
        
        # Accumulate all non-zero blocks of each image into lists
        label_data_blocks = []
        image_data_blocks = []
        for image_slot, label_slot, nonzero_block_slot in zip(self.Images, self.Labels, self.nonzeroLabelBlocks):
            block_slicings = nonzero_block_slot.value
            for block_slicing in block_slicings:
                # Get labels
                block_label_roi = sliceToRoi( block_slicing, label_slot.meta.shape )
                block_label_data = label_slot(*block_label_roi).wait()
                
                # Shrink roi to bounding box of actual label pixels
                bb_roi_within_block = nonzero_bounding_box(block_label_data)
                block_label_bb_roi = bb_roi_within_block + block_label_roi[0]

                # Double-check that there is at least 1 non-zero label in the block.
                if (block_label_bb_roi[1] > block_label_bb_roi[0]).all():
                    # Ask for the halo needed by the classifier
                    axiskeys = image_slot.meta.getAxisKeys()
                    halo_shape = classifier_factory.get_halo_shape(axiskeys)
                    assert len(halo_shape) == len( block_label_roi[0] )
                    assert halo_shape[-1] == 0, "Didn't expect a non-zero halo for channel dimension."
    
                    # Expand block by halo, but keep clipped to image bounds
                    padded_label_roi, bb_roi_within_padded = enlargeRoiForHalo( *block_label_bb_roi, 
                                                                                shape=label_slot.meta.shape,
                                                                                sigma=halo_shape,
                                                                                window=1,
                                                                                return_result_roi=True )
                    
                    # Copy labels to new array, which has size == bounding-box + halo
                    padded_label_data = numpy.zeros( padded_label_roi[1] - padded_label_roi[0], label_slot.meta.dtype )                
                    padded_label_data[roiToSlice(*bb_roi_within_padded)] = block_label_data[roiToSlice(*bb_roi_within_block)]
    
                    padded_image_roi = numpy.array( padded_label_roi )
                    assert (padded_image_roi[:, -1] == [0,1]).all()
                    num_channels = image_slot.meta.shape[-1]
                    padded_image_roi[:, -1] = [0, num_channels]
    
                    # Ensure the results are plain ndarray, not VigraArray, 
                    #  which some classifiers might have trouble with.
                    padded_image_data = numpy.asarray( image_slot(*padded_image_roi).wait() )
                    
                    label_data_blocks.append( padded_label_data )
                    image_data_blocks.append( padded_image_data )

        if len(image_data_blocks) == 0:
            result[0] = None
        else:
            axistags = self.Images[0].meta.axistags
            logger.debug("Training new classifier: {}".format( classifier_factory.description ))
            classifier = classifier_factory.create_and_train_pixelwise( image_data_blocks, label_data_blocks, axistags )
            result[0] = classifier
            if classifier is not None:
                assert issubclass(type(classifier), LazyflowPixelwiseClassifierABC), \
                    "Classifier is of type {}, which does not satisfy the LazyflowPixelwiseClassifierABC interface."\
                    "".format( type(classifier) )

    def propagateDirty(self, slot, subindex, roi):
        self.Classifier.setDirty()

class OpTrainVectorwiseClassifierBlocked(Operator):
    Images = InputSlot(level=1)
    Labels = InputSlot(level=1)
    ClassifierFactory = InputSlot()
    nonzeroLabelBlocks = InputSlot(level=1) # TODO: Eliminate this slot. It isn't used any more...
    MaxLabel = InputSlot()
    
    Classifier = OutputSlot()
    
    # Images[N] ---                                                                                         MaxLabel ------
    #              \                                                                                                       \
    # Labels[N] --> opFeatureMatrixCaches ---(FeatureImage[N])---> opConcatenateFeatureImages ---(label+feature matrix)---> OpTrainFromFeatures ---(Classifier)--->

    def __init__(self, *args, **kwargs):
        super(OpTrainVectorwiseClassifierBlocked, self).__init__(*args, **kwargs)
        self.progressSignal = OrderedSignal()
        
        self._opFeatureMatrixCaches = OperatorWrapper( OpFeatureMatrixCache, parent=self )
        self._opFeatureMatrixCaches.LabelImage.connect( self.Labels )
        self._opFeatureMatrixCaches.FeatureImage.connect( self.Images )
        self._opFeatureMatrixCaches.NonZeroLabelBlocks.connect( self.nonzeroLabelBlocks )
        
        self._opConcatenateFeatureMatrices = OpConcatenateFeatureMatrices( parent=self )
        self._opConcatenateFeatureMatrices.FeatureMatrices.connect( self._opFeatureMatrixCaches.LabelAndFeatureMatrix )
        self._opConcatenateFeatureMatrices.ProgressSignals.connect( self._opFeatureMatrixCaches.ProgressSignal )
        
        self._opTrainFromFeatures = OpTrainClassifierFromFeatureVectors( parent=self )
        self._opTrainFromFeatures.ClassifierFactory.connect( self.ClassifierFactory )
        self._opTrainFromFeatures.LabelAndFeatureMatrix.connect( self._opConcatenateFeatureMatrices.ConcatenatedOutput )
        self._opTrainFromFeatures.MaxLabel.connect( self.MaxLabel )
        
        self.Classifier.connect( self._opTrainFromFeatures.Classifier )

        # Progress reporting
        def _handleFeatureProgress( progress ):
            self.progressSignal( 0.8*progress )
        self._opConcatenateFeatureMatrices.progressSignal.subscribe( _handleFeatureProgress )
        
        def _handleTrainingComplete():
            self.progressSignal( 100.0 )
        self._opTrainFromFeatures.trainingCompleteSignal.subscribe( _handleTrainingComplete )

    def cleanUp(self):
        self.progressSignal.clean()
        self.Classifier.disconnect()
        super( OpTrainVectorwiseClassifierBlocked, self ).cleanUp()

    def setupOutputs(self):
        pass # Nothing to do; our output is connected to an internal operator.

    def execute(self, slot, subindex, roi, result):
        assert False, "Shouldn't get here..."

    def propagateDirty(self, slot, subindex, roi):
        pass

class OpTrainClassifierFromFeatureVectors(Operator):
    ClassifierFactory = InputSlot()
    LabelAndFeatureMatrix = InputSlot()
    
    MaxLabel = InputSlot()
    Classifier = OutputSlot()
    
    def __init__(self, *args, **kwargs):
        super(OpTrainClassifierFromFeatureVectors, self).__init__(*args, **kwargs)
        self.trainingCompleteSignal = OrderedSignal()

        # TODO: Progress...
        #self.progressSignal = OrderedSignal()

    def setupOutputs(self):
        self.Classifier.meta.dtype = object
        self.Classifier.meta.shape = (1,)
        
        # Special metadata for downstream operators using the classifier
        self.Classifier.meta.classifier_factory = self.ClassifierFactory.value

    def execute(self, slot, subindex, roi, result):
        channel_names = self.LabelAndFeatureMatrix.meta.channel_names
        labels_and_features = self.LabelAndFeatureMatrix.value
        featMatrix = labels_and_features[:,1:]
        labelsMatrix = labels_and_features[:,0:1].astype(numpy.uint32)
        
        maxLabel = self.MaxLabel.value

        if featMatrix.shape[0] < maxLabel:
            # If there isn't enough data for the random forest to train with, return None
            result[:] = None
            self.trainingCompleteSignal()
            return

        classifier_factory = self.ClassifierFactory.value
        assert issubclass(type(classifier_factory), LazyflowVectorwiseClassifierFactoryABC), \
            "Factory is of type {}, which does not satisfy the LazyflowVectorwiseClassifierFactoryABC interface."\
            "".format( type(classifier_factory) )

        logger.debug("Training new classifier: {}".format( classifier_factory.description ))
        classifier = classifier_factory.create_and_train( featMatrix, labelsMatrix[:,0], channel_names )
        result[0] = classifier
        if classifier is not None:
            assert issubclass(type(classifier), LazyflowVectorwiseClassifierABC), \
                "Classifier is of type {}, which does not satisfy the LazyflowVectorwiseClassifierABC interface."\
                "".format( type(classifier) )        

        self.trainingCompleteSignal()
        return result

    def propagateDirty(self, slot, subindex, roi):
        self.Classifier.setDirty()


class OpClassifierPredict(Operator):
    Image = InputSlot()
    LabelsCount = InputSlot()
    Classifier = InputSlot()
    
    # An entire prediction request is skipped if the mask is all zeros for the requested roi.
    # Otherwise, the request is serviced as usual and the mask is ignored.
    PredictionMask = InputSlot(optional=True)

    PMaps = OutputSlot()
    
    def __init__(self, *args, **kwargs):
        super( OpClassifierPredict, self ).__init__(*args, **kwargs)
        self._mode = None
        self._prediction_op = None
    
    def setupOutputs(self):
        # Construct an inner operator depending on the type of classifier we'll be using.
        # We don't want to access the classifier directly here because that would trigger the full computation already.
        # Instead, we require the factory to be passed along with the classifier metadata.
        
        try:
            classifier_factory = self.Classifier.meta.classifier_factory
        except KeyError:
            raise Exception( "Classifier slot must include classifier factory as metadata." )
        
        if issubclass( classifier_factory.__class__, LazyflowVectorwiseClassifierFactoryABC ):
            new_mode = 'vectorwise'
        elif issubclass( classifier_factory.__class__, LazyflowPixelwiseClassifierFactoryABC ):
            new_mode = 'pixelwise'
        else:
            raise Exception("Unknown classifier factory type: {}".format( type(classifier_factory) ) )
        
        if new_mode == self._mode:
            return
        
        if self._mode is not None:
            self.PMaps.disconnect()
            self._prediction_op.cleanUp()
        self._mode = new_mode
        
        if self._mode == 'vectorwise':
            self._prediction_op = OpVectorwiseClassifierPredict( parent=self )
        elif self._mode == 'pixelwise':
            self._prediction_op = OpPixelwiseClassifierPredict( parent=self )            

        self._prediction_op.PredictionMask.connect( self.PredictionMask )
        self._prediction_op.Image.connect( self.Image )
        self._prediction_op.LabelsCount.connect( self.LabelsCount )
        self._prediction_op.Classifier.connect( self.Classifier )
        self.PMaps.connect( self._prediction_op.PMaps )

    def execute(self, slot, subindex, roi, result):
        assert False, "Shouldn't get here..."

    def propagateDirty(self, slot, subindex, roi):
        if slot == self.Classifier:
            self.PMaps.setDirty()

class OpPixelwiseClassifierPredict(Operator):
    Image = InputSlot()
    LabelsCount = InputSlot()
    Classifier = InputSlot()

    # An entire prediction request is skipped if the mask is all zeros for the requested roi.
    # Otherwise, the request is serviced as usual and the mask is ignored.
    PredictionMask = InputSlot(optional=True)

    PMaps = OutputSlot()
    
    def __init__(self, *args, **kwargs):
        super( OpPixelwiseClassifierPredict, self ).__init__(*args, **kwargs)

        # Make sure the entire image is dirty if the prediction mask is removed.
        self.PredictionMask.notifyUnready( lambda s: self.PMaps.setDirty() )
    
    def setupOutputs(self):
        assert self.Image.meta.getAxisKeys()[-1] == 'c'
        
        nlabels = max(self.LabelsCount.value, 1) #we'll have at least 2 labels once we actually predict something
                                                #not setting it to 0 here is friendlier to possible downstream
                                                #ilastik operators, setting it to 2 causes errors in pixel classification
                                                #(live prediction doesn't work when only two labels are present)

        self.PMaps.meta.dtype = numpy.float32
        self.PMaps.meta.axistags = copy.copy(self.Image.meta.axistags)
        self.PMaps.meta.shape = self.Image.meta.shape[:-1]+(nlabels,) # FIXME: This assumes that channel is the last axis
        self.PMaps.meta.drange = (0.0, 1.0)

    def execute(self, slot, subindex, roi, result):
        classifier = self.Classifier.value
        
        # Training operator may return 'None' if there was no data to train with
        skip_prediction = (classifier is None)

        # Shortcut: If the mask is totally zero, skip this request entirely
        if not skip_prediction and self.PredictionMask.ready():
            mask_roi = numpy.array((roi.start, roi.stop))
            mask_roi[:,-1:] = [[0],[1]]
            start, stop = map(tuple, mask_roi)
            mask = self.PredictionMask( start, stop ).wait()
            skip_prediction = not numpy.any(mask)

        if skip_prediction:
            result[:] = 0.0
            return result

        assert issubclass(type(classifier), LazyflowPixelwiseClassifierABC), \
            "Classifier is of type {}, which does not satisfy the LazyflowPixelwiseClassifierABC interface."\
            "".format( type(classifier) )

        upstream_roi = (roi.start, roi.stop)
        # Ask for the halo needed by the classifier
        axiskeys = self.Image.meta.getAxisKeys()
        halo_shape = classifier.get_halo_shape(axiskeys)
        assert len(halo_shape) == len( upstream_roi[0] )
        assert halo_shape[-1] == 0, "Didn't expect a non-zero halo for channel dimension."

        # Expand block by halo, then clip to image bounds
        upstream_roi = numpy.array( upstream_roi )
        upstream_roi[0] -= halo_shape
        upstream_roi[1] += halo_shape
        upstream_roi = getIntersection( upstream_roi, roiFromShape(self.Image.meta.shape) )
        upstream_roi = numpy.asarray( upstream_roi )

        # Determine how to extract the data from the result (without the halo)
        downstream_roi = numpy.array((roi.start, roi.stop))
        downstream_channels = self.PMaps.meta.shape[-1]
        roi_within_result = downstream_roi - upstream_roi[0]
        roi_within_result[:,-1] = [0, downstream_channels]

        # Request all upstream channels
        input_channels = self.Image.meta.shape[-1]
        upstream_roi[:,-1] = [0, input_channels]

        # Request the data
        input_data = self.Image(*upstream_roi).wait()
        axistags = self.Image.meta.axistags
        probabilities = classifier.predict_probabilities_pixelwise( input_data, axistags )
        
        # We're expecting a channel for each label class.
        # If we didn't provide at least one sample for each label,
        #  we may get back fewer channels.
        if probabilities.shape[-1] != self.PMaps.meta.shape[-1]:
            # Copy to an array of the correct shape
            # This is slow, but it's an unusual case
            assert probabilities.shape[-1] == len(classifier.known_classes)
            full_probabilities = numpy.zeros( probabilities.shape[:-1] + (self.PMaps.meta.shape[-1],), dtype=numpy.float32 )
            for i, label in enumerate(classifier.known_classes):
                full_probabilities[..., label-1] = probabilities[..., i]
            
            probabilities = full_probabilities

        # Extract requested region (discard halo)
        probabilities = probabilities[ roiToSlice(*roi_within_result) ]
        
        # Copy only the prediction channels the client requested.
        result[...] = probabilities[...,roi.start[-1]:roi.stop[-1]]
        return result

    def propagateDirty(self, slot, subindex, roi):
        if slot == self.Classifier:
            self.logger.debug("classifier changed, setting dirty")
            self.PMaps.setDirty()
        elif slot == self.Image:
            self.PMaps.setDirty()
        elif slot == self.PredictionMask:
            self.PMaps.setDirty(roi.start, roi.stop)

class OpVectorwiseClassifierPredict(Operator):
    Image = InputSlot()
    LabelsCount = InputSlot()
    Classifier = InputSlot()
    
    # An entire prediction request is skipped if the mask is all zeros for the requested roi.
    # Otherwise, the request is serviced as usual and the mask is ignored.
    PredictionMask = InputSlot(optional=True)
    
    PMaps = OutputSlot()

    def __init__(self, *args, **kwargs):
        super( OpVectorwiseClassifierPredict, self ).__init__(*args, **kwargs)

        # Make sure the entire image is dirty if the prediction mask is removed.
        self.PredictionMask.notifyUnready( lambda s: self.PMaps.setDirty() )

    def setupOutputs(self):
        assert self.Image.meta.getAxisKeys()[-1] == 'c'
        
        nlabels = max(self.LabelsCount.value, 1) #we'll have at least 2 labels once we actually predict something
                                                #not setting it to 0 here is friendlier to possible downstream
                                                #ilastik operators, setting it to 2 causes errors in pixel classification
                                                #(live prediction doesn't work when only two labels are present)

        self.PMaps.meta.assignFrom( self.Image.meta )
        self.PMaps.meta.dtype = numpy.float32
        self.PMaps.meta.shape = self.Image.meta.shape[:-1]+(nlabels,) # FIXME: This assumes that channel is the last axis
        self.PMaps.meta.drange = (0.0, 1.0)
        
        ideal_blockshape = self.Image.meta.ideal_blockshape
        if ideal_blockshape is None:
            ideal_blockshape = (0,) * len( self.Image.meta.shape )
        ideal_blockshape = list(ideal_blockshape)
        ideal_blockshape[-1] = self.PMaps.meta.shape[-1]
        self.PMaps.meta.ideal_blockshape = tuple(ideal_blockshape)
        
        output_channels = nlabels
        input_channels = self.Image.meta.shape[-1]
        # Temporarily consumed RAM includes the following:
        # >> result array: 4 * N output_channels
        # >> (times 2 due to temporary variable)
        # >> input data allocation
        classifier_factory = self.Classifier.meta.classifier_factory
        classifier_ram_per_pixelchannel = classifier_factory.estimated_ram_usage_per_requested_predictionchannel()
        classifier_ram_per_pixel = classifier_ram_per_pixelchannel * output_channels
        feature_ram_per_pixel = max(self.Image.meta.dtype().nbytes, 4) * input_channels
        self.PMaps.meta.ram_usage_per_requested_pixel = classifier_ram_per_pixel + feature_ram_per_pixel

    def execute(self, slot, subindex, roi, result):
        classifier = self.Classifier.value
        
        # Training operator may return 'None' if there was no data to train with
        skip_prediction = (classifier is None)

        # Shortcut: If the mask is totally zero, skip this request entirely
        if not skip_prediction and self.PredictionMask.ready():
            mask_roi = numpy.array((roi.start, roi.stop))
            mask_roi[:,-1:] = [[0],[1]]
            start, stop = map(tuple, mask_roi)
            mask = self.PredictionMask( start, stop ).wait()
            skip_prediction = not numpy.any(mask)
            del mask

        if skip_prediction:
            result[:] = 0.0
            return result

        assert issubclass(type(classifier), LazyflowVectorwiseClassifierABC), \
            "Classifier is of type {}, which does not satisfy the LazyflowVectorwiseClassifierABC interface."\
            "".format( type(classifier) )

        key = roi.toSlice()
        newKey = key[:-1]
        newKey += (slice(0,self.Image.meta.shape[-1],None),)

        with Timer() as features_timer:
            input_data = self.Image[newKey].wait()

        input_data = numpy.asarray(input_data, numpy.float32)

        shape=input_data.shape
        prod = numpy.prod(shape[:-1])
        features = input_data.reshape((prod, shape[-1]))

        with Timer() as prediction_timer:
            probabilities = classifier.predict_probabilities( features )

        logger.debug( "Features took {} seconds, Prediction took {} seconds for roi: {} : {}"\
                      .format( features_timer.seconds(), prediction_timer.seconds(), roi.start, roi.stop ) )

        assert probabilities.shape[1] <= self.PMaps.meta.shape[-1], \
            "Error: Somehow the classifier has more label classes than expected:"\
            " Got {} classes, expected {} classes"\
            .format( probabilities.shape[1], self.PMaps.meta.shape[-1] )
        
        # We're expecting a channel for each label class.
        # If we didn't provide at least one sample for each label,
        #  we may get back fewer channels.
        if probabilities.shape[1] < self.PMaps.meta.shape[-1]:
            # Copy to an array of the correct shape
            # This is slow, but it's an unusual case
            assert probabilities.shape[-1] == len(classifier.known_classes)
            full_probabilities = numpy.zeros( probabilities.shape[:-1] + (self.PMaps.meta.shape[-1],), dtype=numpy.float32 )
            for i, label in enumerate(classifier.known_classes):
                full_probabilities[:, label-1] = probabilities[:, i]
            
            probabilities = full_probabilities
        
        # Reshape to image
        probabilities.shape = shape[:-1] + (self.PMaps.meta.shape[-1],)

        # Copy only the prediction channels the client requested.
        result[...] = probabilities[...,roi.start[-1]:roi.stop[-1]]
        return result

    def propagateDirty(self, slot, subindex, roi):
        if slot == self.Classifier:
            self.logger.debug("classifier changed, setting dirty")
            self.PMaps.setDirty()
        elif slot == self.Image:
            self.PMaps.setDirty()
        elif slot == self.PredictionMask:
            self.PMaps.setDirty(roi.start, roi.stop)

class OpAreas(Operator):
    name = "OpAreas"
    description = "counting pixel areas"

    inputSlots = [InputSlot("Input"), InputSlot("NumberOfChannels")]
    outputSlots = [OutputSlot("Areas")]

    logger = logging.getLogger(__name__+".OpAreas")

    def setupOutputs(self):

        self.outputs["Areas"].meta.shape = (self.inputs["NumberOfChannels"].value,)

    def execute(self, slot, subindex, roi, result):
        img = self.inputs["Input"][:].wait()

        numC = self.inputs["NumberOfChannels"].value

        areas = []
        for i in range(numC):
            areas.append(0)

        for i in img.flat:
            areas[int(i)] +=1

        return numpy.array(areas)



    def propagateDirty(self, slot, subindex, roi):
        key = roi.toSlice()
        self.outputs["Output"].setDirty(key)

    @property
    def shape(self):
        return self.outputs["Output"].meta.shape

    @property
    def dtype(self):
        return self.outputs["Output"].meta.dtype
