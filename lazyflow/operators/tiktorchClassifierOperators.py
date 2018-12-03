from __future__ import absolute_import
from builtins import zip
from builtins import map
from builtins import range
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
from lazyflow.classifiers import LazyflowVectorwiseClassifierABC, LazyflowVectorwiseClassifierFactoryABC, \
                                 LazyflowPixelwiseClassifierABC, LazyflowPixelwiseClassifierFactoryABC

from .classifierOperators import OpTrainClassifierBlocked, OpTrainPixelwiseClassifierBlocked, OpClassifierPredict, \
                                 OpPixelwiseClassifierPredict, OpVectorwiseClassifierPredict
from .tiktorchUtils import IlastikBlockinator

logger = logging.getLogger(__name__)

class OpTikTorchTrainClassifierBlocked(OpTrainClassifierBlocked):
    
    def __init__(self, *args, **kwargs):
        super(OpTikTorchTrainClassifierBlocked, self).__init__(*args, **kwargs)

        # Fully connect the pixelwise training operator
        self._opPixelwiseTrain = OpTikTorchTrainPixelwiseClassifierBlocked( parent=self )
        self._opPixelwiseTrain.Images.connect( self.Images )
        self._opPixelwiseTrain.Labels.connect( self.Labels )
        self._opPixelwiseTrain.ClassifierFactory.connect( self.ClassifierFactory )
        self._opPixelwiseTrain.nonzeroLabelBlocks.connect( self.nonzeroLabelBlocks )
        self._opPixelwiseTrain.MaxLabel.connect( self.MaxLabel )
        self._opPixelwiseTrain.progressSignal.subscribe( self.progressSignal )
        

class OpTikTorchTrainPixelwiseClassifierBlocked(OpTrainPixelwiseClassifierBlocked):

    def __init__(self, *args, **kwargs):
        super(OpTikTorchTrainPixelwiseClassifierBlocked, self).__init__(*args, **kwargs)

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

                bb_roi_within_block = numpy.array([[0, 0, 0, 0], list(block_label_data.shape)])
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

        channel_names = self.Images[0].meta.channel_names
        axistags = self.Images[0].meta.axistags
        logger.debug("Training new pixelwise classifier: {}".format(classifier_factory.description))
        classifier = classifier_factory.create_and_train_pixelwise(image_data_blocks, label_data_blocks, axistags,
                                                                   channel_names)
        result[0] = classifier
        if classifier is not None:
            assert issubclass(type(classifier), LazyflowPixelwiseClassifierABC), \
                "Classifier is of type {}, which does not satisfy the LazyflowPixelwiseClassifierABC interface." \
                "".format(type(classifier))

class OpTikTorchClassifierPredict(OpClassifierPredict):
    
    def __init__(self, *args, **kwargs):
        super(OpTikTorchClassifierPredict, self).__init__(*args, **kwargs)
    
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
            self._prediction_op = OpVectorwiseClassifierPredict(parent=self)
        elif self._mode == 'pixelwise':
            self._prediction_op = OpTikTorchPixelwiseClassifierPredict(parent=self)

        self._prediction_op.PredictionMask.connect(self.PredictionMask)
        self._prediction_op.Image.connect(self.Image)
        self._prediction_op.LabelsCount.connect(self.LabelsCount)
        self._prediction_op.Classifier.connect(self.Classifier)
        self.PMaps.connect(self._prediction_op.PMaps)


class OpTikTorchPixelwiseClassifierPredict(OpPixelwiseClassifierPredict):
    def __init__(self, *args, **kwargs):
        super(OpTikTorchPixelwiseClassifierPredict, self ).__init__(*args, **kwargs)

    def execute(self, slot, subindex, roi, result):
        classifier = self.Classifier.value
        
        # Training operator may return 'None' if there was no data to train with
        skip_prediction = (classifier is None)

        # Shortcut: If the mask is totally zero, skip this request entirely
        if not skip_prediction and self.PredictionMask.ready():
            mask_roi = numpy.array((roi.start, roi.stop))
            mask_roi[:,-1:] = [[0],[1]]
            start, stop = list(map(tuple, mask_roi))
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
        upstream_roi = numpy.array(upstream_roi)

        # Determine how to extract the data from the result (without the halo)
        downstream_roi = numpy.array((roi.start, roi.stop))
        predictions_roi = downstream_roi[:, :-1] - upstream_roi[0, :-1]

        # Request all upstream channels
        input_channels = self.Image.meta.shape[-1]
        upstream_roi[:, -1] = [0, input_channels]

        # Request the data
        axistags = self.Image.meta.axistags
        blockinator = IlastikBlockinator(data_slot=self.Image, halo=list(halo_shape))
        input_data = blockinator[upstream_roi]
        probabilities = classifier.predict_probabilities_pixelwise( input_data, predictions_roi, axistags )
        
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

        # Copy only the prediction channels the client requested.
        result[...] = probabilities[..., roi.start[-1]:roi.stop[-1]]
        return result