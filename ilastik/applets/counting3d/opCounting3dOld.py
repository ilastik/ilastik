import numpy
import h5py
import vigra
import vigra.analysis
import copy
from collections import defaultdict

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.stype import Opaque
from lazyflow.rtype import Everything, SubRegion, List
from lazyflow.roi import roiToSlice, sliceToRoi
from lazyflow.operators.ioOperators.opStreamingHdf5Reader import OpStreamingHdf5Reader
from lazyflow.operators.ioOperators.opInputDataReader import OpInputDataReader
from lazyflow.operators import OperatorWrapper, OpBlockedSparseLabelArray, OpValueCache, \
OpMultiArraySlicer2, OpSlicedBlockedArrayCache, OpPrecomputedInput
from lazyflow.request import Request
import lazyflow.request
from functools import partial

from ilastik.applets.pixelClassification.opPixelClassification import OpShapeReader, OpMaxValue
from ilastik.utility import OperatorSubView, MultiLaneOperatorABC, OpMultiLaneWrapper
from ilastik.utility.mode import mode

from ilastik.applets.objectExtraction import config

#from sklearn.svm import SVR2 
from countingsvr import SVR

from lazyflow.operators import OpMultiArrayMerger, OpMultiArraySlicer2,\
OpPixelOperator, OpValueCache 
import lazyflow.request
from ilastik.utility import OpMultiLaneWrapper, MultiLaneOperatorABC
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from learningtocount3d import Counter, StatFeats
import math
from sitecustomize import debug_trace
import threading

# Right now we only support having two types of objects.
_MAXLABELS = 2

# WARNING: since we assume the input image is binary, we also assume
# that it only has one channel. If there are multiple channels, only
# features from the first channel are used in this operater.

class OpMatchDimensions(Operator):
    name = "OpMatchDimensions"
    inputSlots = [InputSlot("Input"), InputSlot("MatchTo", optional = True),
                  InputSlot("AxisFlag", optional = True)]
    outputSlots = [OutputSlot("Output")]

    def setupOutputs(self):
        if self.MatchTo.ready() and self.Input.ready():
            self.Output.meta.assignFrom(self.MatchTo.meta)
            self.shortAxisTags = [x for x in  
                             self.Input.meta.getTaggedShape().keys() if
                             x in self.MatchTo.meta.getTaggedShape().keys()] 
        #self.shortShape = tuple((value for (key, value) in self.shortMeta))
        elif self.AxisFlag.ready() and self.Input.ready():
            self.shortAxisTags = [x for x in  
                             self.Input.meta.getTaggedShape().keys() if
                             x in self.AxisFlag.value] 
            self.shortTable = tuple(self.Input.meta.getTaggedShape().keys().index(key) for key in
                   self.shortAxisTags)
            self.Output.meta.assignFrom(self.Input.meta)

            self.Output.meta.shape = tuple(self.Output.meta.shape[i] for i in
                                      self.shortTable)
            import vigra
            t = vigra.AxisTags()
            conversion = {
                'c' : vigra.AxisType(1),
                'x' : vigra.AxisType(2),
                'y' : vigra.AxisType(2),
                'z' : vigra.AxisType(2),
                't' : vigra.AxisType(8)
            }
            for k in self.Input.meta.getTaggedShape().keys():
                if k in self.AxisFlag.value:

                    t.append(vigra.AxisInfo(k, conversion[k]))
            self.Output.meta.axistags = t 
        else:
            self.Output.meta.assignFrom(self.Input.meta)
            self.shortAxisTags = self.Input.meta.getTaggedShape().keys()

        
        
        self.shortTable = tuple(self.Input.meta.getTaggedShape().keys().index(key) for key in
                   self.shortAxisTags)


    def execute(self, slot, subindex, roi, result):
        key = roiToSlice(roi.start, roi.stop)
        #writeKey = [slice(None) for k in key]
        longKey = [slice(None) for k in self.Input.meta.getTaggedShape().keys()]
        for i,k in enumerate(self.shortTable):
            longKey[k] = key[i]
        ttt = self.Input[longKey].allocate().wait()
        #debug_trace()
        return ttt.reshape(roi.stop - roi.start)

    def propagateDirty(self, slot, subindex, roi):
        if slot is self.MatchTo:
            return
        key = roi.toSlice()
        #debug_trace()
        shortKey = tuple(key[i] for i in self.shortTable)
        self.outputs["Output"].setDirty(shortKey)
        


class OpVolumeOperator(Operator):
    name = "OpVolumeOperator"
    description = "Do Operations involving the whole volume"
    inputSlots = [InputSlot("Input"), InputSlot("Function")]
    outputSlots = [OutputSlot("Output")]

    def setupOutputs(self):
        print "setupOutputsVolume"
        testInput = numpy.ones((3,3))
        testFun = self.Function.value
        testOutput = testFun(testInput)

        self.outputs["Output"].meta.dtype = testOutput.dtype
        self.outputs["Output"].meta.shape = (1,)
        self.outputs["Output"].setDirty((slice(0,1,None),))
        self.cache = None
        self._lock = threading.Lock()


    def execute(self, slot, subindex, roi, result):
        print "ExecuteVolume"
        with self._lock:
            if self.cache is None:
                fun = self.inputs["Function"].value
                data = self.inputs["Input"][:].allocate().wait()
                self.cache = [fun(data)]
            return self.cache

    def propagateDirty(self, slot, subindex, roi):
        print "propagateVolume"
        key = roi.toSlice()
        if slot == self.Input or slot == self.Function:
            self.outputs["Output"].setDirty( slice(None) )
        self.cache = None

