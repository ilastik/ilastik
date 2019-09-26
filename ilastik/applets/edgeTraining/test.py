from builtins import range

from functools import partial

import numpy as np
import pandas as pd
import vigra

import ilastikrag

#TODO Remove, debugging purposes
import pdb

from lazyflow.graph import Operator, InputSlot, OutputSlot, Graph
from lazyflow.roi import roiToSlice
from lazyflow.operators import OpValueCache, OpBlockedArrayCache
from lazyflow.classifiers import ParallelVigraRfLazyflowClassifierFactory

from ilastik.applets.base.applet import DatasetConstraintError
from ilastik.utility.operatorSubView import OperatorSubView
from ilastik.utility import OpMultiLaneWrapper

from ilastik.applets.edgeTraining.opEdgeTraining import OpSelectFeatureFromDataFrame, OpSwitchTwoWayIn

#class OpSwitchTwoWayIn(Operator):
#    """
#    This operator represents a very simple toggle switch
#    that connects an output to either of two inputs.
#
#    If Signal is False, connect to A, else use B.
#    """
#
#    InputA = InputSlot()
#    InputB = InputSlot()
#    Signal = InputSlot(value=False)
#
#    Output = OutputSlot()
#
#    def setupOutputs(self):
#        if self.InputA.ready() and self.InputB.ready():
#            self.refresh_connections()
#
#    def propagateDirty(self, slot, subindex, roi):
#        self.Output.setDirty(roi)
#
#    def execute(self, slot, subindex, roi, result):
#        assert False, "Should not get here: Output is directly connected to the input."
#
#    def refresh_connections(self):
#        if self.Signal.value:
#            self.Output.connect( self.InputB )
#        else:
#            self.Output.connect( self.InputA )


g = Graph()

## Test switch
opsw = OpSwitchTwoWayIn(graph=g)

inp = [1,2,3]
inp2 = [4,5,6]
opsw.InputA.setValue(inp)
opsw.InputB.setValue(inp2)
opsw.Signal.setValue(False)
print(opsw.Signal.value)
print(opsw.outputs['Output'][:].wait())

opsw.Signal.setValue(True)
print(opsw.Signal.value)
print(opsw.outputs['Output'][:].wait())

## Test dataframe feature extraction
optest = OpSelectFeatureFromDataFrame(graph=g)
optest.FeatureName.setValue('test')

test_dataframe = pd.DataFrame([[1,2,-1,-2],[3,4,-1,-2],[5,6,-1,-2]], columns=['sp1','sp2','test','removeme'])
print(test_dataframe)

optest.InputDataFrame.setValue(test_dataframe, check_changed=False)
print(optest.outputs['OutputDataFrame'][:].wait())







