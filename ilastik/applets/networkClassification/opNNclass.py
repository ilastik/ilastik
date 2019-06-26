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
#          http://ilastik.org/license.html
###############################################################################
from functools import partial
import numpy
import vigra

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.roi import getIntersection
from lazyflow.classifiers import TikTorchLazyflowClassifierFactory
from lazyflow.operators import (
    OpMultiArraySlicer2,
    OpValueCache,
    OpBlockedArrayCache,
    OpClassifierPredict,
    OpTrainClassifierBlocked,
)
from lazyflow.operators.tiktorchClassifierOperators import OpTikTorchTrainClassifierBlocked, OpTikTorchClassifierPredict
from ilastik.utility.operatorSubView import OperatorSubView
from ilastik.utility import OpMultiLaneWrapper

from ilastik.applets.pixelClassification.opPixelClassification import OpLabelPipeline, DatasetConstraintError

from tiktorch.types import ModelState
from tiktorch.configkeys import TRAINING, NUM_ITERATIONS_MAX

import logging

logger = logging.getLogger(__name__)


class OpTiktorchFactory(Operator):
    ServerConfig = InputSlot()
    Tiktorch = OutputSlot()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__conf = None

    def setupOutputs(self):
        if self.__conf is not None:
            if self.ServerConfig.value == self.__conf:
                return

        try:
            tiktorch = TikTorchLazyflowClassifierFactory(self.ServerConfig.value)
        except Exception as e:
            logger.info("Could not statt Tiktorch server with %s", self.ServerConfig.value, exc_info=e)
            self.Tiktorch.meta.NOTREADY = True
        else:
            self.__conf = self.ServerConfig.value
            if self.Tiktorch.ready():
                # shutdown previous server
                self.Tiktorch.value.shutdown()

            self.Tiktorch.disconnect()
            self.Tiktorch.setValue(tiktorch)

    def __del__(self):
        if self.Tiktorch.ready():
            self.Tiktorch.value.shutdown()

        super().__del__()

    def cleanUp(self):
        if self.Tiktorch.ready():
            try:
                self.Tiktorch.value.shutdown()
            except Exception as e:
                logger.warning(e)

    def propagateDirty(self, slot, subindex, roi):
        # self.Tiktorch.setDirty(slice(None))
        pass


class OpModel(Operator):
    TiktorchFactory = InputSlot()  #  OpTiktorchFactory.TikTorch
    TiktorchConfig = InputSlot()
    BinaryModel = InputSlot()
    BinaryModelState = InputSlot()
    BinaryOptimizerState = InputSlot()

    TiktorchModel = OutputSlot()  #  OpTiktorchFactory.TikTorch

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._model_binary = None

    def setupOutputs(self):
        tiktorch = self.TiktorchFactory.value

        # todo: Deserialize sequences as tuple of ints, not as numpy.ndarray
        # (which is a weird, implicit default in SerialDictSlot)
        # also note: converting form numpy.int32, etc to python's int
        def make_good(bad):
            good = bad
            if isinstance(bad, dict):
                good = {}
                for key, bad_value in bad.items():
                    good[key] = make_good(bad_value)
            elif isinstance(bad, numpy.integer):
                good = int(bad)
            elif isinstance(bad, numpy.ndarray):
                good = tuple(make_good(v) for v in bad)
            return good

        tiktorch_config = make_good(self.TiktorchConfig.value)

        model_binary = bytes(self.BinaryModel.value)
        model_state = bytes(self.BinaryModelState.value)
        opt_state = bytes(self.BinaryOptimizerState.value)

        exept = tiktorch.load_model(tiktorch_config, model_binary, model_state, opt_state)
        if exept is None:
            self.TiktorchModel.setValue(tiktorch)
            try:
                projectManager = self._parent._shell.projectManager
                applet = self._parent._applets[2]
                assert applet.name == "NN Training"
                # restore labels  # todo: clean up this workaround for resetting the user label block shape
                top_group_name = applet.dataSerializers[0].topGroupName
                group_name = "LabelSets"
                label_serial_block_slot = [s for s in applet.dataSerializers[0].serialSlots if s.name == group_name][0]
                label_serial_block_slot.deserialize(projectManager.currentProjectFile[top_group_name])
            except:
                logger.debug("Could not restore labels after setting TikTorchLazyflowClassifierFactory.")
        else:
            self.TiktorchModel.meta.NOTREADY = True

    def propagateDirty(self, slot, subindex, roi):
        # self.Tiktorch.setDirty(slice(None))
        pass


