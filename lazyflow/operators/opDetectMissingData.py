from __future__ import print_function
from __future__ import division
from future import standard_library

standard_library.install_aliases()
from builtins import zip

from builtins import range
from builtins import object

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
# 		   http://ilastik.org/license/
###############################################################################
import logging
from functools import partial
import pickle as pickle
import tempfile
from threading import Lock as ThreadLock
import re


from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.stype import Opaque
from lazyflow.rtype import SubRegion
from lazyflow.request import Request, RequestPool
from lazyflow.roi import roiToSlice

import numpy as np

import vigra


logger = logging.getLogger(__name__)


class VersionError(Exception):
    pass


def extractVersion(s):
    # assuming a string with a decimal number inside
    # e.g. "0.11-ubuntu", "haiku_os-sklearn-0.9"
    reInt = re.compile("\d+")
    m = reInt.findall(s)
    if m is None or len(m) < 1:
        raise VersionError("Cannot determine sklearn version")
    else:
        return int(m[1])


try:
    from sklearn import __version__ as sklearnVersion

    svcTakesScaleC = extractVersion(sklearnVersion) < 11
except ImportError as VersionError:
    logger.warning("Could not import dependency 'sklearn' for SVMs")
    havesklearn = False
else:
    havesklearn = True


def SVC(*args, **kwargs):
    from sklearn.svm import SVC as _SVC

    # old scikit-learn versions take scale_C as a parameter
    # new ones don't and default to True
    if not svcTakesScaleC and "scale_C" in kwargs:
        del kwargs["scale_C"]
    return _SVC(*args, **kwargs)


_defaultBinSize = 30


############################
############################
############################
###                      ###
###  DETECTION OPERATOR  ###
###                      ###
############################
############################
############################