class OpPixelBinaryOperator(Operator):
    name = "OpPixelBinaryOperator"
    description = "simple operations with "
    inputSlots   = [InputSlot("Input"), InputSlot("Mask"),
                    InputSlot("BinaryFunction"), InputSlot("FunctionParameters",
                                                          optional=True)]
    outputSlots = [OutputSlot("Output")]

    def setupOutputs(self):
        self.function = self.inputs["BinaryFunction"].value

        self.Output.meta.shape = self.Input.meta.shape
        self.Output.meta.axistags = self.Input.meta.axistags
        self.Output.meta.dtype = self.Input.meta.dtype
        self.shortMeta = [(key, value) for (key, value) in 
                         set(self.Input.meta.getTaggedShape().items()) &
                         set(self.Mask.meta.getTaggedShape().items())
                         ]
        self.shortShape = tuple((value for (key, value) in self.shortMeta))
        self.divisor = tuple(x/float(y) for x,y in zip( 
            self.inputs["Input"].meta.shape, self.inputs["Mask"].meta.shape)
        )
        try:
            numpy.broadcast(self.Input, self.Mask)
            print("blub")
        except:
            raise Exception("The shape of BroadcastInput and Input have to be\
                            compatible in a broadcast-sense")
        
    def execute(self, slot, subindex, roi, result):
        key = roiToSlice(roi.start,roi.stop)
        #print key
        print "binaryexecute"
        matrix = self.inputs["Input"][key].allocate().wait()
        shortkey = tuple(slice(int(math.floor(s.start/d)),
                               int(math.ceil(s.stop/d)))
                         for s,d in
                        zip(key, self.divisor))
        broadcast = self.inputs["Mask"][shortkey].allocate().wait()
        fun = self.inputs["BinaryFunction"].value
        param = None
        if self.inputs["FunctionParameters"].connected():
            param = self.inputs["FunctionParameters"].value
            return fun(matrix,broadcast,param)[:]

        print "binaryexecuteEnd"
        return fun(matrix,broadcast)[:]

    def propagateDirty(self, slot, subindex, roi):
        try:
            if slot == self.Input:
                key = roi.toSlice()
                self.outputs["Output"].setDirty(key)
            elif slot == self.Mask:
                key = roi.toSlice()
                self.outputs["Output"].setDirty(key)
            elif slot == self.BinaryFunction:
                self.outputs["Output"].setDirty( slice(None) )
            elif slot == self.FunctionParameters:
                self.outputs["Output"].setDirty( slice(None) )
        except:
            debug_trace()

class OpTrainCounter(Operator):
    name = "OpCounter"
    description = "blub"
    inputSlots   = [InputSlot("Images", level = 1),InputSlot("Dots", level = 1),
                    InputSlot("fixRegressor",
                                                     stype="bool"),
                   InputSlot("Sigma",stype="float")]
    outputSlots = [OutputSlot("Output")]

    
    def __init__(self, *args, **kwargs):
        super(OpTrainCounter, self).__init__(*args, **kwargs)
        self._patchsize = (7,7,3)
        self.cache = None
        self._lock = threading.Lock()

        self.ImageShortener = OpMultiLaneWrapper(OpMatchDimensions, parent=self)
        self.ImageShortener.Input.connect(self.Images)
        self.ImageShortener.AxisFlag.setValue(["x", "y", "z", "c"])
        
        self.LabelShortener = OpMultiLaneWrapper(OpMatchDimensions, parent=self)
        self.LabelShortener.Input.connect(self.Dots)
        self.LabelShortener.AxisFlag.setValue(["x", "y", "z"])

    def setupOutputs(self):
        print "blubsetupOutputs"
        if self.inputs["fixRegressor"].value == False:
            print "falseSetupOutputs"
            self.outputs["Output"].meta.dtype = object
            self.outputs["Output"].meta.shape = (1,)
            self.outputs["Output"].setDirty((slice(0,1,None),))
        #self.function = self.inputs["BinaryFunction"].value

        #self.Output.meta.shape = self.PredictionSlot.meta.shape
        #self.Output.meta.axistags = self.PredictionSlot.meta.axistags
        #self.Output.meta.dtype = self.PredictionSlot.meta.dtype
        
    def execute(self, slot, subindex, roi, result):
        #key = roiToSlice(roi.start,roi.stop)
        with self._lock:
            if self.cache is None:
                self.cache = [Counter(patch_size=self._patchsize,
                                      sigma=self.Sigma.value,
                              regressor=RandomForestRegressor(n_jobs=4),
                              classifier=RandomForestClassifier(n_jobs=4), feats =
                              StatFeats(), frac_pos = 0.5)]
                #print key

                dots = [dot[:].allocate().wait() for dot in
                        self.LabelShortener.Output]
                dots = [numpy.where(dot == 2, 1, 0) for dot in dots]
                imgs = [vol[:].allocate().wait() for vol in self.ImageShortener.Output]
                self.cache[0].fit(imgs, dots, npatches=500)
            return self.cache

    def propagateDirty(self, slot, subindex, roi):
        with self._lock:
            if slot is not self.inputs["fixRegressor"] and self.inputs["fixRegressor"].value == False:
                print "propagateDirty"

                self.outputs["Output"].setDirty((slice(0,1,None),))
                self.cache = None