class OpNNClassification(Operator):
    """
    Top-level operator for pixel classification
    """

    name = "OpNNClassification"
    category = "Top-level"

    # Graph inputs
    InputImages = InputSlot(level=1)
    ServerConfig = InputSlot()
    Checkpoints = InputSlot()

    NumClasses = InputSlot(optional=True)
    LabelInputs = InputSlot(optional=True, level=1)
    FreezePredictions = InputSlot(stype="bool", value=False, nonlane=True)
    ClassifierFactory = InputSlot()
    TiktorchConfig = InputSlot()
    BinaryModel = InputSlot()
    BinaryModelState = InputSlot()
    BinaryOptimizerState = InputSlot()
    MaskCoordinates = InputSlot(level=1, optional=True)

    Classifier = OutputSlot()
    PredictionProbabilities = OutputSlot(
        level=1
    )  # Classification predictions (via feature cache for interactive speed)
    PredictionProbabilityChannels = OutputSlot(level=2)  # Classification predictions, enumerated by channel
    CachedPredictionProbabilities = OutputSlot(level=1)
    LabelImages = OutputSlot(level=1)
    NonzeroLabelBlocks = OutputSlot(level=1)
    ValidationMask = OutputSlot(level=1)

    Halo_Size = InputSlot(value=0)
    Batch_Size = InputSlot(value=1)

    # Gui only (not part of the pipeline)
    LabelNames = OutputSlot()
    LabelColors = OutputSlot()
    PmapColors = OutputSlot()

    def setupOutputs(self):
        numClasses = len(self.opModel.TiktorchModel.value.known_classes)
        self.NumClasses.setValue(numClasses)
        self.opTrain.MaxLabel.setValue(numClasses)

        self.LabelNames.meta.dtype = object
        self.LabelNames.meta.shape = (numClasses,)
        self.LabelColors.meta.dtype = object
        self.LabelColors.meta.shape = (numClasses,)
        self.PmapColors.meta.dtype = object
        self.PmapColors.meta.shape = (numClasses,)

        if self.opBlockShape.BlockShapeInference.ready():
            self.opPredictionPipeline.BlockShape.connect(self.opBlockShape.BlockShapeInference)

    def cleanUp(self):
        try:
            self.ClassifierFactory.value.shutdown()
        except Exception as e:
            logger.warning(e)

    def __init__(self, *args, **kwargs):
        """
        Instantiate all internal operators and connect them together.
        """
        super(OpNNClassification, self).__init__(*args, **kwargs)

        # Default values for some input slots
        self.FreezePredictions.setValue(True)
        self.LabelNames.setValue([])
        self.LabelColors.setValue([])
        self.PmapColors.setValue([])

        self.Checkpoints.setValue([])
        self._binary_model = None

        # SPECIAL connection: the LabelInputs slot doesn't get it's data
        # from the InputImages slot, but it's shape must match.
        self.LabelInputs.connect(self.InputImages)

        self.opBlockShape = OpMultiLaneWrapper(OpBlockShape, parent=self)
        self.opBlockShape.RawImage.connect(self.InputImages)
        self.opBlockShape.ClassifierFactory.connect(self.ClassifierFactory)

        self.opTiktorchFactory = OpTiktorchFactory(parent=self.parent)
        self.opTiktorchFactory.ServerConfig.connect(self.ServerConfig)

        self.opValidationMask = OpMultiLaneWrapper(OpValidationMask, parent=self)
        self.opValidationMask.Coordinates.connect(self.MaskCoordinates)
        self.opValidationMask.RawImage.connect(self.InputImages)
        self.ValidationMask.connect(self.opValidationMask.Mask)

        self.opModel = OpModel(parent=self.parent)
        self.opModel.TiktorchFactory.connect(self.opTiktorchFactory.Tiktorch)
        self.opModel.TiktorchConfig.connect(self.TiktorchConfig)
        self.opModel.BinaryModel.connect(self.BinaryModel)
        self.opModel.BinaryModelState.connect(self.BinaryModelState)
        self.opModel.BinaryOptimizerState.connect(self.BinaryOptimizerState)

        self.ClassifierFactory.connect(self.opModel.TiktorchModel)

        # Hook up Labeling Pipeline
        self.opLabelPipeline = OpMultiLaneWrapper(OpLabelPipeline, parent=self, broadcastingSlotNames=["DeleteLabel"])
        self.opLabelPipeline.RawImage.connect(self.InputImages)
        self.opLabelPipeline.LabelInput.connect(self.LabelInputs)
        self.opLabelPipeline.DeleteLabel.setValue(-1)
        self.opLabelPipeline.BlockShape.connect(self.opBlockShape.BlockShapeTrain)
        self.LabelImages.connect(self.opLabelPipeline.Output)
        self.NonzeroLabelBlocks.connect(self.opLabelPipeline.nonzeroBlocks)

        # TRAINING OPERATOR
        self.opTrain = OpTikTorchTrainClassifierBlocked(parent=self)
        self.opTrain.ClassifierFactory.connect(self.ClassifierFactory)
        self.opTrain.Labels.connect(self.opLabelPipeline.Output)
        self.opTrain.Images.connect(self.InputImages)
        self.opTrain.nonzeroLabelBlocks.connect(self.opLabelPipeline.nonzeroBlocks)
        self.opTrain.ValidationCoord.connect(self.MaskCoordinates)

        # CLASSIFIER CACHE
        # This cache stores exactly one object: the classifier itself.
        self.classifier_cache = OpValueCache(parent=self)
        self.classifier_cache.name = "OpNetworkClassification.classifier_cache"
        self.classifier_cache.inputs["Input"].connect(self.opTrain.Classifier)
        self.classifier_cache.inputs["fixAtCurrent"].connect(self.FreezePredictions)
        self.Classifier.connect(self.classifier_cache.Output)

        # Hook up the prediction pipeline inputs
        self.opPredictionPipeline = OpMultiLaneWrapper(OpPredictionPipeline, parent=self)
        self.opPredictionPipeline.RawImage.connect(self.InputImages)
        self.opPredictionPipeline.Classifier.connect(self.classifier_cache.Output)
        self.opPredictionPipeline.NumClasses.connect(self.NumClasses)
        self.opPredictionPipeline.FreezePredictions.connect(self.FreezePredictions)

        self.PredictionProbabilities.connect(self.opPredictionPipeline.PredictionProbabilities)
        self.CachedPredictionProbabilities.connect(self.opPredictionPipeline.CachedPredictionProbabilities)
        self.PredictionProbabilityChannels.connect(self.opPredictionPipeline.PredictionProbabilityChannels)

        def inputResizeHandler(slot, oldsize, newsize):
            if newsize == 0:
                self.LabelImages.resize(0)
                self.NonzeroLabelBlocks.resize(0)
                self.PredictionProbabilities.resize(0)
                self.CachedPredictionProbabilities.resize(0)

        self.InputImages.notifyResized(inputResizeHandler)

        # Debug assertions: Check to make sure the non-wrapped operators stayed that way.
        assert self.opTrain.Images.operator == self.opTrain

        def handleNewInputImage(multislot, index, *args):
            def handleInputReady(slot):
                self._checkConstraints(index)
                self.setupCaches(multislot.index(slot))

            multislot[index].notifyReady(handleInputReady)

        self.InputImages.notifyInserted(handleNewInputImage)

        # All input multi-slots should be kept in sync
        # Output multi-slots will auto-sync via the graph
        multiInputs = [s for s in list(self.inputs.values()) if s.level >= 1]
        for s1 in multiInputs:
            for s2 in multiInputs:
                if s1 != s2:

                    def insertSlot(a, b, position, finalsize):
                        a.insertSlot(position, finalsize)

                    s1.notifyInserted(partial(insertSlot, s2))

                    def removeSlot(a, b, position, finalsize):
                        a.removeSlot(position, finalsize)

                    s1.notifyRemoved(partial(removeSlot, s2))

    def set_model_state(self, model_state: ModelState):
        config = self.TiktorchConfig.value
        config[TRAINING][NUM_ITERATIONS_MAX] = model_state.num_iterations_max
        model = self.BinaryModel.value
        self.set_classifier(config, model, model_state.model_state, model_state.optimizer_state)

    def set_classifier(
        self, tiktorch_config: dict, model_file: bytes, model_state: bytes, optimizer_state: bytes
    ) -> bool:
        # self.TiktorchConfig.disconnect()  # do not create TiktorchClassifierFactory with invalid intermediate settings
        # self.ClassifierFactory.disconnect()
        # self.FreezePredictions.setValue(False)
        self.BinaryModel.setValue(model_file)
        self.BinaryModelState.setValue(model_state)
        self.BinaryOptimizerState.setValue(optimizer_state)
        # now all non-server settings are up to date...
        self.TiktorchConfig.setValue(tiktorch_config)  # ...setupOutputs can initialize a tiktorchClassifierFactory
        return self.opModel.TiktorchModel.ready()

    def update_config(self, partial_config: dict):
        self.ClassifierFactory.meta.hparams = partial_config

        def _send_hparams(slot):
            classifierFactory = self.ClassifierFactory[:].wait()[0]
            classifierFactory.update_config(self.ClassifierFactory.meta.hparams)

        if not self.ClassifierFactory.ready():
            self.ClassifierFactory.notifyReady(_send_hparams)
        else:
            classifierFactory = self.ClassifierFactory[:].wait()[0]
            classifierFactory.update_config(partial_config)

    def setupCaches(self, imageIndex):
        numImages = len(self.InputImages)
        inputSlot = self.InputImages[imageIndex]

        self.LabelInputs.resize(numImages)

        # Special case: We have to set up the shape of our label *input* according to our image input shape
        shapeList = list(self.InputImages[imageIndex].meta.shape)
        try:
            channelIndex = self.InputImages[imageIndex].meta.axistags.index("c")
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

        if "t" in thisLaneTaggedShape:
            del thisLaneTaggedShape["t"]
        if "t" in validShape:
            del validShape["t"]

        if validShape["c"] != thisLaneTaggedShape["c"]:
            raise DatasetConstraintError(
                "Pixel Classification with CNNs",
                "All input images must have the same number of channels.  "
                "Your new image has {} channel(s), but your other images have {} channel(s).".format(
                    thisLaneTaggedShape["c"], validShape["c"]
                ),
            )

        if len(validShape) != len(thisLaneTaggedShape):
            raise DatasetConstraintError(
                "Pixel Classification with CNNs",
                "All input images must have the same dimensionality.  "
                "Your new image has {} dimensions (including channel), but your other images have {} dimensions.".format(
                    len(thisLaneTaggedShape), len(validShape)
                ),
            )

    def setInSlot(self, slot, subindex, roi, value):
        # Nothing to do here: All inputs that support __setitem__
        #   are directly connected to internal operators.
        pass

    def propagateDirty(self, slot, subindex, roi):
        # Nothing to do here: All outputs are directly connected to
        #  internal operators that handle their own dirty propagation.
        self.PredictionProbabilityChannels.setDirty(slice(None))

    def addLane(self, laneIndex):
        numLanes = len(self.InputImages)
        assert numLanes == laneIndex, f"Image lanes must be appended. {numLanes}, {laneIndex})"
        self.InputImages.resize(numLanes + 1)

    def removeLane(self, laneIndex, finalLength):
        self.InputImages.removeSlot(laneIndex, finalLength)

    def getLane(self, laneIndex):
        return OperatorSubView(self, laneIndex)

    def importLabels(self, laneIndex, slot):
        # Load the data into the cache
        new_max = self.getLane(laneIndex).opLabelPipeline.opLabelArray.ingestData(slot)

        # Add to the list of label names if there's a new max label
        old_names = self.LabelNames.value
        old_max = len(old_names)
        if new_max > old_max:
            new_names = old_names + ["Label {}".format(x) for x in range(old_max + 1, new_max + 1)]
            self.LabelNames.setValue(new_names)

            # Make some default colors, too
            # FIXME: take the colors from default16_new
            from volumina import colortables

            default_colors = colortables.default16_new

            label_colors = self.LabelColors.value
            pmap_colors = self.PmapColors.value

            self.LabelColors.setValue(label_colors + default_colors[old_max:new_max])
            self.PmapColors.setValue(pmap_colors + default_colors[old_max:new_max])

    def mergeLabels(self, from_label, into_label):
        for laneIndex in range(len(self.InputImages)):
            self.getLane(laneIndex).opLabelPipeline.opLabelArray.mergeLabels(from_label, into_label)

    def clearLabel(self, label_value):
        for laneIndex in range(len(self.InputImages)):
            self.getLane(laneIndex).opLabelPipeline.opLabelArray.clearLabel(label_value)