class OpDetectMissing(Operator):
    """
    Sub-Operator for detection of missing image content
    """

    InputVolume = InputSlot()
    PatchSize = InputSlot(value=128)
    HaloSize = InputSlot(value=30)
    DetectionMethod = InputSlot(value="classic")
    NHistogramBins = InputSlot(value=_defaultBinSize)
    OverloadDetector = InputSlot(value="")

    # histograms: ndarray, shape: nHistograms x (NHistogramBins.value + 1)
    # the last column holds the label, i.e. {0: negative, 1: positive}
    TrainingHistograms = InputSlot()

    Output = OutputSlot()
    Detector = OutputSlot(stype=Opaque)

    ### PRIVATE class attributes ###
    _manager = None

    ### PRIVATE attributes ###
    _inputRange = (0, 255)
    _needsTraining = True
    _felzenOpts = {
        "firstSamples": 250,
        "maxRemovePerStep": 0,
        "maxAddPerStep": 250,
        "maxSamples": 1000,
        "nTrainingSteps": 4,
    }

    def __init__(self, *args, **kwargs):
        super(OpDetectMissing, self).__init__(*args, **kwargs)
        self.TrainingHistograms.setValue(_defaultTrainingHistograms())

    def propagateDirty(self, slot, subindex, roi):
        if slot == self.InputVolume:
            self.Output.setDirty(roi)

        if slot == self.TrainingHistograms:
            OpDetectMissing._needsTraining = True

        if slot == self.NHistogramBins:
            OpDetectMissing._needsTraining = OpDetectMissing._manager.has(self.NHistogramBins.value)

        if slot == self.PatchSize or slot == self.HaloSize:
            self.Output.setDirty()

        if slot == self.OverloadDetector:
            s = self.OverloadDetector.value
            self.loads(s)
            self.Output.setDirty()

    def setupOutputs(self):
        self.Output.meta.assignFrom(self.InputVolume.meta)
        self.Output.meta.dtype = np.uint8

        # determine range of input
        if self.InputVolume.meta.dtype == np.uint8:
            r = (0, 255)
        elif self.InputVolume.meta.dtype == np.uint16:
            r = (0, 65535)
        else:
            # FIXME hardcoded range, use np.iinfo
            r = (0, 255)
        self._inputRange = r

        self.Detector.meta.shape = (1,)

    def execute(self, slot, subindex, roi, result):

        if slot == self.Detector:
            result = self.dumps()
            return result

        # sanity check
        assert self.DetectionMethod.value in ["svm", "classic"], "Unknown detection method '{}'".format(
            self.DetectionMethod.value
        )

        # prefill result
        resultZYXCT = vigra.taggedView(result, self.InputVolume.meta.axistags).withAxes(*"zyxct")

        # acquire data
        data = self.InputVolume.get(roi).wait()
        dataZYXCT = vigra.taggedView(data, self.InputVolume.meta.axistags).withAxes(*"zyxct")

        # walk over time and channel axes
        for t in range(dataZYXCT.shape[4]):
            for c in range(dataZYXCT.shape[3]):
                resultZYXCT[..., c, t] = self._detectMissing(dataZYXCT[..., c, t])

        return result

    def _detectMissing(self, data):
        """
        detects missing regions and labels each missing region with 1
        :param data: 3d data with axistags 'zyx'
        :type data: array-like
        """

        assert (
            data.axistags.index("z") == 0
            and data.axistags.index("y") == 1
            and data.axistags.index("x") == 2
            and len(data.shape) == 3
        ), "Data must be 3d with axis 'zyx'."

        result = np.zeros(data.shape, dtype=np.uint8)

        patchSize = self.PatchSize.value
        haloSize = self.HaloSize.value

        if patchSize is None or not patchSize > 0:
            raise ValueError("PatchSize must be a positive integer")
        if haloSize is None or haloSize < 0:
            raise ValueError("HaloSize must be a non-negative integer")

        maxZ = data.shape[0]

        # walk over slices
        for z in range(maxZ):
            patches, slices = _patchify(data[z, :, :], patchSize, haloSize)
            hists = []
            # walk over patches
            for patch in patches:
                (hist, _) = np.histogram(patch, bins=self.NHistogramBins.value, range=self._inputRange, density=True)
                hists.append(hist)
            hists = np.vstack(hists)

            pred = self.predict(hists, method=self.DetectionMethod.value)
            for i, p in enumerate(pred):
                if p > 0:
                    # patch is classified as missing
                    result[z, slices[i][0], slices[i][1]] |= 1

        return result

    def train(self, force=False):
        """
        trains with samples drawn from slot TrainingHistograms
        (retrains only if bin size is currently untrained or force is True)
        """

        # return early if unneccessary
        if not force and not OpDetectMissing._needsTraining and OpDetectMissing._manager.has(self.NHistogramBins.value):
            return

        # return if we don't have svms
        if not havesklearn:
            return

        logger.debug("Training for {} histogram bins ...".format(self.NHistogramBins.value))

        if self.DetectionMethod.value == "classic" or not havesklearn:
            # no need to train this
            return

        histograms = self.TrainingHistograms[:].wait()

        logger.debug("Finished loading histogram data of shape {}.".format(histograms.shape))

        assert (
            histograms.shape[1] >= self.NHistogramBins.value + 1 and len(histograms.shape) == 2
        ), "Training data has wrong shape (expected: (n,{}), got: {}.".format(
            self.NHistogramBins.value + 1, histograms.shape
        )

        labels = histograms[:, self.NHistogramBins.value]
        histograms = histograms[:, : self.NHistogramBins.value]

        neg_inds = np.where(labels == 0)[0]
        pos_inds = np.setdiff1d(np.arange(len(labels)), neg_inds)

        pos = histograms[pos_inds]
        neg = histograms[neg_inds]
        npos = len(pos)
        nneg = len(neg)

        # prepare for 10-fold cross-validation
        nfolds = 10
        cfp = np.zeros((nfolds,))
        cfn = np.zeros((nfolds,))
        cprec = np.zeros((nfolds,))
        crec = np.zeros((nfolds,))
        pos_random = np.random.permutation(len(pos))
        neg_random = np.random.permutation(len(neg))

        logger.debug(
            "Starting training with " + "{} negative patches and {} positive patches...".format(len(neg), len(pos))
        )
        self._felzenszwalbTraining(neg, pos)
        logger.debug("Finished training.")

        OpDetectMissing._needsTraining = False

    def _felzenszwalbTraining(self, negative, positive):
        """
        we want to train on a 'hard' subset of the training data, see
        FELZENSZWALB ET AL.: OBJECT DETECTION WITH DISCRIMINATIVELY TRAINED PART-BASED MODELS (4.4), PAMI 32/9
        """

        # TODO sanity checks

        n = (self.PatchSize.value + self.HaloSize.value) ** 2
        method = self.DetectionMethod.value

        # set options for Felzenszwalb training
        firstSamples = self._felzenOpts["firstSamples"]
        maxRemovePerStep = self._felzenOpts["maxRemovePerStep"]
        maxAddPerStep = self._felzenOpts["maxAddPerStep"]
        maxSamples = self._felzenOpts["maxSamples"]
        nTrainingSteps = self._felzenOpts["nTrainingSteps"]

        # initial choice of training samples
        (initNegative, choiceNegative, _, _) = _chooseRandomSubset(negative, min(firstSamples, len(negative)))
        (initPositive, choicePositive, _, _) = _chooseRandomSubset(positive, min(firstSamples, len(positive)))

        # setup for parallel training
        samples = [negative, positive]
        choice = [choiceNegative, choicePositive]
        S_t = [initNegative, initPositive]

        finished = [False, False]

        ### BEGIN SUBROUTINE ###
        def felzenstep(x, cache, ind):

            case = ("positive" if ind > 0 else "negative") + " set"
            pred = self.predict(x, method=method)

            hard = np.where(pred != ind)[0]
            easy = np.setdiff1d(list(range(len(x))), hard)
            logger.debug(" {}: currently {} hard and {} easy samples".format(case, len(hard), len(easy)))

            # shrink the cache
            easyInCache = np.intersect1d(easy, cache) if len(easy) > 0 else []
            if len(easyInCache) > 0:
                (removeFromCache, _, _, _) = _chooseRandomSubset(easyInCache, min(len(easyInCache), maxRemovePerStep))
                cache = np.setdiff1d(cache, removeFromCache)
                logger.debug(" {}: shrunk the cache by {} elements".format(case, len(removeFromCache)))

            # grow the cache
            temp = len(cache)
            addToCache = _chooseRandomSubset(hard, min(len(hard), maxAddPerStep))[0]
            cache = np.union1d(cache, addToCache)
            addedHard = len(cache) - temp
            logger.debug(" {}: grown the cache by {} elements".format(case, addedHard))

            if len(cache) > maxSamples:
                logger.debug(" {}: Cache to big, removing elements.".format(case))
                cache = _chooseRandomSubset(cache, maxSamples)[0]

            # apply the cache
            C = x[cache]

            return (C, cache, addedHard == 0)

        ### END SUBROUTINE ###

        ### BEGIN PARALLELIZATION FUNCTION ###
        def partFun(i):
            (C, newChoice, newFinished) = felzenstep(samples[i], choice[i], i)
            S_t[i] = C
            choice[i] = newChoice
            finished[i] = newFinished

        ### END PARALLELIZATION FUNCTION ###

        for k in range(nTrainingSteps):

            logger.debug(
                "Felzenszwalb Training "
                + "(step {}/{}): {} hard negative samples, {}".format(k + 1, nTrainingSteps, len(S_t[0]), len(S_t[1]))
                + "hard positive samples."
            )
            self.fit(S_t[0], S_t[1], method=method)

            pool = RequestPool()

            for i in range(len(S_t)):
                req = Request(partial(partFun, i))
                pool.add(req)

            pool.wait()
            pool.clean()

            if np.all(finished):
                # already have all hard examples in training set
                break

        self.fit(S_t[0], S_t[1], method=method)

        logger.debug(" Finished Felzenszwalb Training.")

    #####################
    ### CLASS METHODS ###
    #####################

    @classmethod
    def fit(cls, negative, positive, method="classic"):
        """
        train the underlying SVM
        """

        if cls._manager is None:
            cls._manager = SVMManager()

        if method == "classic" or not havesklearn:
            return

        assert len(negative.shape) == 2, "Negative training set must have shape (nSamples, nHistogramBins)."
        assert len(positive.shape) == 2, "Positive training set must have shape (nSamples, nHistogramBins)."
        assert (
            negative.shape[1] == positive.shape[1]
        ), "Negative and positive histograms must have the same number of bins."

        nBins = negative.shape[1]

        labels = [0] * len(negative) + [1] * len(positive)
        samples = np.vstack((negative, positive))

        svm = SVC(C=1000, kernel=_histogramIntersectionKernel, scale_C=True)

        svm.fit(samples, labels)
        cls._manager.add(svm, nBins, overwrite=True)

    @classmethod
    def predict(cls, X, method="classic"):
        """
        predict if the histograms in X correspond to missing regions
        do this for subsets of X in parallel
        """

        if cls._manager is None:
            cls._manager = SVMManager()

        assert len(X.shape) == 2, "Prediction data must have shape (nSamples, nHistogramBins)."

        nBins = X.shape[1]

        if method == "classic" or not havesklearn:
            svm = PseudoSVC()
        else:
            try:
                svm = cls._manager.get(nBins)
            except SVMManager.NotTrainedError:
                # fail gracefully if not trained => responsibility of user!
                svm = PseudoSVC()

        y = np.zeros((len(X),)) * np.nan

        pool = RequestPool()

        chunkSize = 1000  # FIXME magic number??
        nChunks = len(X) // chunkSize + (1 if len(X) % chunkSize > 0 else 0)

        s = [slice(k * chunkSize, min((k + 1) * chunkSize, len(X))) for k in range(nChunks)]

        def partFun(i):
            y[s[i]] = svm.predict(X[s[i]])

        for i in range(nChunks):
            req = Request(partial(partFun, i))
            pool.add(req)

        pool.wait()
        pool.clean()

        # not neccessary
        # assert not np.any(np.isnan(y))
        return np.asarray(y)

    @classmethod
    def has(cls, n, method="classic"):

        if cls._manager is None:
            cls._manager = SVMManager()
        logger.debug(str(cls._manager))

        if method == "classic" or not havesklearn:
            return True
        return cls._manager.has(n)

    @classmethod
    def reset(cls):
        cls._manager = SVMManager()
        logger.debug("Reset all detectors.")

    @classmethod
    def dumps(cls):

        if cls._manager is None:
            cls._manager = SVMManager()

        return pickle.dumps(cls._manager.extract(), 0)

    @classmethod
    def loads(cls, s):

        if cls._manager is None:
            cls._manager = SVMManager()

        if len(s) > 0:
            try:
                d = pickle.loads(s)
            except Exception as err:
                logger.error("Failed overloading detector due to an error: {}".format(str(err)))
                return
            cls._manager.overload(d)
            logger.debug("Loaded detector: {}".format(str(cls._manager)))


