
# basic python modules
import functools
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
from threading import Lock as ThreadLock

# required numerical modules
import numpy as np
import vigra
import opengm

# basic lazyflow types
from lazyflow.operator import Operator
from lazyflow.slot import InputSlot, OutputSlot
from lazyflow.rtype import SubRegion
from lazyflow.stype import Opaque
from lazyflow.request import Request, RequestPool

# required lazyflow operators
from lazyflow.operators.opLabelVolume import OpLabelVolume
from lazyflow.operators.valueProviders import OpArrayCache
from lazyflow.operators.opCompressedCache import OpCompressedCache
from lazyflow.operators.opReorderAxes import OpReorderAxes


class OpObjectsSegment(Operator):
    name = "OpObjectsSegment"

    # prediction maps
    Prediction = InputSlot()

    # thresholded predictions, or otherwise obtained ROI indicators
    # (a value of 0 is assumed to be background and ignored)
    Binary = InputSlot()

    # which channel to use (if there are multiple channels)
    Channel = InputSlot(value=0)

    # graph cut parameter
    Beta = InputSlot(value=.2)

    # intermediate results
    ConnectedComponents = OutputSlot()
    CachedConnectedComponents = OutputSlot()
    BoundingBoxes = OutputSlot(stype=Opaque)

    # segmentation image -> graph cut segmentation
    Output = OutputSlot()

    CachedOutput = OutputSlot()

    def __init__(self, *args, **kwargs):
        super(OpObjectsSegment, self).__init__(*args, **kwargs)

        opReorder = OpReorderAxes(parent=self)
        opReorder.Input.connect(self.Prediction)
        opReorder.AxisOrder.setValue('xyztc')  # vigra order
        self._opReorderPred = opReorder

        opReorder = OpReorderAxes(parent=self)
        opReorder.Input.connect(self.Binary)
        opReorder.AxisOrder.setValue('xyztc')  # vigra order
        self._opReorderBin = opReorder

        opCC = OpLabelVolume(parent=self)
        opCC.Input.connect(self._opReorderBin.Output)
        self.ConnectedComponents.connect(opCC.Output)
        self._opCC = opCC

        self.CachedConnectedComponents.connect(opCC.CachedOutput)

        self._outputCache = OpCompressedCache(parent=self)
        self._outputCache.name = "{}._outputCache".format(self.name)
        self._outputCache.Input.connect(self.Output)

        self._lock = ThreadLock()

    def setupOutputs(self):
        # sanity checks
        tags = self.Prediction.meta.axistags
        shape = self.Prediction.meta.shape
        haveAxes = [tags.index(c) < len(shape) for c in 'xyz']
        if not all(haveAxes):
            raise ValueError("Prediction maps must be a volume (XYZ)")
        # bounding boxes are just one element arrays of type object
        self.BoundingBoxes.meta.shape = (1,)

        self.Output.meta.assignFrom(self.Prediction.meta)
        self.Output.meta.dtype = np.uint8
        self.Output.meta.shape = self._opReorderPred.Output.meta.shape[:3]
        self.Output.meta.axistags = vigra.defaultAxistags('xyz')
        self.CachedOutput.meta.assignFrom(self.Output.meta)

        self._outputCache.BlockShape.setValue(self.Output.meta.shape)

    def execute(self, slot, subindex, roi, result):

        if slot == self.BoundingBoxes:
            return self._execute_bbox(roi, result)
        elif slot == self.Output:
            return self._execute_graphcut(roi, result)
        elif slot == self.CachedOutput:
            self._lock.acquire()
            newroi = roi.copy()
            req = self._outputCache.Output.get(newroi)
            req.writeInto(result)
            req.block()
            self._lock.release()
        else:
            raise NotImplementedError(
                "execute() is not implemented for slot {}".format(str(slot)))

    def _execute_bbox(self, roi, result):
        logger.debug("computing bboxes...")

        cc = self._opCC.CachedOutput[...].wait()
        cc = vigra.taggedView(cc, axistags=self._opCC.Output.meta.axistags)
        #FIXME what about time slices???
        cc = cc.withAxes(*'xyz')

        feats = vigra.analysis.extractRegionFeatures(
            cc.astype(np.float32),
            cc.astype(np.uint32),
            features=["Count", "Coord<Minimum>", "Coord<Maximum>"])
        feats_dict = {}
        feats_dict["Coord<Minimum>"] = feats["Coord<Minimum>"]
        feats_dict["Coord<Maximum>"] = feats["Coord<Maximum>"]
        feats_dict["Count"] = feats["Count"]
        return feats_dict

    def _execute_graphcut(self, roi, result):

        #TODO make margins an InputSlot
        margin = np.asarray((20, 20, 10))
        channel = self.Channel.value
        beta = self.Beta.value
        MAXBOXSIZE = 10000000  # FIXME justification??
        print("\n\n####################### COMPUTING {} #######################\n\n".format(channel))

        # add time and channel to roi (we reordered to full 'xyztc'!)
        predRoi = roi.copy()
        predRoi.insertDim(3, 0, 1)  # t
        predRoi.insertDim(4, channel, channel+1)  # c

        pred = self._opReorderPred.Output.get(predRoi).wait()
        pred = vigra.taggedView(pred,
                                axistags=self._opReorderPred.Output.meta.axistags)
        #FIXME what about time slices???
        pred = pred.withAxes(*'xyz')

        ccRoi = roi.copy()
        ccRoi.insertDim(3, 0, 1)  # t
        ccRoi.insertDim(4, 0, 1)  # c
        cc = self._opCC.CachedOutput.get(ccRoi).wait()
        cc = vigra.taggedView(cc,
                              axistags=self._opCC.CachedOutput.meta.axistags)
        #FIXME what about time slices???
        cc = cc.withAxes(*'xyz')

        feats = self.BoundingBoxes[0].wait()
        mins = feats["Coord<Minimum>"]
        maxs = feats["Coord<Maximum>"]
        nobj = mins.shape[0]

        # provide xyz view for the output
        resultXYZ = vigra.taggedView(result, axistags=self.Output.meta.axistags
                                     ).withAxes(*'xyz')
        # initialize result
        resultXYZ[:] = 0

        # let's hope the objects are not overlapping
        def parallel(i):
            logger.debug("processing object {}".format(i))
            print("processing object {} starting at {}".format(i, mins[i]))
            xmin = max(mins[i][0]-margin[0], 0)
            ymin = max(mins[i][1]-margin[1], 0)
            zmin = max(mins[i][2]-margin[2], 0)
            xmax = min(maxs[i][0]+margin[0], cc.shape[0])
            ymax = min(maxs[i][1]+margin[1], cc.shape[1])
            zmax = min(maxs[i][2]+margin[2], cc.shape[2])
            ccbox = cc[xmin:xmax, ymin:ymax, zmin:zmax]
            resbox = resultXYZ[xmin:xmax, ymin:ymax, zmin:zmax]

            nVoxels = np.prod(ccbox.shape)
            if nVoxels > MAXBOXSIZE:
                #problem too large to run graph cut, assign to seed
                logger.warn("Object {} too large for graph cut.".format(i))
                resbox[ccbox == i] = 1
                return

            probbox = pred[xmin:xmax, ymin:ymax, zmin:zmax]
            gcsegm = self._segmentGC_fast(probbox, beta)
            gcsegm = vigra.taggedView(gcsegm, axistags='xyz')
            ccsegm = vigra.analysis.labelVolumeWithBackground(
                gcsegm.astype(np.uint8))

            #FIXME document what this part is doing
            seed = ccbox == i
            filtered = seed*ccsegm
            passed = np.unique(filtered)
            assert len(passed.shape) == 1
            if passed.size > 2:
                logger.warn("ambiguous label assignment for region {}".format(
                    (xmin, xmax, ymin, ymax, zmin, zmax)))
                resbox[ccbox == i] = 1
            elif passed.size <= 1:
                logger.warn(
                    "box {} segmented out with beta {}".format(i, beta))
            else:
                # assign to the overlap region
                label = passed[1]  # 0 is background
                resbox[ccsegm == label] = 1

        pool = RequestPool()

        for i in range(1, nobj):
            req = Request(functools.partial(parallel, i))
            pool.add(req)

        logger.info("Processing {} objects ...".format(nobj-1))

        pool.wait()
        pool.clean()

        logger.info("object loop done")

        # convert from label image to segmentation
        resultXYZ[resultXYZ > 0] = 1

        return result

    @staticmethod
    def _segmentGC_fast(pred, beta):
        nx, ny, nz = pred.shape

        numVar = pred.size
        numLabels = 2

        numberOfStates = np.ones(numVar, dtype=opengm.index_type)*numLabels
        gm = opengm.graphicalModel(numberOfStates, operator='adder')

        #Adding unary function and factors
        functions = np.zeros((numVar, 2))
        predflat = pred.reshape((numVar, 1))
        if (predflat.dtype == np.uint8):
            predflat = predflat.astype(np.float32)
            predflat = predflat/256.

        functions[:, 0] = 2*predflat[:, 0]
        functions[:, 1] = 1-2*predflat[:, 0]

        fids = gm.addFunctions(functions)
        gm.addFactors(fids, np.arange(0, numVar))

        #add one binary function (potts fuction)
        potts = opengm.PottsFunction([2, 2], 0.0, beta)
        fid = gm.addFunction(potts)

        #add binary factors
        nyz = ny*nz
        indices = np.arange(numVar,
                            dtype=np.uint32).reshape((nx, ny, nz))
        arg1 = np.concatenate([indices[:nx - 1, :, :], indices[1:, :, :]]
                              ).reshape((2, numVar - nyz)).transpose()

        arg2 = np.concatenate([indices[:, :ny - 1, :], indices[:, 1:, :]]
                              ).reshape((2, numVar - nx*nz)).transpose()

        arg3 = np.concatenate([indices[:, :, :nz - 1], indices[:, :, 1:]]
                              ).reshape((2, numVar - nx*ny)).transpose()

        gm.addFactors(fid, arg1)
        gm.addFactors(fid, arg2)
        gm.addFactors(fid, arg3)

        grcut = opengm.inference.GraphCut(gm)
        grcut.infer()
        argmin = grcut.arg()

        res = argmin.reshape((nx, ny, nz))
        return res

    def propagateDirty(self, slot, subindex, roi):
        # all input slots affect the (global) graph cut computation
        self.Output.setDirty(slice(None))
        self.CachedOutput.setDirty(slice(None))