class OpBlockShape(Operator):
    RawImage = InputSlot()
    ClassifierFactory = InputSlot()

    BlockShapeTrain = OutputSlot()
    BlockShapeInference = OutputSlot()

    def __init__(self, *args, **kwargs):
        super(OpBlockShape, self).__init__(*args, **kwargs)

    def setupOutputs(self):
        self.BlockShapeTrain.setValue(self.setup_train())
        self.BlockShapeInference.setValue(self.setup_inference())

    def setup_train(self):
        tikmodel = self.ClassifierFactory.value
        training_shape = tikmodel.training_shape
        halo = tikmodel.halo
        # total halo = 2 * halo per axis
        total_halo = 2 * numpy.array(halo)
        shrinkage = tikmodel.shrinkage
        shrunk_training_shape_wo_halo = numpy.array(training_shape) - numpy.array(shrinkage) - total_halo
        blockDims = dict(zip("tczyx", shrunk_training_shape_wo_halo))
        blockDims["c"] = 9999  # always request all channels
        axisOrder = self.RawImage.meta.getAxisKeys()
        ret = tuple(blockDims[a] for a in axisOrder)
        logger.debug(
            "got training shape %s and axisorder %s => Set BlockShapeTrain to %s", training_shape, axisOrder, ret
        )
        return ret

    def setup_inference(self):
        tikmodel = self.ClassifierFactory.value
        valid_tczyx_shapes = tikmodel.valid_shapes
        halo = tikmodel.halo  # total halo = 2 * halo per axis
        total_halo = 2 * numpy.array(halo)
        shrinkage = tikmodel.shrinkage
        shrunk_valid_tczyx_shapes_wo_halo = [
            numpy.array(shape) - numpy.array(shrinkage) - total_halo for shape in valid_tczyx_shapes
        ]
        largest_valid_shape = shrunk_valid_tczyx_shapes_wo_halo[-1]

        blockDims = dict(zip("tczyx", largest_valid_shape))
        blockDims["c"] = 9999  # always request all channels
        axisOrder = self.RawImage.meta.getAxisKeys()
        ret = tuple(blockDims[a] for a in axisOrder)
        logger.debug(
            "got largest valid shape %s and axis order %s => Set BlockShapeInference to %s",
            largest_valid_shape,
            axisOrder,
            ret,
        )
        return ret

    def execute(self, slot, subindex, roi, result):
        pass

    def propagateDirty(self, slot, subindex, roi):
        self.BlockShapeTrain.setDirty()
        self.BlockShapeInference.setDirty()


