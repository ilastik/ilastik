import numpy, vigra
from lazyflow import graph
from opStackWriter import OpGStackWriter


volume = (255*numpy.random.rand(10,101,102)).astype(numpy.uint8)
print volume.shape, volume.dtype
outDir = "/home/opetra/Desktop/test"

g = graph.Graph()

writer = OpGStackWriter(g)
writer.inputs["input"].setValue(volume)
writer.inputs["Filepath"].setValue(outDir+'/test')
writer.inputs["Filetype"].setValue("png")

writer.outputs["WritePNGStack"][:].allocate().wait()

import glob
for i, file in enumerate(sorted(glob.glob(outDir + '/*.png'))):
    print i, file
    f = vigra.impex.readImage(file).view(numpy.ndarray).squeeze()
    print f.shape, volume[i,:,:].shape
    assert (volume[i,:,:] == f).all()