class OpTrainCounter2(Operator):
    name = "OpCounter"
    description = "blub"
    inputSlots   = [InputSlot("Images", level = 1),InputSlot("Dots", level = 1),
                    InputSlot("fixRegressor",
                                                     stype="bool"),
                   InputSlot("Sigma",stype="float"), InputSlot("UnderMult",
                                                               stype="float"),
                   InputSlot("OverMult", stype="float"),
                    InputSlot("SelectedOption", stype="object")]
    outputSlots = [OutputSlot("Output")]
    
    def __init__(self, *args, **kwargs):
        super(OpTrainCounter2, self).__init__(*args, **kwargs)
        self.cache = None
        self._lock = threading.Lock()

        self.ImageShortener = OpMultiLaneWrapper(OpMatchDimensions, parent=self)
        self.ImageShortener.Input.connect(self.Images)
        self.ImageShortener.AxisFlag.setValue(["x", "y", "z", "c"])
        
        self.LabelShortener = OpMultiLaneWrapper(OpMatchDimensions, parent=self)
        self.LabelShortener.Input.connect(self.Dots)
        self.LabelShortener.AxisFlag.setValue(["x", "y", "z"])

    def setupOutputs(self):

        if self.inputs["fixRegressor"].value == False:
            print "falseSetupOutputs"
            self.outputs["Output"].meta.dtype = object
            self.outputs["Output"].meta.shape = (1,)
            self.outputs["Output"].setDirty((slice(0,1,None),))
        #self.function = self.inputs["BinaryFunction"].value

        #self.Output.meta.shape = self.PredictionSlot.meta.shape
        #self.Output.meta.axistags = self.PredictionSlot.meta.axistags
        #self.Output.meta.dtype = self.PredictionSlot.meta.dtype
        
    def execute(self, slot, subindex, roi, result):
        #key = roiToSlice(roi.start,roi.stop)
        debug_trace()
        with self._lock:

            if self.cache is None:
                print "bla", self.SelectedOption.value
                self.cache = len(self.LabelShortener.Output) * [SVR(underMult =self.UnderMult.value, overMult =
                     self.OverMult.value, limitDensity=False,
                                                                    **self.SelectedOption.value)]
                #print key

                dots = [dot[:].allocate().wait() for dot in
                        self.LabelShortener.Output]
                imgs = [vol[:].allocate().wait() for vol in self.ImageShortener.Output]
                for nr, svr, img, dot in zip(range(len(self.cache)), self.cache, imgs, dots):
                    svr.fit(img, dot, sigma = self.Sigma.value, normalize =
                            True, epsilon = 0)

            return self.cache

    def propagateDirty(self, slot, subindex, roi):
        with self._lock:
            if slot is not self.inputs["fixRegressor"] and self.inputs["fixRegressor"].value == False:
                print "propagateDirty"

                self.cache = None
                self.Output.setDirty((slice(0,1,None),))

class OpPredictCounter(Operator):
    name = "PredictCounter"
    Regressor = InputSlot()
    Image    = InputSlot()
    #DummySlot = InputSlot()
    Output = OutputSlot()

#def __init__(self, *args, **kwargs):
#    super(OpPredictCounter, self).__init__(*args, **kwargs)
        
    def __init__(self, *args, **kwargs):
        super(OpPredictCounter, self).__init__(*args, **kwargs)
        self._lock = threading.Lock()
        self.cache = None

        self.ImageShortener = OpMatchDimensions(graph = self.graph, parent =
                                                self)
        self.ImageShortener.Input.connect(self.Image)
        self.ImageShortener.AxisFlag.setValue(["x", "y", "z", "c"])

    def setupOutputs(self):
        import copy
        #self.outputs["Output"].resize(len(self.inputs["Images"]))
        #for image, output in zip(self.inputs["Images"], self.outputs["Output"]):
        image = self.inputs["Image"]
        output = self.outputs["Output"]
        output.meta.dtype = numpy.float64
        output.meta.shape = image.meta.shape[:-1]
        output.meta.axistags = copy.deepcopy(image.meta.axistags)
        output.meta.axistags.dropChannelAxis()

    def execute(self, slot, subindex, roi, result):
        print "executePredict"
        with self._lock:
            print "executePredictLock"

            if self.cache is None:
                regressor = self.inputs["Regressor"][:].wait()
                if regressor is None:
                    return numpy.zeros(numpy.subtract(roi.stop, roi.start),
                                       dtype=numpy.float32)[...]
                img = self.ImageShortener.Output[:].wait()
                print "noCache execute"

                #sitecustomize.debug_trace()
                self.cache = regressor[0].predict(img, mode = "dense",
                            skip_size=1, collapse=False)
                
                self.cache = self.cache.reshape(self.outputs["Output"].meta.shape)
                #sitecustomize.debug_trace()
            return self.cache[roiToSlice(roi.start, roi.stop)]

        #self.outputs["Output"].meta.= self.Image.meta.shape[:-1]
    def propagateDirty(self, slot, subindex, roi):
        self.cache = None
        self.outputs["Output"].setDirty(slice( None ))
        print "propagatePrediction"
        #key = roi.toSlice()
        #if slot == self.inputs["Regressor"]:
        #    logger.debug("OpPredictRandomForest: Classifier changed, setting dirty")
        #    if self.LabelsCount.ready() and self.LabelsCount.value > 0:
        #        self.outputs["Output"].setDirty(slice(None,None,None))
        #elif slot == self.inputs["Image"]:
        #    nlabels=self.inputs["LabelsCount"].value
        #    if nlabels > 0:
        #        self.outputs["PMaps"].setDirty(key[:-1] + (slice(0,nlabels,None),))
        #elif slot == self.inputs["LabelsCount"]:
        #    # When the labels count changes, we must resize the output
        #    if self.configured():
        #        # FIXME: It's ugly that we call the 'private' _setupOutputs() function here,
        #        #  but the output shape needs to change when this input becomes dirty,
        #        #  and the output change needs to be propagated to the rest of the graph.
        #        self._setupOutputs()
        #    self.outputs["PMaps"].setDirty(slice(None,None,None))

