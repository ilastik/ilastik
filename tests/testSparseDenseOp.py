import numpy, vigra
from lazyflow.graph import *

from lazyflow import operators

g = Graph()

opSparse = operators.OpDenseSparseArray(g)

opSparse.inputs["shape"].setValue((30,40,50))
opSparse.inputs["eraser"].setValue(1)


assert len(numpy.nonzero(opSparse.outputs["Output"][:].allocate().wait())[0]) == 0

opSparse.inputs["Input"][0,10:20,3] = 17

assert len(opSparse.outputs["nonzeroValues"][:].allocate().wait()[0]) == 10
assert (opSparse.outputs["nonzeroValues"][:].allocate().wait()[0] == 17).all()
assert len(opSparse.outputs["nonzeroCoordinates"][:].allocate().wait()[0]) == 10

opSparse.inputs["Input"][0:1,10:20,3:4] = 1

assert len(opSparse.outputs["nonzeroValues"][:].allocate().wait()[0]) == 0
assert (opSparse.outputs["Output"][:].allocate().wait() == 0).all()
assert len(opSparse.outputs["nonzeroCoordinates"][:].allocate().wait()[0]) == 0


g.finalize()