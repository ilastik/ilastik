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
from __future__ import division
from builtins import next
from builtins import map

from builtins import zip
from builtins import range
from builtins import object
import numpy as np
import vigra
import h5py
from threading import Condition
from threading import Lock as HardLock

from collections import defaultdict
from functools import partial, wraps
import itertools

from lazyflow.operator import Operator, InputSlot, OutputSlot
from lazyflow.rtype import SubRegion
from lazyflow.operators.opCache import ObservableCache
from .opReorderAxes import OpReorderAxes

# the lazyflow lock seems to have deadlock issues sometimes
Lock = HardLock

import logging

logger = logging.getLogger(__name__)

_LABEL_TYPE = np.uint32


# Method decorator locking a method for the whole program. Needs the
# property self._lock to expose the Lock interface.
def threadsafe(method):
    @wraps(method)
    def wrapped(self, *args, **kwargs):
        with self._lock:
            return method(self, *args, **kwargs)

    return wrapped


# Locking decorator similar to threadsafe() that locks per chunk. The
# first argument of the wrapped method must be the chunk index.
def _chunksynchronized(method):
    @wraps(method)
    def synchronizedmethod(self, chunkIndex, *args, **kwargs):
        with self._chunk_locks[chunkIndex]:
            return method(self, chunkIndex, *args, **kwargs)

    return synchronizedmethod


# This class manages parallel executions of the lazy connected
# components algorithm. It tracks which process is responsible for
# finalizing which chunks / labels.
class _LabelManager(object):
    def __init__(self):
        self._lock = Condition()
        self._managedLabels = defaultdict(dict)
        self._iterator = InfiniteLabelIterator(1, dtype=_LABEL_TYPE)
        self._registered = set()
        self._total = 0
        self._asleep = 0

    # Call this before interacting with the manager object. Just used
    # for detecting cyclic wait() calls now.
    @threadsafe
    def hello(self):
        self._total += 1

    # Call at the end of execute()
    @threadsafe
    def goodbye(self):
        self._total -= 1

    # Call this if you are going to take responsibility for some chunks
    # or labels.
    @threadsafe
    def register(self):
        n = next(self._iterator)
        self._registered.add(n)
        return n

    # Call when done with all registered chunks.
    @threadsafe
    def unregister(self, n):
        self._registered.remove(n)
        self._lock.notify_all()

    # call to wait for other processes
    @threadsafe
    def waitFor(self, others):
        others = set(others)
        remaining = others & self._registered
        while len(remaining) > 0:
            self._asleep += 1
            if self._asleep == self._total:
                raise RuntimeError("Cyclic waiting detected")
            self._lock.wait()
            self._asleep -= 1
            remaining &= self._registered

    # Now that you are planning to finalize some labels in a chunk,
    # call this method to see which ones you really have to do and
    # which ones are being processed by some other process right now.
    # @param chunkIndex
    # @param labels a set of local labels you want to process
    # @param n result of the previous call to register()
    # @returns a 2-tuple, consisting of
    #           - the set of labels that you will have to process
    #           - the process numbers you will have to wait for such
    #             that all labels you requested are finalized
    # This method must not be called without being register()'ed first,
    # and you are _required_ to finalize the labels in the return value!
    @threadsafe
    def checkoutLabels(self, chunkIndex, labels, n):
        others = set()
        d = self._managedLabels[chunkIndex]
        for otherProcess, otherLabels in d.items():
            inters = np.intersect1d(labels, otherLabels)
            if inters.size > 0:
                labels = np.setdiff1d(labels, inters)
                others.add(otherProcess)
        if labels.size > 0:
            d[n] = labels
        return labels, others