#############################
#############################
#############################
###                       ###
###         TOOLS         ###
###                       ###
#############################
#############################
#############################


class PseudoSVC(object):
    """
    pseudo SVM
    """

    def __init__(self, *args, **kwargs):
        pass

    def fit(self, *args, **kwargs):
        pass

    def predict(self, *args, **kwargs):
        X = args[0]
        out = np.zeros(len(X))
        for k, patch in enumerate(X):
            out[k] = 1 if np.all(patch[1:] == 0) else 0
        return out


class SVMManager(object):
    """
    manages our SVMs for multiple bin numbers
    """

    _svms = None

    class NotTrainedError(Exception):
        pass

    def __init__(self):
        self._svms = {"version": 1}

    def get(self, n):
        try:
            return self._svms[n]
        except KeyError:
            raise self.NotTrainedError("Detector for bin size {} not trained.\nHave {}.".format(n, self._svms))

    def add(self, svm, n, overwrite=False):
        if not n in list(self._svms.keys()) or overwrite:
            self._svms[n] = svm

    def remove(self, n):
        try:
            del self._svms[n]
        except KeyError:
            # don't fail, just complain
            logger.error("Tried removing a detector which is not trained yet.")

    def has(self, n):
        return n in self._svms

    def extract(self):
        return self._svms

    def overload(self, obj):
        if "version" in obj and obj["version"] == self._svms["version"]:
            self._svms = obj
            return
        else:
            try:
                for n in list(obj["svm"].keys()):
                    for svm in list(obj["svm"][n].values()):
                        self.add(svm, n, overwrite=True)
            except KeyError:
                # don't fail, just complain
                logger.error("Detector overload format not recognized, " "no detector loaded.")

    def __str__(self):
        return str(self._svms)