class OpPredictCounter2(Operator):
    name = "PredictCounter"
    Regressor = InputSlot()
    Image    = InputSlot()
    #DummySlot = InputSlot()
    Output = OutputSlot()

#def __init__(self, *args, **kwargs):
#    super(OpPredictCounter, self).__init__(*args, **kwargs)
        
    def __init__(self, *args, **kwargs):
        super(OpPredictCounter2, self).__init__(*args, **kwargs)
        self._lock = threading.Lock()
        self.cache = None

        self.ImageShortener = OpMatchDimensions(graph = self.graph, parent =
                                                self)
        self.ImageShortener.Input.connect(self.Image)
        self.ImageShortener.AxisFlag.setValue(["x", "y", "z", "c"])

    def setupOutputs(self):
        import copy
        #self.outputs["Output"].resize(len(self.inputs["Images"]))
        #for image, output in zip(self.inputs["Images"], self.outputs["Output"]):
        image = self.inputs["Image"]
        output = self.outputs["Output"]
        output.meta.dtype = numpy.float64
        output.meta.shape = image.meta.shape[:-1]
        output.meta.axistags = copy.deepcopy(image.meta.axistags)
        output.meta.axistags.dropChannelAxis()

    def execute(self, slot, subindex, roi, result):
        print "executePredict"
        with self._lock:
            print "executePredictLock"
            if self.cache is None:
                regressor = self.inputs["Regressor"][:].wait()
                if regressor is None:
                    return numpy.zeros(numpy.subtract(roi.stop, roi.start),
                                       dtype=numpy.float32)[...]
                img = self.ImageShortener.Output[:].allocate().wait()
                print "noCache execute"

                #sitecustomize.debug_trace()
                self.cache = regressor[0].predict(img,normalize=True)
                
                self.cache = self.cache.reshape(self.outputs["Output"].meta.shape)
                #sitecustomize.debug_trace()
            return self.cache[roiToSlice(roi.start, roi.stop)]

        #self.outputs["Output"].meta.= self.Image.meta.shape[:-1]
    def propagateDirty(self, slot, subindex, roi):
        self.cache = None
        self.outputs["Output"].setDirty(slice( None ))
        print "propagatePrediction"


class OpCounting3d(Operator, MultiLaneOperatorABC):
    name = "OpCounting3d"
    category = "Top-level"

    ###############
    # Input slots #
    ###############


    InputImages = InputSlot(level=1) # for visualization
    LabelInputs = InputSlot(optional = True, level=1) # Input for providing label data from an external source
    LabelsAllowedFlags = InputSlot(stype='bool', level=1) # Specifies which images are permitted to be labeled 
    
    FeatureImages = InputSlot(level=1) # Computed feature images (each channel is a different feature)
    CachedFeatureImages = InputSlot(level=1) # Cached feature data.

    FreezePredictions = InputSlot(stype='bool')
    
    PredictionsFromDisk = InputSlot(optional=True, level=1)
    

    #BinaryImages = InputSlot(level=1) # for visualization
    #SegmentationImages = InputSlot(level=1)
    #UserLabels = InputSlot(level=1)
    #ForegroundLabels = InputSlot(level=1)
    #ModifiedFeatureData = OutputSlot(level=1)
    Sigma = InputSlot(stype='object')
    UnderMult = InputSlot(stype='float')
    OverMult = InputSlot(stype='float')
    #FilteredFeatureData = OutputSlot(level=1)
    #FilteredRaw = OutputSlot(level = 1)
    SelectedOption = InputSlot(stype = 'object')
    #ObjectFeatures = InputSlot(rtype=List, level=1)
    #LabelsAllowedFlags = InputSlot(stype='bool', level=1)


    #LabelInputs = InputSlot(stype=Opaque, rtype=List, optional=True, level=1)
    #FreezePredictions = InputSlot(stype='bool')

    #labelEraserValue = InputSlot(stype='bool', optional=True)
    #labelDelete = InputSlot(stype='bool', optional=True)

    #maxLabelValue = InputSlot(optional=True)
    #labelsAllowed = InputSlot(stype='bool', optional=True)
    #NumLabels = InputSlot(optional=True)
    ################
    # Output slots #
    ################
    #NumLabels = OutputSlot()
    Regressor = OutputSlot()
    Density = OutputSlot(level=1)
    MaxLabelValue = OutputSlot()
    OutputSum = OutputSlot(level=1)
    #PredictionImages = OutputSlot(level=1)
    #SegmentationImagesOut = OutputSlot(level=1)

    PredictionProbabilities = OutputSlot(level=1) # Classification predictions (via feature cache for interactive speed)

    LabelImages = OutputSlot(level=1) # Labels from the user
    
    NonzeroLabelBlocks = OutputSlot(level=1) # A list if slices that contain non-zero label values

    CachedPredictionProbabilities = OutputSlot(level=1) # Classification predictions (via feature cache AND prediction cache)

    # TODO: not actually used
    #Eraser = OutputSlot()
    #DeleteLabel = OutputSlot()

    def __init__(self, *args, **kwargs):
        super(OpCounting3d, self).__init__(*args, **kwargs)

        # internal operators
        opkwargs = dict(parent=self)
        #self.maxLabelValue.setValue(2)

        def handleNewInputImage(multislot, index, *args):
            def handleInputReady(slot):
                self.setupCaches(multislot.index(slot))
            multislot[index].notifyReady(handleInputReady)

        self.FreezePredictions.setValue(True)



