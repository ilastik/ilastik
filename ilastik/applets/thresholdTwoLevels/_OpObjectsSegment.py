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

from _OpGraphCut import segmentGC_fast


## TODO documentation
class OpObjectsSegment(Operator):
    name = "OpObjectsSegment"

    # prediction maps
    Prediction = InputSlot()

    # thresholded predictions, or otherwise obtained ROI indicators
    # (a value of 0 is assumed to be background and ignored)
    LabelImage = InputSlot()

    # which channel to use (if there are multiple channels)
    Channel = InputSlot(value=0)

    # graph cut parameter
    Beta = InputSlot(value=.2)

    # margin around each object (always xyz!)
    Margin = InputSlot(value=np.asarray((20, 20, 20)))

    ## intermediate results ##

    # these slots are just piped
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
        opReorder.Input.connect(self.LabelImage)
        opReorder.AxisOrder.setValue('xyztc')  # vigra order
        self._opReorderLabels = opReorder

        self.ConnectedComponents.connect(self.LabelImage)
        self.CachedConnectedComponents.connect(self.LabelImage)

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

        cc = self._opReorderLabels.Output[...].wait()
        cc = vigra.taggedView(cc, axistags=self._opReorderLabels.Output.meta.axistags)
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

        margin = self.Margin.value
        channel = self.Channel.value
        beta = self.Beta.value
        MAXBOXSIZE = 10000000  # FIXME justification??

        ## request the bounding box coordinates ##
        feats = self.BoundingBoxes[0].wait()
        mins = feats["Coord<Minimum>"]
        maxs = feats["Coord<Maximum>"]
        nobj = mins.shape[0]
        # these are indices, so they should have an index datatype
        mins = mins.astype(np.uint32)
        maxs = maxs.astype(np.uint32)

        ## request the prediction image ##
        # add time and channel to roi (we reordered to full 'xyztc'!)
        predRoi = roi.copy()
        predRoi.insertDim(3, 0, 1)  # t
        predRoi.insertDim(4, channel, channel+1)  # c

        pred = self._opReorderPred.Output.get(predRoi).wait()
        pred = vigra.taggedView(pred,
                                axistags=self._opReorderPred.Output.meta.axistags)
        #FIXME what about time slices???
        pred = pred.withAxes(*'xyz')

        ## request the connected components image ##
        ccRoi = roi.copy()
        ccRoi.insertDim(3, 0, 1)  # t
        ccRoi.insertDim(4, 0, 1)  # c
        cc = self._opReorderLabels.Output.get(ccRoi).wait()
        cc = vigra.taggedView(
            cc, axistags=self._opReorderLabels.Output.meta.axistags)
        #FIXME what about time slices???
        cc = cc.withAxes(*'xyz')

        # provide xyz view for the output
        resultXYZ = vigra.taggedView(result, axistags=self.Output.meta.axistags
                                     ).withAxes(*'xyz')
        # initialize result
        resultXYZ[:] = 0

        # let's hope the objects are not overlapping
        def processSingleObject(i):
            logger.debug("processing object {}".format(i))
            # maxs are inclusive, so we need to add 1
            xmin = max(mins[i][0]-margin[0], 0)
            ymin = max(mins[i][1]-margin[1], 0)
            zmin = max(mins[i][2]-margin[2], 0)
            xmax = min(maxs[i][0]+margin[0]+1, cc.shape[0])
            ymax = min(maxs[i][1]+margin[1]+1, cc.shape[1])
            zmax = min(maxs[i][2]+margin[2]+1, cc.shape[2])
            ccbox = cc[xmin:xmax, ymin:ymax, zmin:zmax]
            resbox = resultXYZ[xmin:xmax, ymin:ymax, zmin:zmax]

            nVoxels = ccbox.size
            if nVoxels > MAXBOXSIZE:
                #problem too large to run graph cut, assign to seed
                logger.warn("Object {} too large for graph cut.".format(i))
                resbox[ccbox == i] = 1
                return

            probbox = pred[xmin:xmax, ymin:ymax, zmin:zmax]
            gcsegm = segmentGC_fast(probbox, beta)
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
        #TODO make sure that the parallel computations fit into memory
        for i in range(1, nobj):
            req = Request(functools.partial(processSingleObject, i))
            pool.add(req)

        logger.info("Processing {} objects ...".format(nobj-1))

        pool.wait()
        pool.clean()

        logger.info("object loop done")

        # convert from label image to segmentation
        resultXYZ[resultXYZ > 0] = 1

        return result

    def propagateDirty(self, slot, subindex, roi):
        # all input slots affect the (global) graph cut computation
        self.Output.setDirty(slice(None))
        self.CachedOutput.setDirty(slice(None))

