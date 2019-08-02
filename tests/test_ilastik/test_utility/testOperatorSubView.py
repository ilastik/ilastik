###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
#		   http://ilastik.org/license.html
###############################################################################
from builtins import range
import random
from lazyflow.graph import Graph, Operator, OperatorWrapper, InputSlot, OutputSlot
from ilastik.utility import OpMultiLaneWrapper

from ilastik.utility import OperatorSubView

class OpSum(Operator):
    InputA = InputSlot()
    InputB = InputSlot()

    Output = OutputSlot()
    
    def __init__(self, *args, **kwargs):
        super(OpSum, self).__init__(*args, **kwargs)
        self.rand = random.random()

    def setupOutputs(self):
        assert self.InputA.meta.shape == self.InputB.meta.shape, "Can't add images of different shapes!"
        self.Output.meta.assignFrom(self.InputA.meta)

    def execute(self, slot, subindex, roi, result):
        a = self.InputA.get(roi).wait()
        b = self.InputB.get(roi).wait()
        result[...] = a+b
        return result

    def propagateDirty(self, dirtySlot, subindex, roi):
        self.Output.setDirty(roi)

class OpMultiThreshold(Operator):
    ThresholdLevel = InputSlot()
    Inputs = InputSlot(level=1)
    Outputs = OutputSlot(level=1)

    def __init__(self, *args, **kwargs):
        super(OpMultiThreshold, self).__init__(*args, **kwargs)
        self.hello = "Heya"

    def setupOutputs(self):
        self.Outputs.resize( len(self.Inputs) )
        for i in range( len(self.Inputs) ):
            self.Outputs[i].meta.assignFrom(self.Inputs[i].meta)
            self.Outputs[i].meta.dtype = numpy.uint8

    def execute(self, slot, subindex, roi, result):
        assert len(subindex) == 1
        index = subindex[0]
        thresholdLevel = self.ThresholdLevel.value
        inputData = self.Inputs[index].get(roi).wait()
        result[...] = inputData > thresholdLevel
        return result

    def propagateDirty(self, dirtySlot, subindex, roi):
        self.Outputs[subindex].setDirty(roi)

class OpNestedMultiOps(Operator):
    InputA = InputSlot(level=1)
    InputB = InputSlot(level=1)

    Output = OutputSlot(level=1)

    def __init__(self, *args, **kwargs):
        super(OpNestedMultiOps, self).__init__(*args, **kwargs)
        self.opSum1 = OpMultiLaneWrapper( OpSum, parent=self )
        self.opSum2 = OpMultiLaneWrapper( OpSum, parent=self )
        self.opSum3 = OpMultiLaneWrapper( OpSum, parent=self )

        self.opSum1.InputA.connect( self.InputA )
        self.opSum1.InputB.connect( self.InputB )

        self.opSum2.InputA.connect( self.InputA )
        self.opSum2.InputB.connect( self.InputB )

        self.opSum3.InputA.connect( self.opSum1.Output )
        self.opSum3.InputB.connect( self.opSum2.Output )

        self.Output.connect( self.opSum3.Output )

class TestOperatorSubView(object):
    
    def testBasic(self):
        graph = Graph()
        opWrappedSum = OperatorWrapper( OpSum, graph=graph )
        opWrappedSum.InputA.resize(3)
            
        subView0 = OperatorSubView(opWrappedSum, 0)
        assert subView0.InputA == opWrappedSum.InputA[0]
        assert subView0.InputB == opWrappedSum.InputB[0]
        assert subView0.Output == opWrappedSum.Output[0]
        assert subView0.rand == opWrappedSum.innerOperators[0].rand
        
        subView1 = OperatorSubView(opWrappedSum, 1)
        assert subView1.InputA == opWrappedSum.InputA[1]
        assert subView1.InputB == opWrappedSum.InputB[1]
        assert subView1.Output == opWrappedSum.Output[1]
        assert subView1.rand == opWrappedSum.innerOperators[1].rand
    
        # When a slot is removed, the view should follow the same slots as they slide down the list.
        opWrappedSum.InputA.removeSlot(0, 2)
        assert subView1.InputA == opWrappedSum.InputA[0]
        assert subView1.InputB == opWrappedSum.InputB[0]
        assert subView1.Output == opWrappedSum.Output[0]
        assert subView1.rand == opWrappedSum.innerOperators[0].rand
    
    def testOther(self):
        graph = Graph()
        opMultiThreshold = OpMultiThreshold(graph=graph)
        opMultiThreshold.Inputs.resize(3)
        opMultiThreshold.Outputs.resize(3)
        
        subThresholdView = OperatorSubView( opMultiThreshold, 1 )
        
        assert subThresholdView.Inputs == opMultiThreshold.Inputs[1]
        assert subThresholdView.Outputs == opMultiThreshold.Outputs[1]
        assert subThresholdView.hello == opMultiThreshold.hello
        
    def testNested(self):
        graph = Graph()
        opNested = OpNestedMultiOps( graph=graph )
        opNested.InputA.resize( 3 )
        assert len( opNested.InputB ) == 3
        
        opNestedView = OperatorSubView( opNested, 1 )
        
        assert opNestedView.opSum1.rand == opNested.opSum1.innerOperators[1].rand
        assert opNestedView.opSum2.rand == opNested.opSum2.innerOperators[1].rand
    
        # View should follow the slots as they change index
        opNested.InputA.removeSlot(0, 2)
        assert opNestedView.opSum1.rand == opNested.opSum1.innerOperators[0].rand
        assert opNestedView.opSum2.rand == opNested.opSum2.innerOperators[0].rand
    
        assert isinstance(opNestedView.opSum1, OperatorSubView)
        assert opNestedView.opSum1.InputA.level == 0
    
    def testConvenienceFunctions(self):
        """
        Verify that OperatorSubView.viewed_operator() and OperatorSubView.current_view_index() work correctly.
        """
        graph = Graph()
        opWrappedSum = OperatorWrapper( OpSum, graph=graph )
        opWrappedSum.InputA.resize(3)
            
        subView1 = OperatorSubView(opWrappedSum, 1)
        assert subView1.viewed_operator() == opWrappedSum
        assert subView1.current_view_index() == 1

        opWrappedSum.InputA.removeSlot(0, finalsize=2)
        assert subView1.viewed_operator() == opWrappedSum
        assert subView1.current_view_index() == 0