#        self.opMatchDimensions = OpMultiLaneWrapper(OpMatchDimensions, parent=                                                   self)
#        self.opMatchDimensions.Input.connect(self.ForegroundLabels)
#        self.opMatchDimensions.MatchTo.connect(self.UserLabels)
#        self.ForegroundLabelsShort = self.opMatchDimensions.Output
#        self.opFilterNonLabeled= OpMultiLaneWrapper(OpFilterNonLabeled, parent=self)
#        self.opFilterNonLabeled.UserLabels.connect(self.UserLabels)
#        self.opFilterNonLabeled.ForegroundLabels.connect(self.ForegroundLabelsShort)
#
#
#        
#        self.opLabelPipeline = OpMultiLaneWrapper(OpLabelPipeline, parent=self)
#        self.opLabelPipeline.FeatureData.connect(self.FeatureImages)
#        self.opLabelPipeline.ForegroundLabels.connect(self.ForegroundLabelsShort)
#        #self.InputChannelIndexes.setValue([1])
#        self.opLabelPipeline.ObjectIndices.connect(self.opFilterNonLabeled.Output)
#        self.opLabelPipeline.RawData.connect(self.InputImages)
#
#        self.ModifiedFeatureData.connect(self.opLabelPipeline.Output)
#        self.FilteredFeatureData.connect(self.opLabelPipeline.FilteredOutput)

        
        #self.opTrainCounter = OpTrainCounter(graph = self.graph, parent = self)
        #self.opTrainCounter.fixRegressor.setValue(False)
        #self.opTrainCounter.Dots.connect(self.UserLabels)
        #self.opTrainCounter.Images.connect(self.opLabelPipeline.FilteredOutput)
        self.FreezePredictions.setValue(True)

        self.opLabelPipeline = OpMultiLaneWrapper( OpLabelPipeline, parent=self )
        self.opLabelPipeline.RawImage.connect( self.InputImages )
        self.opLabelPipeline.LabelInput.connect( self.LabelInputs )
        self.LabelImages.connect( self.opLabelPipeline.Output )
        self.NonzeroLabelBlocks.connect( self.opLabelPipeline.nonzeroBlocks )

        self.opTrainCounter2 = OpTrainCounter2(graph = self.graph, parent = self)
        self.opTrainCounter2.fixRegressor.setValue(False)
        self.opTrainCounter2.Dots.connect(self.opLabelPipeline.Output)
        self.opTrainCounter2.Images.connect(self.FeatureImages)
        self.opTrainCounter2.Sigma.connect(self.Sigma)
        self.opTrainCounter2.UnderMult.connect(self.UnderMult)
        self.opTrainCounter2.OverMult.connect(self.OverMult)
        self.opTrainCounter2.SelectedOption.connect(self.SelectedOption)



        self.regressor_cache = OpValueCache( parent=self, graph=self.graph )
        self.regressor_cache.inputs["Input"].connect(self.opTrainCounter2.outputs['Output'])
        self.Regressor.connect( self.regressor_cache.Output )

        #self.opPredictCounter = OpMultiLaneWrapper(OpPredictCounter,graph = self.graph, parent =
        #                                         self)
        #self.opPredictCounter.Image.connect(self.opLabelPipeline.Output)
        #self.opPredictCounter.Regressor.connect(self.regressor_cache.Output)


        self.opPredictCounter2 = OpMultiLaneWrapper(OpPredictCounter2,graph = self.graph, parent =
                                                 self)
        self.opPredictCounter2.Image.connect(self.FeatureImages)
        self.opPredictCounter2.Regressor.connect(self.regressor_cache.Output)


        self.Density.connect(self.opPredictCounter2.Output)
        self.opVolumeSum = OpMultiLaneWrapper(OpVolumeOperator,parent=self, graph = self.graph )
        self.opVolumeSum.Input.connect(self.Density)
        self.opVolumeSum.Function.setValue(numpy.sum)

        self.OutputSum.connect(self.opVolumeSum.Output)
        #self.FilteredRaw.connect(self.opLabelPipeline.FilteredRaw)

        self.options = SVR.options

    def setupCaches(self, imageIndex):
        """Setup the label input to correct dimensions"""
    #    numImages=len(self.SegmentationImages)
    #    self.LabelInputs.resize(numImages)
    #    self.LabelInputs[imageIndex].meta.shape = (1,)
    #    self.LabelInputs[imageIndex].meta.dtype = object
    #    self.LabelInputs[imageIndex].meta.axistags = None
    #    self._resetLabelInputs(imageIndex)

    #def _resetLabelInputs(self, imageIndex, roi=None):
    #    labels = dict()
    #    for t in range(self.SegmentationImages[imageIndex].meta.shape[0]):
    #        labels[t] = numpy.zeros((2,))
    #    self.LabelInputs[imageIndex].setValue(labels)

    def setupOutputs(self):
        pass

    def setInSlot(self, slot, subindex, roi, value):
        pass

    def propagateDirty(self, slot, subindex, roi):
        pass

    def addLane(self, laneIndex):
        print "adding Lane"
        print laneIndex
        #numLanes = len(self.SegmentationImages)
        numLanes = 0
        assert numLanes == laneIndex, "Image lanes must be appended."
        for slot in self.inputs.values():
            if slot.level > 0 and len(slot) == laneIndex:
                print "resizing"
                slot.resize(numLanes + 1)
                print len(slot)

        for slot in self.outputs.values():
            if slot.level > 0 and len(slot) == laneIndex:
                print "resizing"
                slot.resize(numLanes + 1)
                print len(slot)
    def removeLane(self, laneIndex, finalLength):
        print "removing"
        for slot in self.inputs.values():
            if slot.level > 0 and len(slot) == finalLength + 1:
                slot.removeSlot(laneIndex, finalLength)

    def getLane(self, laneIndex):
        print laneIndex
        return OperatorSubView(self, laneIndex)
    
    def _updateParams(self, sigma, underMult, overMult):
        self.Sigma.setValue(sigma)
        self.Sigma.setDirty(slice(None))
        self.UnderMult.setValue(underMult)
        self.UnderMult.setDirty(slice(None))
        self.OverMult.setValue(overMult)
        self.OverMult.setDirty(slice(None))
    



