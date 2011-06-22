import numpy, vigra

from lazyflow import graph

from lazyflow.operators.valueProviders import ArrayProvider, SingleValueProvider
from lazyflow.graph import MultiInputSlot

from lazyflow.operators.vigraOperators import *




graph = graph.Graph(numThreads=2)

fileNameProvider = SingleValueProvider("Filename", object)
fileNameProvider.setValue("ostrich.jpg")

h5fileNameProvider = SingleValueProvider("H5Filename", object)
h5fileNameProvider.setValue("ostrich.h5")

h5pathprovider = SingleValueProvider("H5Filename", object)
h5pathprovider.setValue("volume/data")




ostrich = OpImageReader(graph)
ostrich.inputs["Filename"].connect(fileNameProvider)


h5writer = OpH5Writer(graph)
h5writer.inputs["Filename"].connect(h5fileNameProvider)
h5writer.inputs["hdf5Path"].connect(h5pathprovider)
h5writer.inputs["Image"].connect(ostrich.outputs["Image"])

h5reader = OpH5Reader(graph)
h5reader.inputs["Filename"].connect(h5fileNameProvider)
h5reader.inputs["hdf5Path"].connect(h5pathprovider)

res = ostrich.outputs["Image"][:].allocate().wait()
resh5 = h5reader.outputs["Image"][:].allocate().wait()

assert (res == resh5).all()
