# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Copyright 2011-2014, the ilastik developers

#Python
import copy
import logging
traceLogger = logging.getLogger("TRACE." + __name__)

#SciPy
import numpy

#lazyflow
from lazyflow.graph import Operator, InputSlot, OutputSlot, OrderedSignal, OperatorWrapper
from lazyflow.roi import sliceToRoi, roiToSlice
from lazyflow.classifiers import LazyflowClassifierABC, LazyflowClassifierFactoryABC

from opFeatureMatrixCache import OpFeatureMatrixCache
from opConcatenateFeatureMatrices import OpConcatenateFeatureMatrices

class OpTrainClassifierBlocked(Operator):
    Images = InputSlot(level=1)
    Labels = InputSlot(level=1)
    ClassifierFactory = InputSlot()
    nonzeroLabelBlocks = InputSlot(level=1) # TODO: Eliminate this slot. It isn't used any more...
    MaxLabel = InputSlot()
    
    Classifier = OutputSlot()
    
    # Images[N] ---                                                                                    MaxLabel ------
    #              \                                                                                                  \
    # Labels[N] --> opFeatureMatrixCaches ---(FeatureImage[N])---> opConcatenateFeatureImages ---(FeatureMatrices)---> OpTrainFromFeatures ---(Classifier)--->

    def __init__(self, *args, **kwargs):
        super(OpTrainClassifierBlocked, self).__init__(*args, **kwargs)        
        self.progressSignal = OrderedSignal()
        
        self._opFeatureMatrixCaches = OperatorWrapper( OpFeatureMatrixCache, parent=self )
        self._opFeatureMatrixCaches.LabelImage.connect( self.Labels )
        self._opFeatureMatrixCaches.FeatureImage.connect( self.Images )
        self._opFeatureMatrixCaches.NonZeroLabelBlocks.connect( self.nonzeroLabelBlocks )
        
        self._opConcatenateFeatureMatrices = OpConcatenateFeatureMatrices( parent=self )
        self._opConcatenateFeatureMatrices.FeatureMatrices.connect( self._opFeatureMatrixCaches.LabelAndFeatureMatrix )
        self._opConcatenateFeatureMatrices.ProgressSignals.connect( self._opFeatureMatrixCaches.ProgressSignal )
        
        self._opTrainFromFeatures = OpTrainClassifierFromFeatures( parent=self )
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

    def setupOutputs(self):
        pass # Nothing to do; our output is connected to an internal operator.

    def execute(self, slot, subindex, roi, result):
        assert False, "Shouldn't get here..."

    def propagateDirty(self, slot, subindex, roi):
        pass

class OpTrainClassifierFromFeatures(Operator):
    ClassifierFactory = InputSlot()
    LabelAndFeatureMatrix = InputSlot()
    
    MaxLabel = InputSlot()
    Classifier = OutputSlot()
    
    def __init__(self, *args, **kwargs):
        super(OpTrainClassifierFromFeatures, self).__init__(*args, **kwargs)
        self.trainingCompleteSignal = OrderedSignal()

        # TODO: Progress...
        #self.progressSignal = OrderedSignal()

    def setupOutputs(self):
        self.Classifier.meta.dtype = object
        self.Classifier.meta.shape = (1,)

    def execute(self, slot, subindex, roi, result):
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
        assert isinstance(classifier_factory, LazyflowClassifierFactoryABC), \
            "Factory is of type {}, which does not satisfy the LazyflowClassifierFactoryABC interface."\
            "".format( type(classifier_factory) )

        classifier = classifier_factory.create_and_train( featMatrix, labelsMatrix[:,0] )
        assert isinstance(classifier, LazyflowClassifierABC), \
            "Classifier is of type {}, which does not satisfy the LazyflowClassifierABC interface."\
            "".format( type(classifier) )

        result[0] = classifier
        
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

        assert isinstance(classifier, LazyflowClassifierABC), \
            "Classifier is of type {}, which does not satisfy the LazyflowClassifierABC interface."\
            "".format( type(classifier) )

        key = roi.toSlice()
        newKey = key[:-1]
        newKey += (slice(0,self.Image.meta.shape[-1],None),)

        input_data = self.Image[newKey].wait()
        shape=input_data.shape
        prod = numpy.prod(shape[:-1])
        features = input_data.reshape((prod, shape[-1]))

        probabilities = classifier.predict_probabilities( features )
        
        # We're expecting a channel for each label class.
        # If we didn't provide at least one sample for each label,
        #  we may get back fewer channels.
        if probabilities.shape[1] != self.PMaps.meta.shape[-1]:
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


class OpSegmentation(Operator):
    name = "OpSegmentation"
    description = "displaying highest probability class for each pixel"

    inputSlots = [InputSlot("Input")]
    outputSlots = [OutputSlot("Output")]
    
    logger = logging.getLogger(__name__+".OpSegmentation")

    def setupOutputs(self):
        inputSlot = self.inputs["Input"]
        self.outputs["Output"].meta.shape = inputSlot.meta.shape[:-1] + (1,)
        self.outputs["Output"].meta.dtype = numpy.uint8 #who is going to have more than 256 classes?
        self.outputs["Output"].meta.axistags = inputSlot.meta.axistags

    def execute(self, slot, subindex, roi, result):
        key = roiToSlice(roi.start,roi.stop)
        shape = self.inputs["Input"].meta.shape

        rstart, rstop = sliceToRoi(key, self.outputs["Output"].meta.shape)
        rstart[-1] = 0
        rstop[-1] = shape[-1]
        rkey = roiToSlice(rstart, rstop)
        img = self.inputs["Input"][rkey].wait()
        axis = img.ndim - 1
        result = numpy.argmax(img, axis=axis)
        result.resize(result.shape + (1,))
        return result

    def propagateDirty(self, slot, subindex, roi):
        key = roi.toSlice()
        ndim = len(self.outputs['Output'].meta.shape)
        if len(key) > ndim:
            key = key[:ndim]
        self.outputs["Output"].setDirty(key)

    @property
    def shape(self):
        return self.outputs["Output"].meta.shape

    @property
    def dtype(self):
        return self.outputs["Output"].meta.dtype


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
