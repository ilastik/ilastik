from __future__ import print_function

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
###############################################################################
"""
Object Extraction Performance Benchmark

This script benchmarks the performance of different object extraction methods:
1. Simple single-threaded direct approach
2. Multi-threaded operator-based approach from ilastik
3. Basic multi-threaded implementation without operator overhead

Usage:
    python object_extraction_benchmark.py

The script generates synthetic 4D data (time, x, y, channel) with simple objects
and measures the time taken by each method to extract standard object features.
"""

from builtins import range
import numpy as np
import vigra

from lazyflow.graph import Graph
from lazyflow.operators import OpLabelVolume
from lazyflow.utility import Timer
from lazyflow.operators.opReorderAxes import OpReorderAxes
from lazyflow.operators.opBlockedArrayCache import OpBlockedArrayCache
from lazyflow.request import Request, RequestPool

from functools import partial

from ilastik.applets.objectExtraction.opObjectExtraction import OpObjectExtraction
from lazyflow.graph import Operator, InputSlot, OutputSlot

import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

import logging

logger = logging.getLogger(__name__)

# Define the set of features to extract
NAME = "Standard Object Features"

FEATURES = {
    NAME: {
        "Count": {},                       # Total count of pixels in object
        "RegionCenter": {},                # Center of mass
        "Coord<Principal<Kurtosis>>": {},  # Measure of shape "peakedness"
        "Coord<Minimum>": {},              # Minimum coordinates (bounding box)
        "Coord<Maximum>": {},              # Maximum coordinates (bounding box)
    }
}

# Feature cleanup functions
def cleanup_key(k):
    """
    Remove spaces from feature keys for consistency.
    """
    return k.replace(" ", "")


def cleanup_value(val, nObjects, isGlobal):
    """
    Ensure that the value is a numpy array with the correct shape.
    
    Parameters:
        val (any): The feature value to clean up
        nObjects (int): Number of objects including background
        isGlobal (bool): Whether the feature is global
        
    Returns:
        numpy.ndarray: Properly shaped array of feature values
    """
    val = np.asarray(val)

    if val.ndim == 0 or isGlobal:
        # repeat the global values for all the objects
        scalar = val.reshape((1,))[0]
        val = np.zeros((nObjects, 1), dtype=val.dtype)
        val[:, 0] = scalar

    if val.ndim == 1:
        val = val.reshape(-1, 1)

    if val.ndim > 2:
        val = val.reshape(val.shape[0], -1)

    assert val.shape[0] == nObjects
    # remove background (object with label 0)
    val = val[1:]
    return val


def cleanup(d, nObjects, features):
    """
    Clean up the feature dictionary by formatting keys and values consistently.
    
    Parameters:
        d (dict): Raw feature dictionary from vigra
        nObjects (int): Number of objects including background
        features (list): List of feature names to keep
        
    Returns:
        dict: Cleaned feature dictionary
    """
    result = dict((cleanup_key(k), cleanup_value(v, nObjects, "Global" in k)) for k, v in d.items())
    newkeys = set(result.keys()) & set(features)
    return dict((k, result[k]) for k in newkeys)


def binaryImage():
    """
    Generate a synthetic 4D binary image with simple objects.
    
    Returns:
        vigra.VigraArray: 4D binary image with shape (500, 100, 100, 1)
    """
    frameNum = 500

    img = np.zeros((frameNum, 100, 100, 1), dtype=np.float32)

    # Create 4 objects in each frame
    for frame in range(frameNum):
        img[frame, 0:10, 0:10, 0] = 1       # Small square in top-left
        img[frame, 20:30, 20:30, 0] = 1     # Medium square in middle-left
        img[frame, 40:45, 40:45, 0] = 1     # Tiny square in middle
        img[frame, 60:80, 60:80, 0] = 1     # Large square in bottom-right

    img = img.view(vigra.VigraArray)
    img.axistags = vigra.defaultAxistags("txyc")  # time, x, y, channel

    return img


def rawImage():
    """
    Generate a synthetic 4D raw intensity image with varying intensities for objects.
    
    Returns:
        vigra.VigraArray: 4D intensity image with shape (500, 100, 100, 1)
    """
    frameNum = 500

    img = np.zeros((frameNum, 100, 100, 1), dtype=np.float32)

    # Create 4 objects with different intensities in each frame
    for frame in range(frameNum):
        img[frame, 0:10, 0:10, 0] = 200     # Bright square in top-left
        img[frame, 20:30, 20:30, 0] = 100   # Medium brightness square in middle-left
        img[frame, 40:45, 40:45, 0] = 150   # Bright-medium square in middle
        img[frame, 60:80, 60:80, 0] = 75    # Dim square in bottom-right

    img = img.view(vigra.VigraArray)
    img.axistags = vigra.defaultAxistags("txyc")  # time, x, y, channel

    return img


