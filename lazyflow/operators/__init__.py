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
from . import classifierOperators, filterOperators, generic, operators, valueProviders
from .classifierOperators import (
    OpBaseClassifierPredict,
    OpClassifierPredict,
    OpPixelwiseClassifierPredict,
    OpTrainClassifierBlocked,
    OpTrainClassifierFromFeatureVectors,
    OpTrainPixelwiseClassifierBlocked,
    OpTrainVectorwiseClassifierBlocked,
    OpVectorwiseClassifierPredict,
)
from .filterOperators import (
    OpBaseFilter,
    OpDifferenceOfGaussians,
    OpGaussianGradientMagnitude,
    OpGaussianSmoothing,
    OpHessianOfGaussian,
    OpHessianOfGaussianEigenvalues,
    OpHessianOfGaussianEigenvaluesFirst,
    OpLaplacianOfGaussian,
    OpStructureTensorEigenvalues,
)
from .generic import (
    OpConvertDtype,
    OpDtypeView,
    OpMaxChannelIndicatorOperator,
    OpMultiArrayMerger,
    OpMultiArraySlicer2,
    OpMultiArrayStacker,
    OpMultiInputConcatenater,
    OpPixelOperator,
    OpSelectSubslot,
    OpSingleChannelSelector,
    OpSubRegion,
    OpTransposeSlots,
    OpWrapSlot,
)
from .opArrayPiper import OpArrayPiper
from .opBlockedArrayCache import OpBlockedArrayCache
from .opCacheFixer import OpCacheFixer
from .opCompressedCache import OpCompressedCache
from .opCompressedUserLabelArray import OpCompressedUserLabelArray
from .opConcatenateFeatureMatrices import OpConcatenateFeatureMatrices
from .opFeatureMatrixCache import OpFeatureMatrixCache
from .opFilterLabels import OpFilterLabels
from .opInterpMissingData import OpInterpMissingData
from .opLabelImage import OpLabelImage
from .opLabelVolume import OpLabelVolume
from .opObjectFeatures import OpObjectFeatures
from .opPixelFeaturesPresmoothed import OpPixelFeaturesPresmoothed
from .opRelabelConsecutive import OpRelabelConsecutive
from .opReorderAxes import OpReorderAxes
from .opSimpleBlockedArrayCache import OpSimpleBlockedArrayCache
from .opSimpleStacker import OpSimpleStacker
from .opSlicedBlockedArrayCache import OpSlicedBlockedArrayCache
from .opUnblockedArrayCache import OpUnblockedArrayCache
from .opVigraLabelVolume import OpVigraLabelVolume
from .opVigraWatershed import OpVigraWatershed
from .valueProviders import (
    ListToMultiOperator,
    OpAttributeSelector,
    OpDummyData,
    OpMetadataInjector,
    OpMetadataMerge,
    OpMetadataSelector,
    OpOutputProvider,
    OpPrecomputedInput,
    OpValueCache,
    OpZeroDefault,
    OpRaisingSource,
)