# OpLazyConnectedComponents
# =========================
#
# This operator provides a connected components (labeling) algorithm
# that evaluates lazily, i.e. you don't need to process a full volume
# for getting the connected components in some ROI. The operator just
# computes spatial connected components, channels and time slices are
# treated independently.
#
# Guarantees
# ==========
#
# The resulting label image is equivalent[1] to the label image of
# the vigra function acting on the whole volume. The output is
# guaranteed to have exactly one label per connected component, and to
# have a contiguous set of labels *over the entire spatial volume*.
# This means that your first request to some subregion *could* give
# you labels [120..135], but somewhere else in the volume there will be
# at least one pixel labeled with each of [1..119]. Furthermore, the
# output is computed as lazy as possible, meaning that only the chunks
# that intersect with an object in the requested ROI are computed. The
# operator.execute() method is thread safe, but does not spawn new
# requests besides the ones needed for gathering input data.
# This operator conforms to OpLabelingABC, meaning that it can be used
# as an implementation backend in lazyflow.OpLabelVolume.
#
# [1] The labels might not be equal, but the uniquely labeled objects
#     are the same for both versions.
#
# Parallelization
# ===============
#
# The operator is thread safe, but has no parallelization of its own.
# The user (the GUI) is responsible for tiling the volume and spawning
# parallel requests to the operator's output slots.
#
# Implementation Details
# ======================
#
# The connected components algorithm used internally (chunk wise) is
#       vigra.labelMultiArrayWithBackground()
# with the default 4/6-neighborhood. See
#       http://ukoethe.github.io/vigra/doc/vigra/group__Labeling.html
# for details.
#
# There are 3 kinds of labels that we need to consider throughout the operator:
#     * local labels: The output of the chunk wise labeling calls. These are
#       stored in self._cache, a compressed VigraArray.
#       aka 'local'
#     * global indices: The mapping of local labels to unique global indices.
#       The actual implemetation is hidden in self.localToGlobal().
#       aka 'global'
#     * global labels: The final labels that are communicated to the outside
#       world. These must be contiguous, i.e. if  global label j appears in the
#       output, then, for every global label i<j, i also appears in the output.
#       The actual implementation is hidden in self.globalToFinal().
#       aka 'final'
#
# The strategy we are using could be written as the following piece of
# pseudocode:
#   - put all requested chunks in the processing queue
#   - for each chunk in processing queue:
#       * label the chunk, store the labels
#       * for each neighbour of chunk:
#           + identify objects extending to this neighbour, call makeUnion()
#           + if there were such objects, put chunk in processing queue
#
# In addition to this short algorithm, there is some bookkeeping going
# on that allows us to map the different label types to one another,
# and avoids excessive computation by tracking which process is
# responsible for which particular set of local labels.
#
class OpLazyConnectedComponents(Operator, ObservableCache):
    name = "OpLazyConnectedComponents"
    supportedDtypes = [np.uint8, np.uint32, np.float32]

    # input data (usually segmented)
    Input = InputSlot()

    # the spatial shape of one chunk, in 'xyz' order
    # (even if the input does lack some axis, you *have* to provide a
    # 3-tuple here)
    ChunkShape = InputSlot(optional=True)

    # background with axes 'txyzc', spatial axes must be singletons
    # (this layout is needed to be compatible with OpLabelVolume)
    Background = InputSlot(optional=True)

    # the labeled output, internally cached (the two slots are the same)
    Output = OutputSlot()
    CachedOutput = OutputSlot()

    # cache access slots, see OpCompressedCache

    # fill the cache from an HDF5 group
    InputHdf5 = InputSlot(optional=True)

    # returns an object array of length 1 that contains a list of 2-tuples
    # first item is block start, second item is block stop (exclusive)
    CleanBlocks = OutputSlot()

    # fills an HDF5 group with data from cache, requests must be for exactly
    # one block
    OutputHdf5 = OutputSlot()

    ### INTERNALS -- DO NOT USE ###
    _Input = OutputSlot()
    _Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super(OpLazyConnectedComponents, self).__init__(*args, **kwargs)
        self._lock = HardLock()
        # be able to request usage stats right from initialization
        self._cache = None

        # reordering operators - we want to handle txyzc inside this operator
        self._opIn = OpReorderAxes(parent=self)
        self._opIn.AxisOrder.setValue("txyzc")
        self._opIn.Input.connect(self.Input)
        self._Input.connect(self._opIn.Output)

        self._opOut = OpReorderAxes(parent=self)
        self._opOut.Input.connect(self._Output)
        self.Output.connect(self._opOut.Output)
        self.CachedOutput.connect(self.Output)

        # Now that we're initialized, it's safe to register with the memory manager
        self.registerWithMemoryManager()

    def setupOutputs(self):
        self.Output.meta.assignFrom(self.Input.meta)
        self.Output.meta.dtype = _LABEL_TYPE
        self._Output.meta.assignFrom(self._Input.meta)
        self._Output.meta.dtype = _LABEL_TYPE
        if not self.Input.meta.dtype in self.supportedDtypes:
            raise ValueError("Cannot label data type {}".format(self.Input.meta.dtype))

        self.OutputHdf5.meta.assignFrom(self.Input.meta)
        self.CleanBlocks.meta.shape = (1,)
        self.CleanBlocks.meta.dtype = object

        self._setDefaultInternals()

        # go back to original order
        self._opOut.AxisOrder.setValue(self.Input.meta.getAxisKeys())

    def execute(self, slot, subindex, roi, result):
        if slot is self._Output:
            logger.debug("Execute for {}".format(roi))
            self._manager.hello()
            othersToWaitFor = set()
            chunks = self._roiToChunkIndex(roi)
            for chunk in chunks:
                othersToWaitFor |= self.growRegion(chunk)

            self._manager.waitFor(othersToWaitFor)
            self._manager.goodbye()
            self._mapArray(roi, result)
            self._report()
        elif slot == self.OutputHdf5:
            self._executeOutputHdf5(roi, result)
        elif slot == self.CleanBlocks:
            self._executeCleanBlocks(result)
        else:
            raise ValueError("Request to invalid slot {}".format(str(slot)))

    def propagateDirty(self, slot, subindex, roi):
        # Dirty handling is not trivial with this operator. The worst
        # case happens when an object disappears entirely, meaning that
        # the assigned labels would not be contiguous anymore. We could
        # check for that here, and set everything dirty if it's the
        # case, but this would require us to run the entire algorithm
        # once again, which is not desireable in propagateDirty(). The
        # simplest valid decision is to set the whole output dirty in
        # every case.
        self._setDefaultInternals()
        self.Output.setDirty(slice(None))

    def setInSlot(self, slot, subindex, key, value):
        if slot == self.InputHdf5:
            self._setInSlotInputHdf5(slot, subindex, key, value)
        else:
            raise ValueError("setInSlot() not supported for slot {}".format(slot))

    # grow the requested region such that all labels inside that region are
    # final
    # @param chunkIndex the index of the chunk to finalize
    def growRegion(self, chunkIndex):
        ticket = self._manager.register()
        othersToWaitFor = set()

        # label this chunk
        self._label(chunkIndex)

        # we want to finalize every label in our first chunk
        localLabels = np.arange(1, self._numIndices[chunkIndex] + 1)
        localLabels = localLabels.astype(_LABEL_TYPE)
        chunksToProcess = [(chunkIndex, localLabels)]

        while chunksToProcess:
            # Breadth-First-Search, using list as FIFO
            currentChunk, localLabels = chunksToProcess.pop(0)

            # get the labels in use by this chunk
            # (no need to label this chunk, has been done already because it
            # was labeled as a neighbour of the last chunk, and the first chunk
            # was labeled above)
            localLabels = np.arange(1, self._numIndices[currentChunk] + 1)
            localLabels = localLabels.astype(_LABEL_TYPE)

            # tell the label manager that we are about to finalize some labels
            actualLabels, others = self._manager.checkoutLabels(currentChunk, localLabels, ticket)
            othersToWaitFor |= others

            # now we have got a list of local labels for this chunk, which no
            # other process is going to finalize

            # start merging adjacent regions
            otherChunks = self._generateNeighbours(currentChunk)
            for other in otherChunks:
                self._label(other)
                a, b = self._orderPair(currentChunk, other)
                me = 0 if a == currentChunk else 1
                res = self._merge(a, b)
                myLabels, otherLabels = res[me], res[1 - me]

                # determine which objects from this chunk continue in the
                # neighbouring chunk
                extendingLabels = np.array([b for a, b in zip(myLabels, otherLabels) if a in actualLabels]).astype(
                    myLabels.dtype
                )

                # add the neighbour to our processing queue only if it actually
                # shares objects
                if extendingLabels.size > 0:
                    extendingLabels = np.sort(vigra.analysis.unique(extendingLabels)).astype(_LABEL_TYPE)
                    # check if already in queue
                    found = False
                    for i in range(len(chunksToProcess)):
                        if chunksToProcess[i][0] == other:
                            extendingLabels = np.union1d(chunksToProcess[i][1], extendingLabels)
                            chunksToProcess[i] = (other, extendingLabels)
                            found = True
                            break
                    if not found:
                        chunksToProcess.append((other, extendingLabels))

        self._manager.unregister(ticket)
        return othersToWaitFor

    # label a chunk and store information
    @_chunksynchronized
    def _label(self, chunkIndex):
        if self._numIndices[chunkIndex] >= 0:
            # this chunk is already labeled
            return

        logger.debug("labeling chunk {} ({})".format(chunkIndex, self._chunkIndexToRoi(chunkIndex)))
        # get the raw data
        roi = self._chunkIndexToRoi(chunkIndex)
        inputChunk = self._Input.get(roi).wait()
        inputChunk = vigra.taggedView(inputChunk, axistags="txyzc")
        inputChunk = inputChunk.withAxes(*"xyz")

        # label the raw data
        assert self._background_valid, "Background values are configured incorrectly"
        bg = self._background[chunkIndex[0], chunkIndex[4]]
        # a vigra bug forces us to convert to int here
        bg = int(bg)
        # TODO use labelMultiArray once available
        labeled = vigra.analysis.labelVolumeWithBackground(inputChunk, background_value=bg)
        labeled = vigra.taggedView(labeled, axistags="xyz").withAxes(*"txyzc")
        del inputChunk
        # TODO this could be more efficiently combined with merging

        # store the labeled data in cache
        self._cache[roi.toSlice()] = labeled

        # update the labeling information
        numLabels = labeled.max()  # we ignore 0 here
        self._numIndices[chunkIndex] = numLabels
        if numLabels > 0:
            with self._lock:
                # determine the offset
                # localLabel + offset = globalLabel (for localLabel>0)
                offset = self._uf.makeNewIndex()
                self._globalLabelOffset[chunkIndex] = offset - 1

                # get n-1 more labels
                for i in range(numLabels - 1):
                    self._uf.makeNewIndex()

    # merge the labels of two adjacent chunks
    # the chunks have to be ordered lexicographically, e.g. by self._orderPair
    @_chunksynchronized
    def _merge(self, chunkA, chunkB):
        if chunkB in self._mergeMap[chunkA]:
            return (np.zeros((0,), dtype=_LABEL_TYPE),) * 2
        assert not self._isFinal[chunkA]
        assert not self._isFinal[chunkB]
        self._mergeMap[chunkA].append(chunkB)

        hyperplane_roi_a, hyperplane_roi_b = self._chunkIndexToHyperplane(chunkA, chunkB)
        hyperplane_index_a = hyperplane_roi_a.toSlice()
        hyperplane_index_b = hyperplane_roi_b.toSlice()

        label_hyperplane_a = self._cache[hyperplane_index_a]
        label_hyperplane_b = self._cache[hyperplane_index_b]

        # see if we have border labels at all
        adjacent_bool_inds = np.logical_and(label_hyperplane_a > 0, label_hyperplane_b > 0)
        if not np.any(adjacent_bool_inds):
            return (np.zeros((0,), dtype=_LABEL_TYPE),) * 2

        # check if the labels do actually belong to the same component
        hyperplane_a = self._Input[hyperplane_index_a].wait()
        hyperplane_b = self._Input[hyperplane_index_b].wait()
        adjacent_bool_inds = np.logical_and(adjacent_bool_inds, hyperplane_a == hyperplane_b)

        # union find manipulations are critical
        with self._lock:
            map_a = self.localToGlobal(chunkA)
            map_b = self.localToGlobal(chunkB)
            labels_a = map_a[label_hyperplane_a[adjacent_bool_inds]]
            labels_b = map_b[label_hyperplane_b[adjacent_bool_inds]]
            for a, b in zip(labels_a, labels_b):
                assert a not in self._globalToFinal, "Invalid merge"
                assert b not in self._globalToFinal, "Invalid merge"
                self._uf.makeUnion(a, b)

            logger.debug("merged chunks {} and {}".format(chunkA, chunkB))
        correspondingLabelsA = label_hyperplane_a[adjacent_bool_inds]
        correspondingLabelsB = label_hyperplane_b[adjacent_bool_inds]
        return correspondingLabelsA, correspondingLabelsB

    # get a rectangular region with final global labels
    # @param roi region of interest
    # @param result array of shape roi.stop - roi.start, will be filled
    def _mapArray(self, roi, result):
        assert np.all(roi.stop - roi.start == result.shape)

        logger.debug("mapping roi {}".format(roi))
        indices = self._roiToChunkIndex(roi)
        for idx in indices:
            newroi = self._chunkIndexToRoi(idx)
            newroi.stop = np.minimum(newroi.stop, roi.stop)
            newroi.start = np.maximum(newroi.start, roi.start)
            self._mapChunk(idx)
            chunk = self._cache[newroi.toSlice()]
            newroi.start -= roi.start
            newroi.stop -= roi.start
            s = newroi.toSlice()
            result[s] = chunk

    # Store a chunk with final labels in cache
    @_chunksynchronized
    def _mapChunk(self, chunkIndex):
        if self._isFinal[chunkIndex]:
            return

        newroi = self._chunkIndexToRoi(chunkIndex)
        s = newroi.toSlice()
        chunk = self._cache[s]
        labels = self.localToGlobal(chunkIndex)
        labels = self.globalToFinal(chunkIndex[0], chunkIndex[4], labels)
        self._cache[s] = labels[chunk]

        self._isFinal[chunkIndex] = True

    # returns an array of global labels in use by this chunk. This array can be
    # used as a mapping via
    #   mapping = localToGlobal(...)
    #   mapped = mapping[locallyLabeledArray]
    # The global labels are updated to their current state according to the
    # global UnionFind structure.
    def localToGlobal(self, chunkIndex):
        offset = self._globalLabelOffset[chunkIndex]
        numLabels = self._numIndices[chunkIndex]
        labels = np.arange(1, numLabels + 1, dtype=_LABEL_TYPE) + offset

        labels = np.asarray(list(map(self._uf.findIndex, labels)), dtype=_LABEL_TYPE)

        # we got 'numLabels' real labels, and one label '0', so our
        # output has to have numLabels+1 elements
        out = np.zeros((numLabels + 1,), dtype=_LABEL_TYPE)
        out[1:] = labels
        return out

    # map an array of global indices to final labels
    # after calling this function, the labels passed in may not be used with
    # UnionFind.makeUnion any more!
    @threadsafe
    def globalToFinal(self, t, c, labels):
        newlabels = labels.copy()
        d = self._globalToFinal[(t, c)]
        labeler = self._labelIterators[(t, c)]
        for k in vigra.analysis.unique(labels):
            l = self._uf.findIndex(k)
            if l == 0:
                continue

            if l not in d:
                nextLabel = next(labeler)
                d[l] = nextLabel
            newlabels[labels == k] = d[l]
        return newlabels

    ##########################################################################
    ##################### HELPER METHODS #####################################
    ##########################################################################

    # create roi object from chunk index
    def _chunkIndexToRoi(self, index):
        shape = self._shape
        start = self._chunkShape * np.asarray(index)
        stop = self._chunkShape * (np.asarray(index) + 1)
        stop = np.where(stop > shape, shape, stop)
        roi = SubRegion(self.Input, start=tuple(start), stop=tuple(stop))
        return roi

    # create a list of chunk indices needed for a particular roi
    def _roiToChunkIndex(self, roi):
        cs = self._chunkShape
        start = np.asarray(roi.start)
        stop = np.asarray(roi.stop)
        start_cs = start // cs
        stop_cs = stop // cs
        # add one if division was not even
        stop_cs += np.where(stop % cs, 1, 0)
        iters = [range(start_cs[i], stop_cs[i]) for i in range(5)]
        chunks = list(itertools.product(*iters))
        return chunks

    # compute the adjacent hyperplanes of two chunks (1 pix wide)
    # @return 2-tuple of roi's for the respective chunk
    def _chunkIndexToHyperplane(self, chunkA, chunkB):
        rev = False
        assert chunkA[0] == chunkB[0] and chunkA[4] == chunkB[4], "these chunks are not spatially adjacent"

        # just iterate over spatial axes
        for i in range(1, 4):
            if chunkA[i] > chunkB[i]:
                rev = True
                chunkA, chunkB = chunkB, chunkA
            if chunkA[i] < chunkB[i]:
                roiA = self._chunkIndexToRoi(chunkA)
                roiB = self._chunkIndexToRoi(chunkB)
                start = np.asarray(roiA.start)
                start[i] = roiA.stop[i] - 1
                roiA.start = tuple(start)
                stop = np.asarray(roiB.stop)
                stop[i] = roiB.start[i] + 1
                roiB.stop = tuple(stop)
        if rev:
            return roiB, roiA
        else:
            return roiA, roiB

    # generate a list of adjacent chunks
    def _generateNeighbours(self, chunkIndex):
        n = []
        idx = np.asarray(chunkIndex, dtype=np.int64)
        # only spatial neighbours are considered
        for i in range(1, 4):
            if idx[i] > 0:
                new = idx.copy()
                new[i] -= 1
                n.append(tuple(new))
            if idx[i] + 1 < self._chunkArrayShape[i]:
                new = idx.copy()
                new[i] += 1
                n.append(tuple(new))
        return n

    # fills attributes with standard values, call on each setupOutputs
    def _setDefaultInternals(self):
        # chunk array shape calculation
        shape = self._Input.meta.shape
        if self.ChunkShape.ready():
            chunkShape = (1,) + self.ChunkShape.value + (1,)
        elif self._Input.meta.ideal_blockshape is not None and np.prod(self._Input.meta.ideal_blockshape) > 0:
            chunkShape = self._Input.meta.ideal_blockshape
        else:
            chunkShape = self._automaticChunkShape(self._Input.meta.shape)
        assert len(shape) == len(chunkShape), "Encountered an invalid chunkShape"
        chunkShape = np.minimum(shape, chunkShape)
        f = lambda i: shape[i] // chunkShape[i] + (1 if shape[i] % chunkShape[i] else 0)
        self._chunkArrayShape = tuple(map(f, list(range(len(shape)))))
        self._chunkShape = np.asarray(chunkShape, dtype=np.int64)
        self._shape = shape

        # determine the background values
        self._background = np.zeros((shape[0], shape[4]), dtype=self.Input.meta.dtype)
        if self.Background.ready():
            bg = self.Background[...].wait()
            bg = vigra.taggedView(bg, axistags="txyzc").withAxes("t", "c")
            # we might have an old value set for the background value
            # ignore it until it is configured correctly, or execute is called
            if bg.size > 1 and (shape[0] != bg.shape[0] or shape[4] != bg.shape[1]):
                self._background_valid = False
            else:
                self._background_valid = True
                self._background[:] = bg
        else:
            self._background_valid = True

        # manager object
        self._manager = _LabelManager()

        ### local labels ###
        # cache for local labels
        # adjust cache chunk shape to our chunk shape
        cs = tuple(map(_get_next_power, self._chunkShape))
        logger.debug("Creating cache with chunk shape {}".format(cs))
        self._cache = vigra.ChunkedArrayCompressed(shape, dtype=_LABEL_TYPE, chunk_shape=cs)

        ### global indices ###
        # offset (global labels - local labels) per chunk
        self._globalLabelOffset = np.ones(self._chunkArrayShape, dtype=_LABEL_TYPE)
        # keep track of number of indices in chunk (-1 == not labeled yet)
        self._numIndices = -np.ones(self._chunkArrayShape, dtype=np.int32)

        # union find data structure, tells us for every global index to which
        # label it belongs
        self._uf = UnionFindArray(_LABEL_TYPE(1))

        ### global labels ###
        # keep track of assigned global labels
        gen = partial(InfiniteLabelIterator, 1, dtype=_LABEL_TYPE)
        self._labelIterators = defaultdict(gen)
        self._globalToFinal = defaultdict(dict)
        self._isFinal = np.zeros(self._chunkArrayShape, dtype=bool)

        ### algorithmic ###

        # keep track of merged regions
        self._mergeMap = defaultdict(list)

        # locks that keep threads from changing a specific chunk
        self._chunk_locks = defaultdict(HardLock)

    def _executeCleanBlocks(self, destination):
        assert destination.shape == (1,)
        finalIndices = np.where(self._isFinal)

        def ind2tup(ind):
            roi = self._chunkIndexToRoi(ind)
            return (roi.start, roi.stop)

        destination[0] = list(map(ind2tup, list(zip(*finalIndices))))

    def _executeOutputHdf5(self, roi, destination):
        logger.debug("Servicing request for hdf5 block {}".format(roi))

        assert isinstance(
            destination, h5py.Group
        ), "OutputHdf5 slot requires an hdf5 GROUP to copy into (not a numpy array)."
        index = self._roiToChunkIndex(roi)[0]
        block_roi = self._chunkIndexToRoi(index)
        valid = np.all(roi.start == block_roi.start)
        valid = valid and np.all(roi.stop == block_roi.stop)
        assert valid, "OutputHdf5 slot requires roi to be exactly one block."

        name = str([block_roi.start, block_roi.stop])
        assert name not in destination, "destination hdf5 group already has a dataset with this block's name"
        destination.create_dataset(
            name, shape=self._chunkShape, dtype=_LABEL_TYPE, data=self._cache[block_roi.toSlice()]
        )

    def _setInSlotInputHdf5(self, slot, subindex, roi, value):
        logger.debug("Setting block {} from hdf5".format(roi))
        assert isinstance(
            value, h5py.Dataset
        ), "InputHdf5 slot requires an hdf5 Dataset to copy from (not a numpy array)."

        indices = self._roiToChunkIndex(roi)
        for idx in indices:
            cacheroi = self._chunkIndexToRoi(idx)
            cacheroi.stop = np.minimum(cacheroi.stop, roi.stop)
            cacheroi.start = np.maximum(cacheroi.start, roi.start)
            dsroi = cacheroi.copy()
            dsroi.start -= roi.start
            dsroi.stop -= roi.start
            self._cache[cacheroi.toSlice()] = value[dsroi.toSlice()]
            self._isFinal[idx] = True

    # print a summary of blocks in use and their storage volume
    def _report(self):
        m = {np.uint8: 1, np.uint16: 2, np.uint32: 4, np.uint64: 8}
        nStoredChunks = self._isFinal.sum()
        nChunks = self._isFinal.size
        cachedMB = self._cache.data_bytes / 1024.0**2
        rawMB = self._cache.size * m[_LABEL_TYPE]
        logger.debug("Currently stored chunks: {}/{} ({:.1f} MB)".format(nStoredChunks, nChunks, cachedMB))

    # order a pair of chunk indices lexicographically
    # (ret[0] is top-left-in-front-of of ret[1])
    @staticmethod
    def _orderPair(tupA, tupB):
        for a, b in zip(tupA, tupB):
            if a < b:
                return tupA, tupB
            if a > b:
                return tupB, tupA
        raise ValueError("tupA={} and tupB={} are the same".format(tupA, tupB))
        return tupA, tupB

    # choose chunk shape appropriate for a particular dataset
    # TODO: this is by no means an optimal decision -> extend
    @staticmethod
    def _automaticChunkShape(shape):
        # use about 16 million pixels per chunk
        default = (1, 256, 256, 256, 1)
        if np.prod(shape) < 2 * np.prod(default):
            return (1,) + shape[1:4] + (1,)
        else:
            return default

    # ======== CACHE API ========

    def usedMemory(self):
        if self._cache is not None:
            return self._cache.data_bytes
        else:
            return 0

    def fractionOfUsedMemoryDirty(self):
        # we do not handle dirtyness
        return 0.0

    def generateReport(self, report):
        super(OpLazyConnectedComponents, self).generateReport(report)
        report.dtype = _LABEL_TYPE


