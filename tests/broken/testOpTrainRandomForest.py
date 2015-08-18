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
import os
import h5py
import numpy
import vigra

from lazyflow.graph import Graph
from lazyflow.operators import OpTrainRandomForestBlocked, OpPixelFeaturesPresmoothed
from lazyflow.operators.opBlockedSparseLabelArray import OpBlockedSparseLabelArray

import logging
rootLogger = logging.getLogger()
rootLogger.setLevel(logging.INFO)

class TestOpTrainRandomForest(object):
    def setUp(self):
        rootLogger.setLevel(logging.INFO)
        pass
    
    def tearDown(self):
        pass
    
    def test(self):
        graph = Graph()

        testVolumePath = 'tinyfib_volume.h5'

        # Unzip the data if necessary
        if not os.path.exists(testVolumePath):
            zippedTestVolumePath = testVolumePath + ".gz"
            assert os.path.exists(zippedTestVolumePath)
            os.system("gzip -d " + zippedTestVolumePath)
            assert os.path.exists(testVolumePath)
        
        f = h5py.File(testVolumePath, 'r')
        data = f['data'][...]
        data = data.view(vigra.VigraArray)
        data.axistags = vigra.defaultAxistags('txyzc')
        
        labels = f['labels'][...]
        assert data.shape[:-1] == labels.shape[:-1]
        assert labels.shape[-1] == 1
        assert len(data.shape) == 5
        f.close()
        scales = [0.3, 0.7, 1, 1.6, 3.5, 5.0, 10.0]
        featureIds = OpPixelFeaturesPresmoothed.DefaultFeatureIds

        # The following conditions cause this test to *usually* fail, but *sometimes* pass:
        # When using Structure Tensor EVs at sigma >= 3.5 (NaNs in feature matrix)
        # When using Gaussian Gradient Mag at sigma >= 3.5 (inf in feature matrix)
        # When using *any feature* at sigma == 10.0 (NaNs in feature matrix)
        
        #                    sigma:   0.3    0.7    1.0    1.6    3.5    5.0   10.0
        selections = numpy.array( [[False, False, False, False, False, False, False],
                                   [False, False, False, False, False, False, False],
                                   [False, False, False, False,  True, False, False], # ST EVs
                                   [False, False, False, False, False, False, False],
                                   [False, False, False, False, False, False, False],  # GGM
                                   [False, False, False, False, False, False, False]] )
        
        opFeatures = OpPixelFeaturesPresmoothed(graph=graph)
        opFeatures.Input.setValue(data)
        opFeatures.Scales.setValue(scales)
        opFeatures.FeatureIds.setValue(featureIds)
        opFeatures.Matrix.setValue(selections)
        
        opTrain = OpTrainRandomForestBlocked(graph=graph)
        opTrain.Images.resize(1)        
        opTrain.Images[0].connect(opFeatures.Output)
        opTrain.Labels.resize(1)
        opTrain.nonzeroLabelBlocks.resize(1)

        # This test only fails when this flag is True.
        use_sparse_label_storage = True
        
        if use_sparse_label_storage:
            opLabelArray = OpBlockedSparseLabelArray(graph=graph)
            opLabelArray.inputs["shape"].setValue(labels.shape)
            opLabelArray.inputs["blockShape"].setValue((1, 32, 32, 32, 1))
            opLabelArray.inputs["eraser"].setValue(100)
    
            opTrain.nonzeroLabelBlocks[0].connect(opLabelArray.nonzeroBlocks)
            
            # Slice the label data into the sparse array storage
            opLabelArray.Input[...] = labels[...]
            opTrain.Labels[0].connect(opLabelArray.Output)
        else:
            # Skip the sparse storage operator and provide labels as one big block
            opTrain.Labels[0].setValue(labels)
            # One big block
            opTrain.nonzeroLabelBlocks.resize(1)
            opTrain.nonzeroLabelBlocks[0].setValue( [[slice(None, None, None)] * 5] )

        # Sanity check: Make sure we configured the training operator correctly.
        readySlots = [ slot.ready() for slot in opTrain.inputs.values() ]
        assert all(readySlots)
 
        # Generate the classifier       
        classifier = opTrain.Classifier.value

if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)
    if not ret: sys.exit(1)
