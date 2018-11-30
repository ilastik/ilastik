from __future__ import absolute_import
from .lazyflowClassifier import LazyflowVectorwiseClassifierABC, LazyflowVectorwiseClassifierFactoryABC, LazyflowPixelwiseClassifierABC, LazyflowPixelwiseClassifierFactoryABC
from .vigraRfLazyflowClassifier import VigraRfLazyflowClassifier, VigraRfLazyflowClassifierFactory
from .parallelVigraRfLazyflowClassifier import ParallelVigraRfLazyflowClassifier, ParallelVigraRfLazyflowClassifierFactory
from .sklearnLazyflowClassifier import SklearnLazyflowClassifier, SklearnLazyflowClassifierFactory

try:
    from .tiktorchLazyflowClassifier import TikTorchLazyflowClassifier, TikTorchLazyflowClassifierFactory
except ImportError:
    import warnings
    warnings.warn("init: Could not import tiktorch classifier")

# Testing
from .vigraRfPixelwiseClassifier import VigraRfPixelwiseClassifier, VigraRfPixelwiseClassifierFactory
from .tiktorchLazyflowClassifier import *