import numpy, vigra

from lazyflow import graph

from lazyflow.graph import MultiInputSlot

from lazyflow.operators.vigraOperators import *




graph = graph.Graph()


ostrich = OpImageReader(graph)
ostrich.inputs["Filename"].setValue("ostrich.jpg")


h5writer = OpH5Writer(graph)
h5writer.inputs["Filename"].setValue("ostrich.h5")
h5writer.inputs["hdf5Path"].setValue("volume/data")
h5writer.inputs["Image"].connect(ostrich.outputs["Image"])

h5reader = OpH5Reader(graph)
h5reader.inputs["Filename"].setValue("ostrich.h5")
h5reader.inputs["hdf5Path"].setValue("volume/data")

res = ostrich.outputs["Image"][:].allocate().wait()
resh5 = h5reader.outputs["Image"][:].allocate().wait()

assert (res == resh5).all()
