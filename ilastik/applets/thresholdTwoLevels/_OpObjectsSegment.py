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
#           http://ilastik.org/license.html
##############################################################################


# basic python modules
import functools
import logging
logger = logging.getLogger(__name__)
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

from _OpGraphCut import segmentGC, OpGraphCut


# segment predictions with pre-thresholding
#
# This operator segments an image into foreground and background and makes use
# of a preceding thresholding step. After thresholding, connected components
# are computed and are then considered to be "cores" of objects to be segmented.
# The Graph Cut optimization (see _OpGraphCut.OpGraphCut) is then applied to
# the bounding boxes of the object "cores, enlarged by a user-specified margin.
# The pre-thresholding operation allows to apply Graph Cut segmentation on
# large data volumes, in case the segmented foreground consists of sparse objects
# of limited size and the probability map of the unaries is of high recall, but
# possibly low precision. One particular application for this setup is
# segmentation of synapses in anisotropic 3D Electron Microscopy image stacks.
#
#
# The slot CachedOutput guarantees consistent results, the slot Output computes
# the roi on demand.
#
# The operator inherits from OpGraphCut because they share some details:
#   * output meta
#   * dirtiness propagation
#   * input slots
#
class OpObjectsSegment(OpGraphCut):
    name = "OpObjectsSegment"

    # thresholded predictions, or otherwise obtained ROI indicators
    # (a value of 0 is assumed to be background and ignored)
    LabelImage = InputSlot()

    # margin around each object (always zyx!)
    MarginZYX = InputSlot(value=np.asarray((20, 20, 20)))

    # bounding boxes of the labeled objects
    # this slot returns an array of dicts with shape (t, c)
    BoundingBoxes = OutputSlot(stype=Opaque)

    ### slots from OpGraphCut ###

    # prediction maps
    #Prediction = InputSlot()

    # graph cut parameter
    #Beta = InputSlot(value=.2)

    # labeled segmentation image
    #Output = OutputSlot()
    #CachedOutput = OutputSlot()

    def __init__(self, *args, **kwargs):
        super(OpObjectsSegment, self).__init__(*args, **kwargs)

    def setupOutputs(self):
        super(OpObjectsSegment, self).setupOutputs()
        # sanity checks
        shape = self.LabelImage.meta.shape
        assert len(shape) == 5,\
            "Prediction maps must be a full 5d volume (tzyxc)"
        tags = self.LabelImage.meta.getAxisKeys()
        tags = "".join(tags)
        assert tags == 'tzyxc',\
            "Label image has wrong axes order"\
            "(expected: tzyxc, got: {})".format(tags)

        # bounding boxes are just one element arrays of type object, but we
        # want to request boxes from a specific region, therefore BoundingBoxes
        # needs a shape
        shape = self.Prediction.meta.shape
        self.BoundingBoxes.meta.shape = shape
        self.BoundingBoxes.meta.dtype = np.object
        self.BoundingBoxes.meta.axistags = vigra.defaultAxistags('tzyxc')

    def execute(self, slot, subindex, roi, result):
        # check the axes - cannot do this in setupOutputs because we could be
        # in some invalid intermediate state where the dimensions do not agree
        shape = self.LabelImage.meta.shape
        agree = [i == j for i, j in zip(self.Prediction.meta.shape, shape)]
        assert all(agree),\
            "shape mismatch: {} vs. {}".format(self.Prediction.meta.shape,
                                               shape)
        if slot == self.BoundingBoxes:
            return self._execute_bbox(roi, result)
        elif slot == self.Output:
            self._execute_graphcut(roi, result)
        else:
            raise NotImplementedError(
                "execute() is not implemented for slot {}".format(str(slot)))

    def _execute_bbox(self, roi, result):
        cc = self.LabelImage.get(roi).wait()
        cc = vigra.taggedView(cc, axistags=self.LabelImage.meta.axistags)
        cc = cc.withAxes(*'zyx')

        logger.debug("computing bboxes...")
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
        for i in (0, 4):
            assert roi.stop[i] - roi.start[i] == 1,\
                "Invalid roi for graph-cut: {}".format(str(roi))
        t = roi.start[0]
        c = roi.start[4]

        margin_zyx = self.MarginZYX.value
        beta = self.Beta.value
        MAXBOXSIZE = 10000000  # FIXME justification??

        ## request the bounding box coordinates ##
        # the trailing index brackets give us the dictionary (instead of an
        # array of size 1)
        feats = self.BoundingBoxes.get(roi).wait()
        mins = feats["Coord<Minimum>"]
        maxs = feats["Coord<Maximum>"]
        nobj = mins.shape[0]
        # these are indices, so they should have an index datatype
        mins = mins.astype(np.uint32)
        maxs = maxs.astype(np.uint32)

        ## request the prediction image ##
        pred = self.Prediction.get(roi).wait()
        pred = vigra.taggedView(pred, axistags=self.Prediction.meta.axistags)
        pred = pred.withAxes(*'zyx')

        ## request the connected components image ##
        cc = self.LabelImage.get(roi).wait()
        cc = vigra.taggedView(cc, axistags=self.LabelImage.meta.axistags)
        cc = cc.withAxes(*'zyx')

        # provide zyx view for the output (just need 8bit for segmentation
        resultZYX = vigra.taggedView(np.zeros(cc.shape, dtype=np.uint8),
                                     axistags='zyx')

        def processSingleObject(i):
            logger.debug("processing object {}".format(i))
            # maxs are inclusive, so we need to add 1
            zmin = max(mins[i][0] - margin_zyx[0], 0)
            ymin = max(mins[i][1] - margin_zyx[1], 0)
            xmin = max(mins[i][2] - margin_zyx[2], 0)
            zmax = min(maxs[i][0] + margin_zyx[0] + 1, cc.shape[0])
            ymax = min(maxs[i][1] + margin_zyx[1] + 1, cc.shape[1])
            xmax = min(maxs[i][2] + margin_zyx[2] + 1, cc.shape[2])
            ccbox = cc[zmin:zmax, ymin:ymax, xmin:xmax]
            resbox = resultZYX[zmin:zmax, ymin:ymax, xmin:xmax]

            nVoxels = ccbox.size
            if nVoxels > MAXBOXSIZE:
                # problem too large to run graph cut, assign to seed
                logger.warning("Object {} too large for graph cut.".format(i))
                resbox[ccbox == i] = 1
                return

            probbox = pred[zmin:zmax, ymin:ymax, xmin:xmax]
            gcsegm = segmentGC(probbox, beta)
            gcsegm = vigra.taggedView(gcsegm, axistags='zyx')
            ccsegm = vigra.analysis.labelVolumeWithBackground(
                gcsegm.astype(np.uint8))

            # Extended bboxes of different objects might overlap.
            # To avoid conflicting segmentations, we find all connected
            # components in the results and only take the one, which
            # overlaps with the object "core" or "seed", defined by the
            # pre-thresholding
            seed = ccbox == i
            filtered = seed * ccsegm
            passed = vigra.analysis.unique(filtered.astype(np.uint32))
            assert len(passed.shape) == 1
            if passed.size > 2:
                logger.warning("ambiguous label assignment for region {}".format(
                    (zmin, zmax, ymin, ymax, xmin, xmax)))
                resbox[ccbox == i] = 1
            elif passed.size <= 1:
                logger.warning(
                    "box {} segmented out with beta {}".format(i, beta))
            else:
                # assign to the overlap region
                label = passed[1]  # 0 is background
                resbox[ccsegm == label] = 1

        pool = RequestPool()
        # FIXME make sure that the parallel computations fit into memory
        for i in range(1, nobj):
            req = Request(functools.partial(processSingleObject, i))
            pool.add(req)

        logger.info("Processing {} objects ...".format(nobj - 1))

        pool.wait()
        pool.clean()

        logger.info("object loop done")

        # prepare result
        resView = vigra.taggedView(result, axistags=self.Output.meta.axistags)
        resView = resView.withAxes(*'zyx')

        # some labels could have been removed => relabel
        vigra.analysis.labelVolumeWithBackground(resultZYX, out=resView)

    def propagateDirty(self, slot, subindex, roi):
        super(OpObjectsSegment, self).propagateDirty(slot, subindex, roi)

        if slot == self.LabelImage:
            # time-channel slices are pairwise independent

            # determine t, c from input volume
            t_ind = 0
            c_ind = 4
            t = (roi.start[t_ind], roi.stop[t_ind])
            c = (roi.start[c_ind], roi.stop[c_ind])

            # set output dirty
            start = t[0:1] + (0,) * 3 + c[0:1]
            stop = t[1:2] + self.Output.meta.shape[1:4] + c[1:2]
            roi = SubRegion(self.Output, start=start, stop=stop)
            self.Output.setDirty(roi)
        elif slot == self.MarginZYX:
            # margin affects the whole volume
            self.Output.setDirty(slice(None))
