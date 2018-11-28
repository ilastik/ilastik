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

from .classifierOperators import OpTrainClassifierBlocked, OpTrainPixelwiseClassifierBlocked

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
                
                # Shrink roi to bounding box of actual label pixels
                bb_roi_within_block = nonzero_bounding_box(block_label_data)
                block_label_bb_roi = bb_roi_within_block + block_label_roi[0]

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