def _atleast_nd(a, ndim):
    """Like numpy.atleast_1d and friends, but supports arbitrary ndim,
    always puts extra dimensions last, and resizes.

    """
    if ndim < a.ndim:
        return
    nnew = ndim - a.ndim
    newshape = tuple(list(a.shape) + [1] * nnew)
    a.resize(newshape)


def _concatenate(arrays, axis):
    """wrapper to numpy.concatenate that resizes arrays first."""
    arrays = list(a for a in arrays if 0 not in a.shape)
    if len(arrays) == 0:
        return numpy.array([])
    maxd = max(max(a.ndim for a in arrays), 2)
    for a in arrays:
        _atleast_nd(a, maxd)
    return numpy.concatenate(arrays, axis=axis)


#class OpObjectTrain(Operator):
#    name = "TrainRandomForestObjects"
#    description = "Train a random forest on multiple images"
#    category = "Learning"
#
#    Labels = InputSlot(level=1, stype=Opaque, rtype=List)
#    Features = InputSlot(level=1, rtype=List)
#    FixClassifier = InputSlot(stype="bool")
#    ForestCount = InputSlot(stype="int", value=1)
#
#    Classifier = OutputSlot()
#
#    def __init__(self, *args, **kwargs):
#        super(OpObjectTrain, self).__init__(*args, **kwargs)
#        self._tree_count = 100
#        self.FixClassifier.setValue(False)
#
#    def setupOutputs(self):
#        if self.inputs["FixClassifier"].value == False:
#            self.outputs["Classifier"].meta.dtype = object
#            self.outputs["Classifier"].meta.shape = (self.ForestCount.value,)
#            self.outputs["Classifier"].meta.axistags = None
#
#    def execute(self, slot, subindex, roi, result):
#
#        featMatrix = []
#        labelsMatrix = []
#
#        for i in range(len(self.Labels)):
#            feats = self.Features[i]([]).wait()
#
#            # TODO: we should be able to use self.Labels[i].value,
#            # but the current implementation of Slot.value() does not
#            # do the right thing.
#            labels = self.Labels[i]([]).wait()
#
#            for t in sorted(feats.keys()):
#                featsMatrix_tmp = []
#                labelsMatrix_tmp = []
#                lab = labels[t].squeeze()
#                index = numpy.nonzero(lab)
#                labelsMatrix_tmp.append(lab[index])
#
#                for channel in sorted(feats[t]):
#                    for featname in sorted(channel.keys()):
#                        value = channel[featname]
#                        if not featname in config.selected_features:
#                            continue
#                        ft = numpy.asarray(value.squeeze())
#                        featsMatrix_tmp.append(ft[index])
#
#                featMatrix.append(_concatenate(featsMatrix_tmp, axis=1))
#                labelsMatrix.append(_concatenate(labelsMatrix_tmp, axis=1))
#
#        if len(featMatrix) == 0 or len(labelsMatrix) == 0:
#            result[:] = None
#        else:
#            featMatrix = _concatenate(featMatrix, axis=0)
#            labelsMatrix = _concatenate(labelsMatrix, axis=0)
#
#            try:
#                # train and store forests in parallel
#                pool = Pool()
#                for i in range(self.ForestCount.value):
#                    def train_and_store(number):
#                        result[number] = vigra.learning.RandomForest(self._tree_count)
#                        result[number].learnRF(featMatrix.astype(numpy.float32),
#                                               labelsMatrix.astype(numpy.uint32))
#                    req = pool.request(partial(train_and_store, i))
#                pool.wait()
#                pool.clean()
#            except:
#                print ("couldn't learn classifier")
#                raise
#
#        slcs = (slice(0, self.ForestCount.value, None),)
#        self.outputs["Classifier"].setDirty(slcs)
#        return result
#
#    def propagateDirty(self, slot, subindex, roi):
#        if slot is not self.FixClassifier and \
#           self.inputs["FixClassifier"].value == False:
#            slcs = (slice(0, self.ForestCount.value, None),)
#            self.outputs["Classifier"].setDirty(slcs)