class OpObjectFeaturesSimplified(Operator):
    """
    Simplified operator for object feature extraction.
    
    This operator extracts object features directly without the overhead
    of the complete ilastik object extraction framework.
    
    Inputs:
        RawVol: Raw intensity image
        BinaryVol: Binary mask image
        
    Outputs:
        Features: Extracted object features
    """
    RawVol = InputSlot()
    BinaryVol = InputSlot()
    Features = OutputSlot()

    def setupOutputs(self):
        """Configure the output slot based on input metadata."""
        taggedOutputShape = self.BinaryVol.meta.getTaggedShape()
        self.Features.meta.shape = (taggedOutputShape["t"],)
        self.Features.meta.axistags = vigra.defaultAxistags("t")
        self.Features.meta.dtype = object  # Storing feature dicts

    def execute(self, slot, subindex, roi, result):
        """Execute the operator for the given ROI."""
        t_ind = self.RawVol.meta.axistags.index("t")

        for res_t_ind, t in enumerate(range(roi.start[t_ind], roi.stop[t_ind])):
            result[res_t_ind] = self._computeFeatures(t_ind, t)

    def propagateDirty(self, slot, subindex, roi, key, oldkey):
        """Mark outputs as dirty when inputs change."""
        self.Features.setDirty(roi)

    def _computeFeatures(self, t_ind, t):
        """
        Compute features for a single time point.
        
        Parameters:
            t_ind (int): Index of time dimension
            t (int): Time point to process
            
        Returns:
            dict: Dictionary of computed features
        """
        # Create ROI for the requested time point
        roi = [slice(None) for i in range(len(self.RawVol.meta.shape))]
        roi[t_ind] = slice(t, t + 1)
        roi = tuple(roi)

        # Get raw and binary volumes
        rawVol = self.RawVol(roi).wait()
        binaryVol = self.BinaryVol(roi).wait()

        # Connected components (label each separate object)
        labelVol = vigra.analysis.labelImageWithBackground(binaryVol.squeeze(), background_value=int(0))

        # Compute features
        features = ["Count", "Coord<Minimum>", "RegionCenter", "Coord<Principal<Kurtosis>>", "Coord<Maximum>"]
        res = vigra.analysis.extractRegionFeatures(
            rawVol.squeeze().astype(np.float32), labelVol.squeeze().astype(np.uint32), features, ignoreLabel=0
        )

        # Cleanup results
        local_features = [x for x in features if "Global<" not in x]
        nobj = res[local_features[0]].shape[0]
        return cleanup(res, nobj, features)


