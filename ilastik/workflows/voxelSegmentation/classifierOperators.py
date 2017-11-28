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
#          http://ilastik.org/license/
###############################################################################
# Python
import copy
import logging
traceLogger = logging.getLogger("TRACE." + __name__)

# SciPy
import numpy

# lazyflow
from lazyflow.graph import Operator, InputSlot, OutputSlot, OrderedSignal, OperatorWrapper
from lazyflow.roi import sliceToRoi, roiToSlice, getIntersection, roiFromShape, nonzero_bounding_box, enlargeRoiForHalo
from lazyflow.utility import Timer
from lazyflow.classifiers import LazyflowVectorwiseClassifierABC, LazyflowVectorwiseClassifierFactoryABC, \
    LazyflowPixelwiseClassifierABC, LazyflowPixelwiseClassifierFactoryABC

from lazyflow.operators.opConcatenateFeatureMatrices import OpConcatenateFeatureMatrices

from lazyflow.operators.opFeatureMatrixCache import OpFeatureMatrixCache
from .utils import get_supervoxel_features, get_supervoxel_labels, slic_to_mask



logger = logging.getLogger(__name__)


class OpTrainSupervoxelClassifierBlocked(Operator):
    """
    Owns two child training operators, for 'vectorwise' and 'pixelwise' classifier types.
    Chooses which one to use based on the type of ClassifierFactory provided as input.
    """
    Images = InputSlot(level=1)
    SupervoxelSegmentation = InputSlot(level=1)
    Labels = InputSlot(level=1)
    SupervoxelFeatures = InputSlot(level=1)
    SupervoxelLabels = InputSlot(level=1)
    ClassifierFactory = InputSlot()
    nonzeroLabelBlocks = InputSlot(level=1)  # Used only in the pixelwise case.

    Classifier = OutputSlot()

    def __init__(self, *args, **kwargs):
        print("init {}".format(self.__class__))
        super(OpTrainSupervoxelClassifierBlocked, self).__init__(*args, **kwargs)
        self.progressSignal = OrderedSignal()
        self._mode = None

        # Fully connect the vectorwise training operator
        self._opVectorwiseTrain = OpTrainSupervoxelwiseClassifierBlocked(parent=self)
        self._opVectorwiseTrain.Images.connect(self.Images)
        self._opVectorwiseTrain.SupervoxelSegmentation.connect(self.SupervoxelSegmentation)
        self._opVectorwiseTrain.SupervoxelFeatures.connect(self.SupervoxelFeatures)
        self._opVectorwiseTrain.SupervoxelLabels.connect(self.SupervoxelLabels)
        self._opVectorwiseTrain.Labels.connect(self.Labels)
        self._opVectorwiseTrain.ClassifierFactory.connect(self.ClassifierFactory)
        self._opVectorwiseTrain.progressSignal.subscribe(self.progressSignal)

        # # Fully connect the pixelwise training operator
        # self._opPixelwiseTrain = OpTrainPixelwiseClassifierBlocked(parent=self)
        # self._opPixelwiseTrain.Images.connect(self.Images)
        # self._opPixelwiseTrain.Labels.connect(self.Labels)
        # self._opPixelwiseTrain.ClassifierFactory.connect(self.ClassifierFactory)
        # self._opPixelwiseTrain.nonzeroLabelBlocks.connect(self.nonzeroLabelBlocks)
        # self._opPixelwiseTrain.MaxLabel.connect(self.MaxLabel)
        # self._opPixelwiseTrain.progressSignal.subscribe(self.progressSignal)

    def setupOutputs(self):
        # Construct an inner operator depending on the type of classifier we'll be creating.
        classifier_factory = self.ClassifierFactory.value
        if issubclass(type(classifier_factory), LazyflowVectorwiseClassifierFactoryABC):
            new_mode = 'vectorwise'
        else:
            raise Exception("Unknown classifier factory type: {}".format(type(classifier_factory)))

        if new_mode == self._mode:
            return

        self.Classifier.disconnect()
        self._mode = new_mode

        if self._mode == 'vectorwise':
            self.Classifier.connect(self._opVectorwiseTrain.Classifier)
        elif self._mode == 'pixelwise':
            raise RuntimeError("shouldn't be here")
            # self.Classifier.connect(self._opPixelwiseTrain.Classifier)

    def execute(self, slot, subindex, roi, result):
        assert False, "Shouldn't get here..."

    def propagateDirty(self, slot, subindex, roi):
        pass