def _chooseRandomSubset(data, n):
    choice = np.random.permutation(len(data))
    return (data[choice[:n]], choice[:n], data[choice[n:]], choice[n:])


def _patchify(data, patchSize, haloSize):
    """
    data must be 2D y-x

    returns (patches, slices)
    """

    patches = []
    slices = []
    nPatchesX = data.shape[1] // patchSize + (1 if data.shape[1] % patchSize > 0 else 0)
    nPatchesY = data.shape[0] // patchSize + (1 if data.shape[0] % patchSize > 0 else 0)

    for y in range(nPatchesY):
        for x in range(nPatchesX):
            right = min((x + 1) * patchSize + haloSize, data.shape[1])
            bottom = min((y + 1) * patchSize + haloSize, data.shape[0])

            rightIsIncomplete = (x + 1) * patchSize > data.shape[1]
            bottomIsIncomplete = (y + 1) * patchSize > data.shape[0]

            left = max(x * patchSize - haloSize, 0) if not rightIsIncomplete else max(0, right - patchSize - haloSize)
            top = max(y * patchSize - haloSize, 0) if not bottomIsIncomplete else max(0, bottom - patchSize - haloSize)

            patches.append(data[top:bottom, left:right])

            if rightIsIncomplete:
                horzSlice = slice(max(data.shape[1] - patchSize, 0), data.shape[1])
            else:
                horzSlice = slice(patchSize * x, patchSize * (x + 1))

            if bottomIsIncomplete:
                vertSlice = slice(max(data.shape[0] - patchSize, 0), data.shape[0])
            else:
                vertSlice = slice(patchSize * y, patchSize * (y + 1))

            slices.append((vertSlice, horzSlice))

    return (patches, slices)