class OpPredictionPipeline(Operator):
    RawImage = InputSlot()
    Classifier = InputSlot()
    NumClasses = InputSlot()
    FreezePredictions = InputSlot()
    BlockShape = InputSlot()

    PredictionProbabilities = OutputSlot()
    CachedPredictionProbabilities = OutputSlot()
    PredictionProbabilityChannels = OutputSlot(level=1)

    def __init__(self, *args, **kwargs):
        super(OpPredictionPipeline, self).__init__(*args, **kwargs)

        self.cacheless_predict = OpTikTorchClassifierPredict(parent=self)
        self.cacheless_predict.name = "OpClassifierPredict (Cacheless Path)"
        self.cacheless_predict.Classifier.connect(self.Classifier)
        self.cacheless_predict.Image.connect(self.RawImage)  # <--- Not from cache
        self.cacheless_predict.LabelsCount.connect(self.NumClasses)

        self.predict = OpTikTorchClassifierPredict(parent=self)
        self.predict.name = "OpClassifierPredict"
        self.predict.Classifier.connect(self.Classifier)
        self.predict.Image.connect(self.RawImage)
        self.predict.LabelsCount.connect(self.NumClasses)
        self.predict.BlockShape.connect(self.BlockShape)
        self.PredictionProbabilities.connect(self.predict.PMaps)

        self.prediction_cache = OpBlockedArrayCache(parent=self)
        self.prediction_cache.name = "BlockedArrayCache"
        self.prediction_cache.inputs["fixAtCurrent"].connect(self.FreezePredictions)
        self.prediction_cache.BlockShape.connect(self.BlockShape)
        self.prediction_cache.inputs["Input"].connect(self.predict.PMaps)
        self.CachedPredictionProbabilities.connect(self.prediction_cache.Output)

        self.opPredictionSlicer = OpMultiArraySlicer2(parent=self)
        self.opPredictionSlicer.name = "opPredictionSlicer"
        self.opPredictionSlicer.Input.connect(self.prediction_cache.Output)
        self.opPredictionSlicer.AxisFlag.setValue("c")
        self.PredictionProbabilityChannels.connect(self.opPredictionSlicer.Slices)

    def execute(self, slot, subindex, roi, result):
        assert False, "Shouldn't get here.  Output is assigned a value in setupOutputs()"

    def propagateDirty(self, slot, subindex, roi):
        # Our output changes when the input changed shape, not when it becomes dirty.
        pass