class OpTrainSupervoxelwiseClassifierBlocked(Operator):
    Images = InputSlot(level=1)
    SupervoxelSegmentation = InputSlot(level=1)
    Labels = InputSlot(level=1)
    SupervoxelFeatures = InputSlot(level=1)
    SupervoxelLabels = InputSlot(level=1)
    ClassifierFactory = InputSlot()

    Classifier = OutputSlot()

    # Images[N] ---                                                                                         MaxLabel ------
    #              \                                                                                                       \
    # Labels[N] --> opFeatureMatrixCaches ---(FeatureImage[N])---> opConcatenateFeatureImages ---(label+feature matrix)---> OpTrainFromFeatures ---(Classifier)--->

    def __init__(self, *args, **kwargs):
        print("init {}".format(self.__class__))
        super(OpTrainSupervoxelwiseClassifierBlocked, self).__init__(*args, **kwargs)
        self.progressSignal = OrderedSignal()

        self._opFeatureMatrixCaches = OperatorWrapper(OpFeatureMatrixCache, parent=self)
        self._opFeatureMatrixCaches.LabelImage.connect(self.Labels)
        self._opFeatureMatrixCaches.FeatureImage.connect(self.Images)

        # self._opConcatenateFeatureMatrices = OpConcatenateFeatureMatrices(parent=self)
        # self._opConcatenateFeatureMatrices.FeatureMatrices.connect(self._opFeatureMatrixCaches.LabelAndFeatureMatrix)
        # self._opConcatenateFeatureMatrices.ProgressSignals.connect(self._opFeatureMatrixCaches.ProgressSignal)

        self._opTrainFromFeatures = OpTrainClassifierFromFeatureVectorsAndSupervoxelMask(parent=self)
        self._opTrainFromFeatures.ClassifierFactory.connect(self.ClassifierFactory)
        self._opTrainFromFeatures.LabelAndFeatureMatrix.connect(self._opFeatureMatrixCaches.LabelAndFeatureMatrix)
        self._opTrainFromFeatures.SupervoxelSegmentation.connect(self.SupervoxelSegmentation)
        self._opTrainFromFeatures.SupervoxelFeatures.connect(self.SupervoxelFeatures)
        self._opTrainFromFeatures.SupervoxelLabels.connect(self.SupervoxelLabels)
        self._opTrainFromFeatures.Labels.connect(self.Labels)
        self._opTrainFromFeatures.Images.connect(self.Images)

        self.Classifier.connect(self._opTrainFromFeatures.Classifier)

        # Progress reporting
        # def _handleFeatureProgress(progress):
        #     # Note that these progress messages will probably appear out-of-order.
        #     # See comments in OpFeatureMatrixCache
        #     logger.debug("Training: {:02}% (Computing features)".format(int(progress)))
        #     self.progressSignal(0.8*progress)
        # self._opConcatenateFeatureMatrices.progressSignal.subscribe(_handleFeatureProgress)

        def _handleTrainingComplete():
            logger.debug("Training: 100% (Complete)")
            self.progressSignal(100.0)
        self._opTrainFromFeatures.trainingCompleteSignal.subscribe(_handleTrainingComplete)

    def cleanUp(self):
        self.progressSignal.clean()
        self.Classifier.disconnect()
        super(OpTrainSupervoxelwiseClassifierBlocked, self).cleanUp()

    def setupOutputs(self):
        pass  # Nothing to do; our output is connected to an internal operator.

    def execute(self, slot, subindex, roi, result):
        assert False, "Shouldn't get here..."

    def propagateDirty(self, slot, subindex, roi):
        pass