def _histogramIntersectionKernel(X, Y):
    """
    implements the histogram intersection kernel in a fancy way
    (standard: k(x,y) = sum(min(x_i,y_i)) )
    """

    A = X.reshape((X.shape[0], 1, X.shape[1]))
    B = Y.reshape((1,) + Y.shape)

    return np.sum(np.minimum(A, B), axis=2)


def _defaultTrainingHistograms():
    """
    produce a standard training set with black regions
    """

    nHists = 100
    n = _defaultBinSize + 1
    hists = np.zeros((nHists, n))

    # generate nHists/2 positive sets
    for i in range(nHists // 2):
        (hists[i, : n - 1], _) = np.histogram(
            np.zeros((64, 64), dtype=np.uint8), bins=_defaultBinSize, range=(0, 255), density=True
        )
        hists[i, n - 1] = 1

    for i in range(nHists // 2, nHists):
        (hists[i, : n - 1], _) = np.histogram(
            np.random.randint(60, 181, (64, 64)), bins=_defaultBinSize, range=(0, 255), density=True
        )

    return hists


#####################################
### HISTOGRAM EXTRACTION FUNCTION ###
#####################################


def extractHistograms(volume, labels, patchSize=64, haloSize=0, nBins=30, intRange=(0, 255), appendPositions=False):
    """
    extracts histograms from 3d-volume
     - labels are
        0       ignore
        1       positive
        2       negative
     - histogram extraction is attempted to be done in parallel
     - patches that intersect with the volume border are discarded
     - volume and labels must be 3d, and in order 'zyx' (if not VigraArrays)
     - returns: np.ndarray, shape: (nSamples,nBins+1), last column is the label
    """

    # progress reporter class, histogram extraction can take quite a long time
    class ProgressReporter(object):

        lock = None

        def __init__(self, nThreads):
            self.lock = ThreadLock()
            self.nThreads = nThreads
            self.status = np.zeros((nThreads,))

        def report(self, index):
            self.lock.acquire()
            self.status[index] = 1
            logger.debug("Finished threads: %d/%d." % (self.status.sum(), len(self.status)))
            self.lock.release()

    # sanity checks
    assert len(volume.shape) == 3, "Volume must be 3d data"
    assert volume.shape == labels.shape, "Volume and labels must have the same shape"

    try:
        volumeZYX = volume.withAxes(*"zyx")
        labelsZYX = labels.withAxes(*"zyx")
    except AttributeError:
        # can't blame me
        volumeZYX = volume
        labelsZYX = labels
        pass

    # compute actual patch size
    patchSize = patchSize + 2 * haloSize

    # fill list of patch centers (VigraArray does not support bitwise_or)
    ind_z, ind_y, ind_x = np.where((labelsZYX == 1).view(np.ndarray) | (labelsZYX == 2).view(np.ndarray))
    index = np.arange(len(ind_z))

    # prepare chunking of histogram centers
    chunkSize = 10000  # FIXME magic number??
    nChunks = len(index) // chunkSize + (1 if len(index) % chunkSize > 0 else 0)
    sliceList = [slice(k * chunkSize, min((k + 1) * chunkSize, len(index))) for k in range(nChunks)]
    histoList = [None] * nChunks

    # prepare subroutine for parallel extraction
    reporter = ProgressReporter(nChunks)

    # BEGIN subroutine
    def _extractHistogramsSub(itemList):

        xs = ind_x[itemList]
        ys = ind_y[itemList]
        zs = ind_z[itemList]

        ymin = ys - patchSize // 2
        ymax = ymin + patchSize

        xmin = xs - patchSize // 2
        xmax = xmin + patchSize

        validPatchIndices = np.where(
            np.all((ymin >= 0, xmin >= 0, xmax <= volumeZYX.shape[2], ymax <= volumeZYX.shape[1]), axis=0)
        )[0]

        if appendPositions:
            out = np.zeros((len(validPatchIndices), nBins + 4))
        else:
            out = np.zeros((len(validPatchIndices), nBins + 1))

        for k, patchInd in enumerate(validPatchIndices):
            x = xs[patchInd]
            y = ys[patchInd]
            z = zs[patchInd]

            vol = volumeZYX[z, ymin[patchInd] : ymax[patchInd], xmin[patchInd] : xmax[patchInd]]
            (out[k, :nBins], _) = np.histogram(vol, bins=nBins, range=intRange, density=True)
            out[k, nBins] = 1 if labelsZYX[z, y, x] == 1 else 0
            if appendPositions:
                out[k, nBins + 1 :] = [z, y, x]

        return out

    def partFun(i):
        itemList = index[sliceList[i]]
        histos = _extractHistogramsSub(itemList)
        histoList[i] = histos

        reporter.report(i)

    # END subroutine

    # pool the extraction requests
    pool = RequestPool()

    for i in range(nChunks):
        req = Request(partial(partFun, i))
        pool.add(req)

    pool.wait()
    pool.clean()

    return np.vstack(histoList)


############################
############################
############################
###                      ###
###         MAIN         ###
###                      ###
############################
############################
############################


def toH5(data, pathOrGroup, pathInFile, compression=None):
    try:
        return vigra.impex.writeHDF5(data, pathOrGroup, pathInFile, compression)
    except TypeError:
        # old vigra does not support compression
        logger.debug("'compression' argument not yet supported by vigra.")
        return vigra.impex.writeHDF5(data, pathOrGroup, pathInFile)


if __name__ == "__main__":

    import argparse
    import os.path
    from sys import exit
    import time
    import csv

    from lazyflow.graph import Graph

    from lazyflow.operators.opDetectMissingData import _histogramIntersectionKernel

    logging.basicConfig()
    logger.setLevel(logging.INFO)

    thisTime = time.strftime("%Y-%m-%d_%H.%M")

    # BEGIN ARGPARSE

    parser = argparse.ArgumentParser(
        description="Train a missing slice detector"
        + """
        Example invocation:
        python2 opDetectMissingData.py block1_test.h5 block1_testLabels.h5 --patch 64 --halo 32 --bins 30 -d ~/testing/2013_08_16 -t 9-12 --opts 200,0,400,1000,2 --shape "(1024,1024,14)"
        """
    )

    parser.add_argument(
        "file",
        nargs="*",
        action="store",
        help="volume and labels (if omitted, the working directory must contain histogram files)",
    )

    parser.add_argument(
        "-d",
        "--directory",
        dest="directory",
        action="store",
        default="/tmp",
        help="working directory, histograms and detector file will be stored there",
    )

    parser.add_argument(
        "-t",
        "--testingrange",
        dest="testingrange",
        action="store",
        default=None,
        help='the z range of the labels that are for testing (like "0-3,11,17-19" which would evaluate to [0,1,2,3,11,17,18,19])',
    )

    parser.add_argument(
        "-f",
        "--force",
        dest="force",
        action="store_true",
        default=False,
        help="force extraction of histograms, even if the directory already contains histograms",
    )

    parser.add_argument(
        "--patch", dest="patchSize", action="store", default="64", help='patch size (e.g.: "32,64-128")'
    )
    parser.add_argument("--halo", dest="haloSize", action="store", default="64", help='halo size (e.g.: "32,64-128")')
    parser.add_argument(
        "--bins", dest="binSize", action="store", default="30", help='number of histogram bins (e.g.: "10-15,20")'
    )

    parser.add_argument(
        "--shape",
        dest="shape",
        action="store",
        default=None,
        help='shape of the volume in tuple notation "(x,y,z)" (only neccessary if loading histograms from file)',
    )

    parser.add_argument(
        "--opts",
        dest="opts",
        action="store",
        default="250,0,250,1000,4",
        help="<initial number of samples>,<maximum number of samples removed per step>,<maximum number of samples added per step>,"
        + "<maximum number of samples>,<number of steps> (e.g. 250,0,250,1000,4)",
    )

    args = parser.parse_args()

    # END ARGPARSE

    # BEGIN FILESYSTEM

    workingdir = args.directory
    assert os.path.isdir(workingdir), "Directory '{}' does not exist.".format(workingdir)
    for f in args.file:
        assert os.path.isfile(f), "'{}' does not exist.".format(f)

    # END FILESYSTEM

    # BEGIN NORMALIZE

    def _expand(rangelist):
        if rangelist is not None:
            singleRanges = rangelist.split(",")
            expandedRanges = []
            for r in singleRanges:
                r2 = r.split("-")
                if len(r2) == 1:
                    expandedRanges.append(int(r))
                elif len(r2) == 2:
                    for i in range(int(r2[0]), int(r2[1]) + 1):
                        expandedRanges.append(i)
                else:
                    logger.error("Syntax Error: '{}'".format(r))
                    exit(33)
            return np.asarray(expandedRanges)
        else:
            return np.zeros((0,))

    testrange = _expand(args.testingrange)

    patchSizes = _expand(args.patchSize)
    haloSizes = _expand(args.haloSize)
    binSizes = _expand(args.binSize)

    try:
        opts = [int(opt) for opt in args.opts.split(",")]
        assert len(opts) == 5
        opts = dict(
            list(zip(["firstSamples", "maxRemovePerStep", "maxAddPerStep", "maxSamples", "nTrainingSteps"], opts))
        )
    except:
        raise ValueError("Cannot parse '--opts' argument '{}'".format(args.opts))

    # END NORMALIZE

    csvfile = open(os.path.join(workingdir, "%s_test_results.tsv" % (thisTime,)), "w")
    csvwriter = csv.DictWriter(
        csvfile,
        fieldnames=("patch", "halo", "bins", "recall", "precision"),
        delimiter=" ",
        quotechar='"',
        quoting=csv.QUOTE_MINIMAL,
    )
    csvwriter.writeheader()

    op = OpDetectMissing(graph=Graph())
    op._felzenOpts = opts

    logger.info("Starting training script ({})".format(time.strftime("%Y-%m-%d %H:%M")))
    t_start = time.time()

    # iterate training conditions
    for patchSize in patchSizes:
        for haloSize in haloSizes:
            for binSize in binSizes:

                histfile = os.path.join(workingdir, "histograms_%d_%d_%d.h5" % (patchSize, haloSize, binSize))
                detfile = os.path.join(
                    workingdir, "%s_detector_%d_%d_%d.pkl" % (thisTime, patchSize, haloSize, binSize)
                )
                predfile = os.path.join(
                    workingdir, "%s_prediction_results_%d_%d_%d.h5" % (thisTime, patchSize, haloSize, binSize)
                )

                startFromLabels = args.force or not os.path.exists(histfile)

                # EXTRACT HISTOGRAMS
                if startFromLabels:
                    logger.info(
                        "Gathering histograms from {} patches (this could take a while) ...".format(
                            (patchSize, haloSize, binSize)
                        )
                    )
                    assert (
                        len(args.file) == 2
                    ), "If there are no histograms available, volume and labels must be provided."

                    locs = ["/volume/data", "/cube"]

                    volume = None
                    labels = None

                    for l in locs:
                        try:
                            volume = vigra.impex.readHDF5(args.file[0], l).withAxes(*"zyx")
                            break
                        except KeyError:
                            pass
                    if volume is None:
                        logger.error("Could not find a volume in {} with paths {}".format(args.file[0], locs))
                        csvfile.close()
                        exit(42)

                    for l in locs:
                        try:
                            labels = vigra.impex.readHDF5(args.file[1], "/volume/data").withAxes(*"zyx")
                            break
                        except KeyError:
                            pass
                    if labels is None:
                        logger.error("Could not find a volume in {} with paths {}".format(args.file[1], locs))
                        csvfile.close()
                        exit(43)

                    volShape = volume.withAxes(*"xyz").shape

                    # bear with me, complicated axistags stuff is neccessary
                    # for my old vigra to work
                    trainrange = np.setdiff1d(np.arange(volume.shape[0]), testrange)

                    trainData = vigra.taggedView(volume[trainrange, :, :], axistags=vigra.defaultAxistags("zyx"))
                    trainLabels = vigra.taggedView(labels[trainrange, :, :], axistags=vigra.defaultAxistags("zyx"))

                    trainHistograms = extractHistograms(
                        trainData,
                        trainLabels,
                        patchSize=patchSize,
                        haloSize=haloSize,
                        nBins=binSize,
                        intRange=(0, 255),
                        appendPositions=True,
                    )

                    if len(testrange) > 0:
                        testData = vigra.taggedView(volume[testrange, :, :], axistags=vigra.defaultAxistags("zyx"))
                        testLabels = vigra.taggedView(labels[testrange, :, :], axistags=vigra.defaultAxistags("zyx"))

                        testHistograms = extractHistograms(
                            testData,
                            testLabels,
                            patchSize=patchSize,
                            haloSize=haloSize,
                            nBins=binSize,
                            intRange=(0, 255),
                            appendPositions=True,
                        )
                    else:
                        testHistograms = np.zeros((0, trainHistograms.shape[1]))

                    vigra.impex.writeHDF5(trainHistograms, histfile, "/volume/train")
                    if len(testHistograms) > 0:
                        vigra.impex.writeHDF5(testHistograms, histfile, "/volume/test")
                    logger.info("Dumped histograms to '{}'.".format(histfile))

                else:
                    logger.info("Gathering histograms from file...")
                    trainHistograms = vigra.impex.readHDF5(histfile, "/volume/train")
                    try:
                        testHistograms = vigra.impex.readHDF5(histfile, "/volume/test")
                    except KeyError:
                        testHistograms = np.zeros((0, trainHistograms.shape[1]))
                    logger.info("Loaded histograms from '{}'.".format(histfile))

                    assert trainHistograms.shape[1] == binSize + 4
                    assert testHistograms.shape[1] == binSize + 4

                    if len(testHistograms) > 0:
                        if args.shape is None:
                            logger.warning("Guessing the shape of the original data...")
                            volShape = (1024, 1024, 512)
                        else:
                            volShape = eval(args.shape)
                            assert isinstance(volShape, tuple) and len(volShape) == 3

                    assert not np.any(np.isinf(trainHistograms))
                    assert not np.any(np.isnan(trainHistograms))

                    assert not np.any(np.isinf(testHistograms))
                    assert not np.any(np.isnan(testHistograms))

                # TRAIN

                logger.info("Training...")

                op.PatchSize.setValue(patchSize)
                op.HaloSize.setValue(haloSize)
                op.DetectionMethod.setValue("svm")
                op.NHistogramBins.setValue(binSize)

                op.TrainingHistograms.setValue(trainHistograms[:, : binSize + 1])

                op.train(force=True)

                # save detector
                try:
                    if detfile is None:
                        with tempfile.NamedTemporaryFile(suffix=".pkl", prefix="detector_", delete=False) as f:
                            f.write(op.dumps())
                    else:
                        with open(detfile, "w") as f:
                            logger.info("Detector written to {}".format(f.name))
                            f.write(op.dumps())

                    logger.info("Detector written to {}".format(f.name))
                except Exception as e:
                    logger.error("==== BEGIN DETECTOR DUMP ====")
                    logger.error(op.dumps())
                    logger.error("==== END DETECTOR DUMP ====")
                    logger.error(str(e))

                if len(testHistograms) == 0:
                    # no testing required
                    continue

                logger.info("Testing...")

                # split into histos, positions and labels
                hists = testHistograms[:, :binSize]
                labels = testHistograms[:, binSize]
                zyxPos = testHistograms[:, binSize + 1 :]

                pred = op.predict(hists, method="svm")
                predNeg = pred[np.where(labels == 0)[0]]
                predPos = pred[np.where(labels == 1)[0]]

                fp = (predNeg.sum()) / float(predNeg.size)
                fn = (predPos.size - predPos.sum()) / float(predPos.size)

                prec = predPos.sum() / float(predPos.sum() + predNeg.sum())
                recall = 1 - fn

                logger.info(
                    " Predicted {} histograms with patchSize={}, haloSize={}, bins={}.".format(
                        len(hists), patchSize, haloSize, binSize
                    )
                )
                logger.info(" FPR=%.5f, FNR=%.5f (recall=%.5f, precision=%.5f)." % (fp, fn, recall, prec))
                csvwriter.writerow(
                    {"patch": patchSize, "halo": haloSize, "bins": binSize, "recall": recall, "precision": prec}
                )

                logger.info("Writing prediction volume...")

                predVol = vigra.VigraArray(
                    np.zeros(volShape, dtype=np.uint8), axistags=vigra.defaultAxistags("xyz")
                ).withAxes(*"zyx")

                for i, p in enumerate(pred):
                    predVol[testrange[zyxPos[i][0]], zyxPos[i][1], zyxPos[i][2]] = p

                toH5(predVol, predfile, "/volume/data", compression="GZIP")

    logger.info("Finished training script ({})".format(time.strftime("%Y-%m-%d %H:%M")))

    t_stop = time.time()

    logger.info("Duration: {}".format(time.strftime("%Hh, %Mm, %Ss", time.gmtime((t_stop - t_start) % (24 * 60 * 60)))))
    if (t_stop - t_start) >= 24 * 60 * 60:
        logger.info(" and %d days!" % int(t_stop - t_start) // (24 * 60 * 60))

    csvfile.close()
