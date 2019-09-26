import numpy as np
import pandas as pd

from ilastikrag.util import generate_random_voronoi

from lazyflow.graph import Graph, Operator, InputSlot, OutputSlot
from lazyflow.operators.valueProviders import OpPrecomputedInput, OpOutputProvider
from ilastik.applets.edgeTraining import OpEdgeTraining


class OpTest(Operator):

	Input = InputSlot(value='Uninit')
	Output = OutputSlot()

	def propagateDirty(self, slot, subindex, roi):
		self.Output.setDirty(roi)

	def setupOutputs(self):
		self.Output.connect(self.Input)

class OpSwitchToggle(Operator):
	"""
	Simple toggle switch between the output and
	either of two input slots.
	"""

	pass

g = Graph()

op1 = OpTest(graph=g)
op1.Input.setValue('testA')
op2 = OpTest(graph=g)
op2.Input.setValue('testB')

op_out = OpPrecomputedInput(False, graph=g)
op_out.PrecomputedInput.connect(op1.Output)
op_out.SlowInput.connect(op2.Output)
print(op_out.outputs['Output'][:].wait())