#class OpObjectPredict(Operator):
#    # WARNING: right now we predict and cache a whole time slice. We
#    # expect this to be fast because there are relatively few objects
#    # compared to the number of pixels in pixel classification. If
#    # this should be too slow, we should instead cache at the object
#    # level, and only predict for objects visible in the roi.
#
#    name = "OpObjectPredict"
#
#    Features = InputSlot(rtype=List)
#    LabelsCount = InputSlot(stype='integer')
#    Classifier = InputSlot()
#
#    Predictions = OutputSlot(stype=Opaque, rtype=List)
#
#    def setupOutputs(self):
#        self.Predictions.meta.shape = self.Features.meta.shape
#        self.Predictions.meta.dtype = object
#        self.Predictions.meta.axistags = None
#
#        self.cache = dict()
#
#    def execute(self, slot, subindex, roi, result):
#        forests=self.inputs["Classifier"][:].wait()
#
#        if forests is None:
#            # this happens if there was no data to train with
#            return numpy.zeros(numpy.subtract(roi.stop, roi.start),
#                               dtype=numpy.float32)[...]
#        feats = {}
#        predictions = {}
#        for t in roi._l:
#            if t in self.cache:
#                continue
#
#            ftsMatrix = []
#            tmpfeats = self.Features([t]).wait()
#            for channel in sorted(tmpfeats[t]):
#                for featname in sorted(channel.keys()):
#                    value = channel[featname]
#                    if not featname in config.selected_features:
#                        continue
#                    tmpfts = numpy.asarray(value).astype(numpy.float32)
#                    _atleast_nd(tmpfts, 2)
#                    ftsMatrix.append(tmpfts)
#
#            feats[t] = _concatenate(ftsMatrix, axis=1)
#            predictions[t]  = [0] * len(forests)
#
#        def predict_forest(t, number):
#            predictions[t][number] = forests[number].predictLabels(feats[t]).reshape(1, -1)
#
#        # predict the data with all the forests in parallel
#        pool = Pool()
#
#        for t in roi._l:
#            if t in self.cache:
#                continue
#            for i, f in enumerate(forests):
#                req = pool.request(partial(predict_forest, t, i))
#
#        pool.wait()
#        pool.clean()
#
#        final_predictions = dict()
#
#        for t in roi._l:
#            if t not in self.cache:
#                # shape (ForestCount, number of objects)
#                prediction = numpy.vstack(predictions[t])
#
#                # take mode of each column
#                m, _ = mode(prediction, axis=0)
#                m = m.squeeze()
#                assert m.ndim == 1
#                m[0] = 0
#                self.cache[t] = m
#            final_predictions[t] = self.cache[t]
#
#        return final_predictions
#
#    def propagateDirty(self, slot, subindex, roi):
#        self.cache = dict()
#        self.Predictions.setDirty(())

class OpToImage(Operator):
    """Takes a segmentation image and a mapping and returns the
    mapped image.

    For instance, map prediction labels onto objects.

    """
    name = "OpToImage"
    Image = InputSlot()
    ObjectMap = InputSlot(stype=Opaque, rtype=List)
    Features = InputSlot(rtype=List)
    Output = OutputSlot()

    def setupOutputs(self):
        self.Output.meta.assignFrom(self.Image.meta)

    def execute(self, slot, subindex, roi, result):
        slc = roi.toSlice()
        img = self.Image[slc].wait()

        for t in range(roi.start[0], roi.stop[0]):
            map_ = self.ObjectMap([t]).wait()
            tmap = map_[t]

            # FIXME: necessary because predictions are returned
            # enclosed in a list.
            if isinstance(tmap, list):
                tmap = tmap[0]

            tmap = tmap.squeeze()

            idx = img.max()
            if len(tmap) <= idx:
                newTmap = numpy.zeros((idx + 1,))
                newTmap[:len(tmap)] = tmap[:]
                tmap = newTmap

            img[t] = tmap[img[t]]

        return img

    def propagateDirty(self, slot, subindex, roi):
        if slot is self.Image:
            self.Output.setDirty(roi)

        elif slot is self.ObjectMap or slot is self.Features:
            # this is hacky. the gui's onClick() function calls
            # setDirty with a (time, object) pair, while elsewhere we
            # call setDirty with ().
            if len(roi._l) == 0:
                self.Output.setDirty(slice(None))
            elif isinstance(roi._l[0], int):
                for t in roi._l:
                    self.Output.setDirty(slice(t))
            else:
                assert len(roi._l[0]) == 2
                # for each dirty object, only set its bounding box dirty
                ts = list(set(t for t, _ in roi._l))
                feats = self.Features(ts).wait()
                for t, obj in roi._l:
                    try:
                        min_coords = feats[t][0]['Coord<Minimum>'][obj]
                        max_coords = feats[t][0]['Coord<Maximum>'][obj]
                    except KeyError:
                        min_coords = feats[t][0]['Coord<Minimum >'][obj]
                        max_coords = feats[t][0]['Coord<Maximum >'][obj]
                    slcs = list(slice(*args) for args in zip(min_coords, max_coords))
                    slcs = [slice(t, t+1),] + slcs + [slice(None),]
                    self.Output.setDirty(slcs)