class ObjectExtractionTimeComparison(object):
    """
    Benchmark class for comparing object extraction performance.
    
    This class sets up the necessary operators and runs three different
    approaches for object feature extraction:
    1. Simple single-threaded approach
    2. ilastik's OpObjectExtraction (multi-threaded)
    3. Basic multi-threaded implementation
    """
    def __init__(self):
        """
        Initialize the benchmark with synthetic images and operators.
        
        Note: You can uncomment the following lines to adjust memory and threads:
            lazyflow.request.Request.reset_thread_pool(2)
            Memory.setAvailableRam(500*1024**2)
        """
        # Generate synthetic test images
        binary_img = binaryImage()
        raw_img = rawImage()

        # Create operator graph
        g = Graph()

        # Set up reorder axis operators to ensure consistent axis ordering
        self.op5Raw = OpReorderAxes(graph=g)
        self.op5Raw.AxisOrder.setValue("txyzc")
        self.op5Raw.Input.setValue(raw_img)

        self.op5Binary = OpReorderAxes(graph=g)
        self.op5Binary.AxisOrder.setValue("txyzc")
        self.op5Binary.Input.setValue(binary_img)

        # Cache operators to store intermediate results
        self.opCacheRaw = OpBlockedArrayCache(graph=g)
        self.opCacheRaw.Input.connect(self.op5Raw.Output)
        self.opCacheRaw.BlockShape.setValue((1,) + self.op5Raw.Output.meta.shape[1:])

        self.opCacheBinary = OpBlockedArrayCache(graph=g)
        self.opCacheBinary.Input.connect(self.op5Binary.Output)
        self.opCacheBinary.BlockShape.setValue((1,) + self.op5Binary.Output.meta.shape[1:])

        # Label volume operator to identify connected components
        self.opLabel = OpLabelVolume(graph=g)
        self.opLabel.Input.connect(self.op5Binary.Output)

        # Standard ilastik object extraction operator
        self.opObjectExtraction = OpObjectExtraction(graph=g)
        self.opObjectExtraction.RawImage.connect(self.op5Raw.Output)
        self.opObjectExtraction.BinaryImage.connect(self.op5Binary.Output)
        self.opObjectExtraction.Features.setValue(FEATURES)

        # Simplified object features operator (minimal overhead)
        self.opObjectFeaturesSimp = OpObjectFeaturesSimplified(graph=g)
        self.opObjectFeaturesSimp.RawVol.connect(self.opCacheRaw.Output)
        self.opObjectFeaturesSimp.BinaryVol.connect(self.opCacheBinary.Output)

    def run(self):
        """
        Run the benchmark comparing the three different methods.
        
        Uncomment the cache loading section if you want to prefill caches
        before benchmarking to eliminate I/O overhead.
        """
        # Uncomment to pre-load caches before benchmarks
        # with Timer() as timerCaches:
        #     rawVol = self.opCacheRaw.Output([]).wait()
        #     binaryVol = self.opCacheBinary.Output([]).wait()
        # print("Caches took {} secs".format(timerCaches.seconds()))
        # del rawVol
        # del binaryVol

        # Benchmark 1: Simple single-threaded approach
        print("\nStarting object extraction simplified (single-thread, without cache)")
        with Timer() as timerObjectFeaturesSimp:
            featsObjectFeaturesSimp = self.opObjectFeaturesSimp.Features([]).wait()
        print("Simplified object extraction took: {} seconds".format(timerObjectFeaturesSimp.seconds()))

        # Benchmark 2: ilastik's OpObjectExtraction (multi-threaded)
        print("\nStarting object extraction (multi-thread, without cache)")
        with Timer() as timerObjectExtraction:
            featsObjectExtraction = self.opObjectExtraction.RegionFeatures([]).wait()
        print("Object extraction took: {} seconds".format(timerObjectExtraction.seconds()))

        # Benchmark 3: Basic multi-threaded implementation
        print("\nStarting basic multi-threaded feature computation")
        featsBasicFeatureComp = dict.fromkeys(list(range(self.op5Raw.Output.meta.shape[0])), None)
        
        pool = RequestPool()
        for t in range(0, self.op5Raw.Output.meta.shape[0], 1):
            pool.add(Request(partial(self._computeObjectFeatures, t, featsBasicFeatureComp)))

        with Timer() as timerBasicFeatureComp:
            pool.wait()
        print("Basic multi-threaded feature extraction took: {} seconds".format(timerBasicFeatureComp.seconds()))

    def _computeObjectFeatures(self, t, result):
        """
        Compute object features for a single time point.
        
        This is used by the direct multi-threaded implementation.
        
        Parameters:
            t (int): Time point to process
            result (dict): Dictionary to store results
        """
        # Create ROI for the requested time point
        roi = [slice(None) for i in range(len(self.op5Raw.Output.meta.shape))]
        roi[0] = slice(t, t + 1)
        roi = tuple(roi)

        # Get image data directly from source (uncomment to use cache instead)
        # rawVol = self.opCacheRaw.Output(roi).wait()
        # binaryVol = self.opCacheBinary.Output(roi).wait()
        rawVol = self.op5Raw.Output(roi).wait()
        binaryVol = self.op5Binary.Output(roi).wait()

        # List of features to extract
        features = ["Count", "Coord<Minimum>", "RegionCenter", "Coord<Principal<Kurtosis>>", "Coord<Maximum>"]

        for i in range(t, t + 1):
            # Label objects
            labelVol = vigra.analysis.labelImageWithBackground(binaryVol[i - t].squeeze(), background_value=int(0))
            
            # Extract features
            res = vigra.analysis.extractRegionFeatures(
                rawVol[i - t].squeeze().astype(np.float32),
                labelVol.squeeze().astype(np.uint32),
                features,
                ignoreLabel=0,
            )

            # Cleanup results
            local_features = [x for x in features if "Global<" not in x]
            nobj = res[local_features[0]].shape[0]
            result[i] = cleanup(res, nobj, features)


if __name__ == "__main__":
    """
    Main entry point for the benchmark.
    
    Creates an instance of the benchmark class and runs it,
    comparing performance of different object extraction methods.
    """
    # Run object extraction comparison
    objectExtractionTimeComparison = ObjectExtractionTimeComparison()
    objectExtractionTimeComparison.run()
