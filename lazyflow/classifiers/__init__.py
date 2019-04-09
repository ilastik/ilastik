from __future__ import absolute_import
from .lazyflowClassifier import (
    LazyflowVectorwiseClassifierABC,
    LazyflowVectorwiseClassifierFactoryABC,
    LazyflowPixelwiseClassifierABC,
    LazyflowPixelwiseClassifierFactoryABC,
    LazyflowOnlineClassifier,
)
from .vigraRfLazyflowClassifier import VigraRfLazyflowClassifier, VigraRfLazyflowClassifierFactory
from .parallelVigraRfLazyflowClassifier import (
    ParallelVigraRfLazyflowClassifier,
    ParallelVigraRfLazyflowClassifierFactory,
)
from .sklearnLazyflowClassifier import SklearnLazyflowClassifier, SklearnLazyflowClassifierFactory

try:
    from .tiktorchLazyflowClassifier import TikTorchLazyflowClassifierFactory
    has_tiktorch = True
except ImportError as err:
    has_tiktorch = False
    import sys
    import warnings
    import_err = err

    class Raise:
        def __init__(self, *args, **kwargs):
            raise import_err

    TikTorchLazyflowClassifierFactory = Raise
    warnings.warn("Could not import tiktorch classifier")

# Testing
from .vigraRfPixelwiseClassifier import VigraRfPixelwiseClassifier, VigraRfPixelwiseClassifierFactory
