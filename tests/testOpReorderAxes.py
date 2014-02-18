# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Copyright 2011-2014, the ilastik developers

import sys
import unittest
import random
import vigra
import numpy
from lazyflow.graph import Graph, Operator, InputSlot, OutputSlot
from lazyflow.roi import TinyVector
from lazyflow.roi import roiToSlice

from lazyflow.operators.opReorderAxes import OpReorderAxes

# Use logging instead of print statements ...
import logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))

class OpArrayProvider(Operator):
    
    Input = InputSlot()
    Output = OutputSlot()
    
    def setupOutputs(self):
        self.Output.meta.assignFrom( self.Input.meta )
    
    def execute(self, slot, subindex, out_roi, result):
        assert not isinstance( result, vigra.VigraArray ),\
            "The 'write into' view passed to upstream operators must not be a VigraArray."
        self.Input(out_roi.start, out_roi.stop).writeInto(result).wait()
        return result

    def propagateDirty(self, inputSlot, subindex, in_roi):
        pass

class TestOpReorderAxes(unittest.TestCase):

    def setUp(self):
        self.array = None
        self.axis = list('txyzc')
        self.tests = 20
        graph = Graph()
        self.operator = OpReorderAxes(graph=graph)

    def prepareVolnOp(self, possible_axes='txyzc', num=5):
        tags = random.sample(possible_axes,random.randint(2,num))
        tagStr = ''
        for s in tags:
            tagStr += s
        axisTags = vigra.defaultAxistags(tagStr)

        self.shape = []
        for tag in axisTags:
            self.shape.append(random.randint(20,30))

        self.array = (numpy.random.rand(*tuple(self.shape))*255)
        self.array =  (float(250)/255*self.array + 5).astype(int)
        self.inArray = vigra.VigraArray(self.array,axistags = axisTags)

        opProvider = OpArrayProvider( graph=self.operator.graph )
        opProvider.Input.setValue( self.inArray )
        self.operator.Input.connect( opProvider.Output )

    def test_Full(self):
        for i in range(self.tests):
            self.prepareVolnOp()
            result = self.operator.Output().wait()
            logger.debug('------------------------------------------------------')
            logger.debug( "self.array.shape = " + str(self.array.shape) )
            logger.debug( "type(input) == " + str(type(self.operator.Input.value)) )
            logger.debug( "input.shape == " + str(self.operator.Input.meta.shape) )
            logger.debug( "Input Tags:")
            logger.debug( str( self.operator.Input.meta.axistags ) )
            logger.debug( "Output Tags:" )
            logger.debug( str(self.operator.Output.meta.axistags) )
            logger.debug( "type(result) == " + str(type(result)) )
            logger.debug( "result.shape == " + str(result.shape) )
            logger.debug( '------------------------------------------------------' )

            # Check the shape
            assert len(result.shape) == 5

            assert not isinstance(result, vigra.VigraArray), \
                "For compatibility with generic code, output should be provided as a plain numpy array."

            # Ensure the result came out in volumina order
            assert self.operator.Output.meta.axistags == vigra.defaultAxistags('txyzc')

            # Check the data
            vresult = result.view(vigra.VigraArray)
            vresult.axistags = self.operator.Output.meta.axistags
            reorderedInput = self.inArray.withAxes(*[tag.key for tag in vresult.axistags])
            assert numpy.all(vresult == reorderedInput)

    def test_Roi_default_order(self):
        for i in range(self.tests):
            self.prepareVolnOp()
            shape = self.operator.Output.meta.shape
            roi = [None,None]
            roi[1]=[numpy.random.randint(2,s) if s != 1 else 1 for s in shape]
            roi[0]=[numpy.random.randint(0,roi[1][i]) if s != 1 else 0 for i,s in enumerate(shape)]
            roi[0]=TinyVector(roi[0])
            roi[1]=TinyVector(roi[1])
            result = self.operator.Output(roi[0],roi[1]).wait()
            logger.debug('------------------------------------------------------')
            logger.debug( "self.array.shape = " + str(self.array.shape) )
            logger.debug( "type(input) == " + str(type(self.operator.Input.value)) )
            logger.debug( "input.shape == " + str(self.operator.Input.meta.shape) )
            logger.debug( "Input Tags:")
            logger.debug( str( self.operator.Input.meta.axistags ) )
            logger.debug( "Output Tags:" )
            logger.debug( str(self.operator.Output.meta.axistags) )
            logger.debug( "roi= " + str(roi) )
            logger.debug( "type(result) == " + str(type(result)) )
            logger.debug( "result.shape == " + str(result.shape) )
            logger.debug( '------------------------------------------------------' )

            # Check the shape
            assert len(result.shape) == 5
            assert not isinstance(result, vigra.VigraArray), \
                "For compatibility with generic code, output should be provided as a plain numpy array."

            # Ensure the result came out in volumina order
            assert self.operator.Output.meta.axistags == vigra.defaultAxistags('txyzc')

            # Check the data
            vresult = result.view(vigra.VigraArray)
            vresult.axistags = self.operator.Output.meta.axistags
            reorderedInput = self.inArray.withAxes(*[tag.key for tag in self.operator.Output.meta.axistags])
            assert numpy.all(vresult == reorderedInput[roiToSlice(roi[0], roi[1])])

    def test_Roi_custom_order(self):
        self._impl_roi_custom_order( 'cztxy' )
        self._impl_roi_custom_order( 'xyz' )
        
    def _impl_roi_custom_order(self, axisorder):
        for i in range(self.tests):
            self.prepareVolnOp(axisorder, len(axisorder)-1)
            
            # Specify a strange order for the output axis tags
            self.operator.AxisOrder.setValue(axisorder)
            shape = self.operator.Output.meta.shape
            
            roi = [None,None]
            roi[1]=[numpy.random.randint(2,s) if s != 1 else 1 for s in shape]
            roi[0]=[numpy.random.randint(0,roi[1][i]) if s != 1 else 0 for i,s in enumerate(shape)]
            roi[0]=TinyVector(roi[0])
            roi[1]=TinyVector(roi[1])
            result = self.operator.Output(roi[0],roi[1]).wait()
            logger.debug('------------------------------------------------------')
            logger.debug( "self.array.shape = " + str(self.array.shape) )
            logger.debug( "type(input) == " + str(type(self.operator.Input.value)) )
            logger.debug( "input.shape == " + str(self.operator.Input.meta.shape) )
            logger.debug( "Input Tags:")
            logger.debug( str( self.operator.Input.meta.axistags ) )
            logger.debug( "Output Tags:" )
            logger.debug( str(self.operator.Output.meta.axistags) )
            logger.debug( "roi= " + str(roi) )
            logger.debug( "type(result) == " + str(type(result)) )
            logger.debug( "result.shape == " + str(result.shape) )
            logger.debug( '------------------------------------------------------' )

            # Check the shape
            assert len(result.shape) == len( axisorder )

            assert not isinstance(result, vigra.VigraArray), \
                "For compatibility with generic code, output should be provided as a plain numpy array."

            # Ensure the result came out in the same strange order we asked for.
            assert self.operator.Output.meta.axistags == vigra.defaultAxistags(axisorder)

            # Check the data
            vresult = result.view(vigra.VigraArray)
            vresult.axistags = self.operator.Output.meta.axistags
            reorderedInput = self.inArray.withAxes(*[tag.key for tag in self.operator.Output.meta.axistags])
            assert numpy.all(vresult == reorderedInput[roiToSlice(roi[0], roi[1])])

    def test_insert_singleton_axis(self):
        for i in range(self.tests):
            self.prepareVolnOp('xyzc', 4)
            
            # Specify a strange order for the output axis tags
            self.operator.AxisOrder.setValue('yxtzc')
            shape = self.operator.Output.meta.shape
            
            roi = [None,None]
            roi[1]=[numpy.random.randint(2,s) if s != 1 else 1 for s in shape]
            roi[0]=[numpy.random.randint(0,roi[1][i]) if s != 1 else 0 for i,s in enumerate(shape)]
            roi[0]=TinyVector(roi[0])
            roi[1]=TinyVector(roi[1])
            result = self.operator.Output(roi[0],roi[1]).wait()
            logger.debug('------------------------------------------------------')
            logger.debug( "self.array.shape = " + str(self.array.shape) )
            logger.debug( "type(input) == " + str(type(self.operator.Input.value)) )
            logger.debug( "input.shape == " + str(self.operator.Input.meta.shape) )
            logger.debug( "Input Tags:")
            logger.debug( str( self.operator.Input.meta.axistags ) )
            logger.debug( "Output Tags:" )
            logger.debug( str(self.operator.Output.meta.axistags) )
            logger.debug( "roi= " + str(roi) )
            logger.debug( "type(result) == " + str(type(result)) )
            logger.debug( "result.shape == " + str(result.shape) )
            logger.debug( '------------------------------------------------------' )

            # Check the shape
            assert len(result.shape) == 5

            assert not isinstance(result, vigra.VigraArray), \
                "For compatibility with generic code, output should be provided as a plain numpy array."

            # Ensure the result came out in the same strange order we asked for.
            assert self.operator.Output.meta.axistags == vigra.defaultAxistags('yxtzc')

            # Check the data
            vresult = result.view(vigra.VigraArray)
            vresult.axistags = self.operator.Output.meta.axistags
            reorderedInput = self.inArray.withAxes(*[tag.key for tag in self.operator.Output.meta.axistags])
            assert numpy.all(vresult == reorderedInput[roiToSlice(roi[0], roi[1])])

    def test_attempt_drop_nonsingleton_axis(self):
        """
        Attempt to configure the operator with invalid settings by trying to drop a non-singleton axis.
        The execute method should assert in that case.
        """
        data = numpy.zeros( (100,100,100), dtype=numpy.uint8 )
        data = vigra.taggedView( data, vigra.defaultAxistags('xyz') )
        
        op = OpReorderAxes( graph=Graph() )
        op.Input.setValue( data )
        
        # Attempt to drop some axes that can't be dropped.
        op.AxisOrder.setValue( 'txc' )

        # Make sure this results in an error.        
        self.assertRaises( AssertionError, op.Output[:].wait )

if __name__ == "__main__":
    #logger.setLevel(logging.DEBUG)
    unittest.main()