class OpTrainClassifierFromFeatureVectorsAndSupervoxelMask(Operator):
    ClassifierFactory = InputSlot()
    LabelAndFeatureMatrix = InputSlot(level=1)
    SupervoxelSegmentation = InputSlot(level=1)
    Labels = InputSlot(level=1)
    Images = InputSlot(level=1)
    SupervoxelFeatures = InputSlot(level=1)
    SupervoxelLabels = InputSlot(level=1)

    Classifier = OutputSlot()

    def __init__(self, *args, **kwargs):
        print("init {}".format(self.__class__))
        super(OpTrainClassifierFromFeatureVectorsAndSupervoxelMask, self).__init__(*args, **kwargs)
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
        # labels_and_features = self.LabelAndFeatureMatrix[0].value
        # featMatrix = labels_and_features[:, 1:]
        # labelsMatrix = labels_and_features[:, 0:1].astype(numpy.uint32)
        supervoxelSegmentationMatrix = self.SupervoxelSegmentation[0].value

        # if featMatrix.shape[0] < maxLabel:
        #     # If there isn't enough data for the random forest to train with, return None
        #     result[:] = None
        #     self.trainingCompleteSignal()
        #     return

        classifier_factory = self.ClassifierFactory.value
        assert issubclass(type(classifier_factory), LazyflowVectorwiseClassifierFactoryABC), \
            "Factory is of type {}, which does not satisfy the LazyflowVectorwiseClassifierFactoryABC interface."\
            "".format(type(classifier_factory))

        print("labels shape {}".format(self.Labels[0].value.shape))
        print("Image shape {}".format(self.Images[0].value.shape))
        print("ROI {}".format(roi.pprint()))
        # featMatrix = featMatrix.reshape(list(self.Images[0].value.shape[:3])+[featMatrix.shape[1]])
        # supervoxelFeatures = get_supervoxel_features(self.Images[0].value, supervoxelSegmentationMatrix)
        # supervoxelLabels = get_supervoxel_labels(self.Labels[0].value, supervoxelSegmentationMatrix)
        # indices = numpy.arange(supervoxelFeatures.shape[0])

        supervoxelFeatures = self.SupervoxelFeatures[0].value
        supervoxelLabels = self.SupervoxelLabels[0].value
        mask = numpy.where(supervoxelLabels != 0)
        supervoxelFeatures = supervoxelFeatures[mask]
        supervoxelLabels = supervoxelLabels[mask]
        # import ipdb; ipdb.set_trace()
        print("pixel labels {}".format(numpy.unique(self.Labels[0].value)))
        print("Training new classifier: {}".format(classifier_factory.description))
        # print("features before training {}".format(supervoxelFeatures))
        classifier = classifier_factory.create_and_train(supervoxelFeatures, supervoxelLabels, channel_names)
        result[0] = classifier
        if classifier is not None:
            assert issubclass(type(classifier), LazyflowVectorwiseClassifierABC), \
                "Classifier is of type {}, which does not satisfy the LazyflowVectorwiseClassifierABC interface."\
                "".format(type(classifier))

        self.trainingCompleteSignal()
        return result

    def propagateDirty(self, slot, subindex, roi):
        self.Classifier.setDirty()


