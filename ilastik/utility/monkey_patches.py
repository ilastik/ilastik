# This file is the first import for any workflow.
# It implements any monkey-patching that is necessary for any of the libraries that ilastik uses.
# For now, there's just one monkeypatched library (numpy.ndarray)

# h5py complains if it is imported after numpy has been patched, so import it first.
import h5py

# Monkey-patch ndarray to always init with nans.
# (Hopefully this will help us track down a bug...)
import numpy
from abc import ABCMeta
original_ndarray = numpy.ndarray
class nan_ndarray(numpy.ndarray):
    __metaclass__ = ABCMeta
    
    def __init__(self, *args, **kwargs):
        super(nan_ndarray, self).__init__(*args, **kwargs)
        if self.dtype == numpy.dtype('float32') or self.dtype == numpy.dtype('float32'):
            self[...] = numpy.nan

    @classmethod
    def __subclasshook__(cls, C):
        return C is nan_ndarray or issubclass(C, original_ndarray)

numpy.ndarray = nan_ndarray

# Make sure our patch is transparant to those who check instance types
assert isinstance(numpy.zeros((1,)), numpy.ndarray)
import vigra
assert isinstance(vigra.VigraArray((1,)), numpy.ndarray)