class OpFilterNonLabeled( Operator ):

    UserLabels = InputSlot()
    ForegroundLabels  = InputSlot()
    Output = OutputSlot(rtype=List)
    #ObjectFeatures = InputSlot(rtype=List, level=1)

    def __init__(self, *args, **kwargs):
        super( OpFilterNonLabeled, self ).__init__( *args, **kwargs)
        self._lock = threading.Lock()
        self.cache = None
    def setupOutputs(self):
        self.Output.meta.shape = (1,)
        self.Output.meta.dtype = object
        self.Output.meta.axistags = None
        
    def execute(self, slot, subindex, roi, result):
        if self.cache is None:
            foreground = self.ForegroundLabels[:].allocate().wait()
            userlabels = self.UserLabels[:].allocate().wait()
            result = numpy.unique(foreground[numpy.where(userlabels == 2)])
        
        return [result]
    
    def propagateDirty(self, slot, subindex, roi):
        self.cache = None
        self.Output.setDirty(())

        


class OpLabelPipeline( Operator ):
    FeatureData = InputSlot()
    ForegroundLabels  = InputSlot()
    ObjectIndices = InputSlot()
    FilteredRaw = OutputSlot(optional = True)
    FilteredOutput = OutputSlot()
    Output = OutputSlot()
    RawData = InputSlot(optional = True)



    def __init__(self, *args, **kwargs):
        super( OpLabelPipeline, self ).__init__( *args, **kwargs)
        

        self.labelfiltering = OpPixelBinaryOperator(graph = self.graph, parent = self)
        self.labelfiltering.Input.connect(self.FeatureData)
        self.labelfiltering.Mask.connect(self.ForegroundLabels)
        def _labelMaskOperator(array, mask, objectList):
            f = numpy.vectorize(lambda x: x in objectList, otypes = [numpy.bool])
            binarymask = f(mask)
            #sitecustomize.debug_trace()
            return array * binarymask
        self.labelfiltering.BinaryFunction.setValue(_labelMaskOperator)
        self.labelfiltering.FunctionParameters.connect(self.ObjectIndices)


        self.rawfiltering = OpPixelBinaryOperator(graph = self.graph, parent = self)
        self.rawfiltering.Input.connect(self.RawData)
        self.rawfiltering.Mask.connect(self.ForegroundLabels)
        def _rawMaskOperator(array, mask, objectList):
            f = numpy.vectorize(lambda x: x in objectList, otypes = [numpy.bool])
            binarymask = f(mask)
            #sitecustomize.debug_trace()
            return array * binarymask
        self.rawfiltering.BinaryFunction.setValue(_labelMaskOperator)
        self.rawfiltering.FunctionParameters.connect(self.ObjectIndices)

        self.filtering = OpPixelBinaryOperator(graph = self.graph, parent = self)
        #self.filtering.Input.connect(self.opAverage.Output)
        self.filtering.Input.connect(self.FeatureData)
        self.filtering.Mask.connect(self.ForegroundLabels)
        def _maskOperator(array, mask):
            binarymask = numpy.where(mask < 1, 0,1)
            #sitecustomize.debug_trace()
            return array * binarymask
        self.filtering.BinaryFunction.setValue(_maskOperator)

        self.FilteredOutput.connect(self.labelfiltering.Output)
        self.Output.connect(self.filtering.Output)
        self.FilteredRaw.connect(self.rawfiltering.Output)



    def propagateDirty(self, slot, subindex, roi):
        print "propagatePipeline"
        if slot == self.FeatureData:
            key = roi.toSlice()
            self.outputs["Output"].setDirty(key)
        elif slot == self.ForegroundLabels:
            key = roi.toSlice()
            self.outputs["Output"].setDirty(key)
        elif slot == self.ObjectIndices:
            self.outputs["Output"].setDirty( slice(None) )
    
    
class OpLabelPipeline( Operator ):
    RawImage = InputSlot()
    LabelInput = InputSlot()
    
    Output = OutputSlot()
    nonzeroBlocks = OutputSlot()
    MaxLabel = OutputSlot()
    
    def __init__(self, *args, **kwargs):
        super( OpLabelPipeline, self ).__init__( *args, **kwargs )
        self.opInputShapeReader = OpShapeReader( parent=self )
        self.opInputShapeReader.Input.connect( self.RawImage )
        
        self.opLabelArray = OpBlockedSparseLabelArray( parent=self )
        self.opLabelArray.Input.connect( self.LabelInput )
        self.opLabelArray.shape.connect( self.opInputShapeReader.OutputShape )
        self.opLabelArray.eraser.setValue(100)

        # Initialize the delete input to -1, which means "no label".
        # Now changing this input to a positive value will cause label deletions.
        # (The deleteLabel input is monitored for changes.)
        self.opLabelArray.deleteLabel.setValue(-1)

        # Connect external outputs to their internal sources
        self.Output.connect( self.opLabelArray.Output )
        self.nonzeroBlocks.connect( self.opLabelArray.nonzeroBlocks )
        self.MaxLabel.connect( self.opLabelArray.maxLabel )
    
    def setupOutputs(self):
        taggedShape = self.RawImage.meta.getTaggedShape()
        blockDims = { 't' : 1, 'x' : 64, 'y' : 64, 'z' : 64, 'c' : 1 }
        blockDims = dict( filter( lambda (k,v): k in taggedShape, blockDims.items() ) )
        taggedShape.update( blockDims )
        self.opLabelArray.blockShape.setValue( tuple( taggedShape.values() ) )

    def setInSlot(self, slot, subindex, roi, value):
        # Nothing to do here: All inputs that support __setitem__
        #   are directly connected to internal operators.
        pass

    def execute(self, slot, subindex, roi, result):
        assert False, "Shouldn't get here.  Output is assigned a value in setupOutputs()"

    def propagateDirty(self, slot, subindex, roi):
        # Our output changes when the input changed shape, not when it becomes dirty.
        pass    