class OpSupervoxelClassifierPredict(Operator):
    Image = InputSlot()
    LabelsCount = InputSlot()
    Classifier = InputSlot()
    SupervoxelSegmentation = InputSlot()

    # An entire prediction request is skipped if the mask is all zeros for the requested roi.
    # Otherwise, the request is serviced as usual and the mask is ignored.
    PredictionMask = InputSlot(optional=True)
    SupervoxelFeatures = InputSlot()

    PMaps = OutputSlot()

    def __init__(self, *args, **kwargs):
        super(OpSupervoxelClassifierPredict, self).__init__(*args, **kwargs)
        self._mode = None
        self._prediction_op = None

    def setupOutputs(self):
        # Construct an inner operator depending on the type of classifier we'll be using.
        # We don't want to access the classifier directly here because that would trigger the full computation already.
        # Instead, we require the factory to be passed along with the classifier metadata.

        try:
            classifier_factory = self.Classifier.meta.classifier_factory
        except KeyError:
            raise Exception("Classifier slot must include classifier factory as metadata.")

        if issubclass(classifier_factory.__class__, LazyflowVectorwiseClassifierFactoryABC):
            new_mode = 'vectorwise'
        # elif issubclass(classifier_factory.__class__, LazyflowPixelwiseClassifierFactoryABC):
        #     new_mode = 'pixelwise'
        else:
            raise Exception("Unknown classifier factory type: {}".format(type(classifier_factory)))

        if new_mode == self._mode:
            return

        if self._mode is not None:
            self.PMaps.disconnect()
            self._prediction_op.cleanUp()
        self._mode = new_mode

        if self._mode == 'vectorwise':
            self._prediction_op = OpSupervoxelwiseClassifierPredict(parent=self)
        elif self._mode == 'pixelwise':
            raise RuntimeError("shouldn't be here")

        self._prediction_op.PredictionMask.connect(self.PredictionMask)
        self._prediction_op.Image.connect(self.Image)
        self._prediction_op.LabelsCount.connect(self.LabelsCount)
        self._prediction_op.Classifier.connect(self.Classifier)
        self._prediction_op.SupervoxelSegmentation.connect(self.SupervoxelSegmentation)
        self._prediction_op.SupervoxelFeatures.connect(self.SupervoxelFeatures)
        self.PMaps.connect(self._prediction_op.PMaps)

    def execute(self, slot, subindex, roi, result):
        assert False, "Shouldn't get here..."

    def propagateDirty(self, slot, subindex, roi):
        if slot == self.Classifier:
            self.PMaps.setDirty()