###########
#  TOOLS  #
###########


# python implementation of vigra's UnionFindArray structure
class UnionFindArray(object):
    def __init__(self, nextFree=1):
        self._map = dict(list(zip(*(list(range(nextFree)),) * 2)))
        self._lock = HardLock()
        self._nextFree = nextFree
        self._it = None

    ## join regions a and b
    # callback is called whenever two regions are joined that were
    # separate before, signature is
    #   callback(smaller_label, larger_label)
    @threadsafe
    def makeUnion(self, a, b):
        assert a in self._map
        assert b in self._map

        a = self._findIndex(a)
        b = self._findIndex(b)

        # avoid cycles by choosing the smallest label as the common one
        # swap such that a is smaller
        if a > b:
            a, b = b, a

        self._map[b] = a

    @threadsafe
    def makeNewIndex(self):
        newLabel = self._nextFree
        self._nextFree += 1
        self._map[newLabel] = newLabel
        return newLabel

    @threadsafe
    def findIndex(self, a):
        return self._findIndex(a)

    def _findIndex(self, a):
        while a != self._map[a]:
            a = self._map[a]
        return a

    def __str__(self):
        s = "<UnionFindArray>\n{}".format(self._map)

    def __getstate__(self):
        odict = self.__dict__.copy()
        del odict["_lock"]
        return odict

    def __setstate__(self, dict):
        self.__dict__.update(dict)


class InfiniteLabelIterator(object):
    def __init__(self, n, dtype=_LABEL_TYPE):
        if not np.issubdtype(dtype, np.integer):
            raise ValueError("Labels must have an integral type")
        self.dtype = dtype
        self.n = n

    def __next__(self):
        a = self.dtype(self.n)
        assert a < np.iinfo(self.dtype).max, "Label overflow."
        self.n += 1
        return a


def _get_next_power(x, n=2):
    a = 1
    while a < x:
        a *= n
    return a