class OpValidationMask(Operator):
    Coordinates = InputSlot()
    RawImage = InputSlot()
    Mask = OutputSlot()

    def __init__(self, *args, **kwargs):
        super(OpValidationMask, self).__init__(*args, **kwargs)

        self.coord_roi = slice((0,),(0,))

    def get_coordroi(self, coord_dict):
        z = coord_dict['z_coord']
        y = coord_dict['y_coord']
        x = coord_dict['x_coord']

        return slice((z[0], y[0], x[0], 0), (z[1], y[1], x[1], 1))


    def setupOutputs(self):
        self.Mask.meta.dtype = numpy.uint8
        self.Mask.meta.axistags = vigra.defaultAxistags('zyxc')
        self.Mask.meta.shape = self.RawImage.meta.shape

    def execute(self, slot, subindex, roi, result):
        assert slot == self.Mask
        result[:] = 0

        self.coord_roi = self.get_coordroi(self.Coordinates.value)

        intsec = getIntersection((roi.start, roi.stop),
                       (self.coord_roi.start, self.coord_roi.stop),
                        assertIntersect=False)

        if intsec is not None:
            result[:, intsec[0][1]:intsec[1][1], intsec[0][2]:intsec[1][2], :] = 1

        return result

    def propagateDirty(self, slot, subindex, roi):
        pass




     