class OpSupervoxelwiseClassifierPredict(Operator):
    Image = InputSlot()
    LabelsCount = InputSlot()
    Classifier = InputSlot()
    SupervoxelSegmentation = InputSlot()
    SupervoxelFeatures = InputSlot()


    # An entire prediction request is skipped if the mask is all zeros for the requested roi.
    # Otherwise, the request is serviced as usual and the mask is ignored.
    PredictionMask = InputSlot(optional=True)

    PMaps = OutputSlot()

    def __init__(self, *args, **kwargs):
        super(OpSupervoxelwiseClassifierPredict, self).__init__(*args, **kwargs)

        # Make sure the entire image is dirty if the prediction mask is removed.
        self.PredictionMask.notifyUnready(lambda s: self.PMaps.setDirty())

    def setupOutputs(self):
        assert self.Image.meta.getAxisKeys()[-1] == 'c'

        nlabels = max(self.LabelsCount.value, 1)  # we'll have at least 2 labels once we actually predict something
        # not setting it to 0 here is friendlier to possible downstream
        # ilastik operators, setting it to 2 causes errors in pixel classification
        #(live prediction doesn't work when only two labels are present)

        self.PMaps.meta.assignFrom(self.Image.meta)
        self.PMaps.meta.dtype = numpy.float32
        self.PMaps.meta.shape = self.Image.meta.shape[:-1]+(nlabels,)  # FIXME: This assumes that channel is the last axis
        self.PMaps.meta.drange = (0.0, 1.0)

        self.Image.meta.ideal_blockshape = self.Image.meta.shape
        self.PMaps.meta.ideal_blockshape = self.Image.meta.shape
        # ideal_blockshape = self.Image.meta.ideal_blockshape
        # if ideal_blockshape is None:
        #     ideal_blockshape = (0,) * len(self.Image.meta.shape)
        # ideal_blockshape = list(ideal_blockshape)
        # ideal_blockshape[-1] = self.PMaps.meta.shape[-1]
        # self.PMaps.meta.ideal_blockshape = tuple(ideal_blockshape)

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
        print("predicting")
        classifier = self.Classifier.value

        # Training operator may return 'None' if there was no data to train with
        skip_prediction = (classifier is None)

        # Shortcut: If the mask is totally zero, skip this request entirely
        if not skip_prediction and self.PredictionMask.ready():
            mask_roi = numpy.array((roi.start, roi.stop))
            mask_roi[:, -1:] = [[0], [1]]
            start, stop = list(map(tuple, mask_roi))
            mask = self.PredictionMask(start, stop).wait()
            skip_prediction = not numpy.any(mask)
            del mask

        if skip_prediction:
            result[:] = 0.0
            return result

        assert issubclass(type(classifier), LazyflowVectorwiseClassifierABC), \
            "Classifier is of type {}, which does not satisfy the LazyflowVectorwiseClassifierABC interface."\
            "".format(type(classifier))

        key = roi.toSlice()
        newKey = key[:-1]
        newKey += (slice(0, self.Image.meta.shape[-1], None),)

        with Timer() as features_timer:
            input_data = self.Image[newKey].wait()

        input_data = numpy.asarray(input_data, numpy.float32)

        shape = input_data.shape
        prod = numpy.prod(shape[:-1])
        features = input_data.reshape((prod, shape[-1]))
        features = self.SupervoxelFeatures.value
        # print("features before prediction {}".format(features))
        # features = get_supervoxel_features(features, self.SupervoxelSegmentation.value)

        with Timer() as prediction_timer:
            probabilities = classifier.predict_probabilities(features)
        print("probs shape: {}".format(probabilities.shape))
        # import ipdb; ipdb.set_trace()
        probabilities = slic_to_mask(self.SupervoxelSegmentation.value, probabilities).reshape(-1, probabilities.shape[-1])
        print("probs shape unslicd: {}".format(probabilities.shape))
        print("ROI {}".format(roi.pprint()))
        logger.debug("Features took {} seconds, Prediction took {} seconds for roi: {} : {}"
                     .format(features_timer.seconds(), prediction_timer.seconds(), roi.start, roi.stop))

        assert probabilities.shape[1] <= self.PMaps.meta.shape[-1], \
            "Error: Somehow the classifier has more label classes than expected:"\
            " Got {} classes, expected {} classes"\
            .format(probabilities.shape[1], self.PMaps.meta.shape[-1])

        # We're expecting a channel for each label class.
        # If we didn't provide at least one sample for each label,
        #  we may get back fewer channels.
        if probabilities.shape[1] < self.PMaps.meta.shape[-1]:
            # Copy to an array of the correct shape
            # This is slow, but it's an unusual case
            assert probabilities.shape[-1] == len(classifier.known_classes)
            full_probabilities = numpy.zeros(probabilities.shape[:-1] + (self.PMaps.meta.shape[-1],), dtype=numpy.float32)
            for i, label in enumerate(classifier.known_classes):
                full_probabilities[:, label-1] = probabilities[:, i]

            probabilities = full_probabilities

        # Reshape to image
        probabilities.shape = shape[:-1] + (self.PMaps.meta.shape[-1],)

        # Copy only the prediction channels the client requested.
        result[...] = probabilities[..., roi.start[-1]:roi.stop[-1]]
        return result

    def propagateDirty(self, slot, subindex, roi):
        if slot == self.Classifier:
            self.logger.debug("classifier changed, setting dirty")
            self.PMaps.setDirty()
        elif slot in [self.Image, self.PredictionMask, self.SupervoxelFeatures, self.SupervoxelSegmentation]:
            self.PMaps.setDirty()
