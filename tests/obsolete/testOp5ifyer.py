import sys
import unittest
import random
import vigra
import numpy
from lazyflow.graph import Graph
from volumina.adaptors import Op5ifyer
from lazyflow.roi import TinyVector
from lazyflow.roi import roiToSlice

# Use logging instead of print statements ...
import logging
logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler(sys.stdout))

class TestOp5ifyer(unittest.TestCase):

    def setUp(self):
        self.array = None
        self.axis = list('txyzc')
        self.tests = 20
        graph = Graph()
        self.operator = Op5ifyer(graph)

    def prepareVolnOp(self):
        tags = random.sample(self.axis,random.randint(2,len(self.axis)))
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
        self.operator.inputs["input"].setValue(self.inArray)

    def test_Full(self):
        for i in range(self.tests):
            self.prepareVolnOp()
            result = self.operator.outputs["output"]().wait()
            logger.debug('------------------------------------------------------')
            logger.debug( "self.array.shape = " + str(self.array.shape) )
            logger.debug( "type(input) == " + str(type(self.operator.input.value)) )
            logger.debug( "input.shape == " + str(self.operator.input.meta.shape) )
            logger.debug( "Input Tags:")
            logger.debug( str( self.operator.inputs['input'].axistags ) )
            logger.debug( "Output Tags:" )
            logger.debug( str(self.operator.output.axistags) )
            logger.debug( "type(result) == " + str(type(result)) )
            logger.debug( "result.shape == " + str(result.shape) )
            logger.debug( '------------------------------------------------------' )

            # Check the shape
            assert len(result.shape) == 5

            # Ensure the result came out in volumina order
            assert self.operator.outputs["output"].meta.axistags == vigra.defaultAxistags('txyzc')

            # Check the data
            vresult = result.view(vigra.VigraArray)
            vresult.axistags = self.operator.output.meta.axistags
            reorderedInput = self.inArray.withAxes(*[tag.key for tag in vresult.axistags])
            assert numpy.all(vresult == reorderedInput)

    def test_Roi_default_order(self):
        for i in range(self.tests):
            self.prepareVolnOp()
            shape = self.operator.outputs["output"].shape
            roi = [None,None]
            roi[1]=[numpy.random.randint(2,s) if s != 1 else 1 for s in shape]
            roi[0]=[numpy.random.randint(0,roi[1][i]) if s != 1 else 0 for i,s in enumerate(shape)]
            roi[0]=TinyVector(roi[0])
            roi[1]=TinyVector(roi[1])
            result = self.operator.outputs["output"](roi[0],roi[1]).wait()
            logger.debug('------------------------------------------------------')
            logger.debug( "self.array.shape = " + str(self.array.shape) )
            logger.debug( "type(input) == " + str(type(self.operator.input.value)) )
            logger.debug( "input.shape == " + str(self.operator.input.meta.shape) )
            logger.debug( "Input Tags:")
            logger.debug( str( self.operator.inputs['input'].axistags ) )
            logger.debug( "Output Tags:" )
            logger.debug( str(self.operator.output.axistags) )
            logger.debug( "roi= " + str(roi) )
            logger.debug( "type(result) == " + str(type(result)) )
            logger.debug( "result.shape == " + str(result.shape) )
            logger.debug( '------------------------------------------------------' )

            # Check the shape
            assert len(result.shape) == 5

            # Ensure the result came out in volumina order
            assert self.operator.outputs["output"].meta.axistags == vigra.defaultAxistags('txyzc')

            # Check the data
            vresult = result.view(vigra.VigraArray)
            vresult.axistags = self.operator.outputs["output"].meta.axistags
            reorderedInput = self.inArray.withAxes(*[tag.key for tag in self.operator.outputs["output"].meta.axistags])
            assert numpy.all(vresult == reorderedInput[roiToSlice(roi[0], roi[1])])

    def test_Roi_custom_order(self):
        for i in range(self.tests):
            self.prepareVolnOp()
            
            # Specify a strange order for the output axis tags
            self.operator.order.setValue('ctyzx')
            shape = self.operator.outputs["output"].shape
            
            roi = [None,None]
            roi[1]=[numpy.random.randint(2,s) if s != 1 else 1 for s in shape]
            roi[0]=[numpy.random.randint(0,roi[1][i]) if s != 1 else 0 for i,s in enumerate(shape)]
            roi[0]=TinyVector(roi[0])
            roi[1]=TinyVector(roi[1])
            result = self.operator.outputs["output"](roi[0],roi[1]).wait()
            logger.debug('------------------------------------------------------')
            logger.debug( "self.array.shape = " + str(self.array.shape) )
            logger.debug( "type(input) == " + str(type(self.operator.input.value)) )
            logger.debug( "input.shape == " + str(self.operator.input.meta.shape) )
            logger.debug( "Input Tags:")
            logger.debug( str( self.operator.inputs['input'].axistags ) )
            logger.debug( "Output Tags:" )
            logger.debug( str(self.operator.output.axistags) )
            logger.debug( "roi= " + str(roi) )
            logger.debug( "type(result) == " + str(type(result)) )
            logger.debug( "result.shape == " + str(result.shape) )
            logger.debug( '------------------------------------------------------' )

            # Check the shape
            assert len(result.shape) == 5

            # Ensure the result came out in the same strange order we asked for.
            assert self.operator.outputs["output"].meta.axistags == vigra.defaultAxistags('ctyzx')

            # Check the data
            vresult = result.view(vigra.VigraArray)
            vresult.axistags = self.operator.outputs["output"].meta.axistags
            reorderedInput = self.inArray.withAxes(*[tag.key for tag in self.operator.outputs["output"].meta.axistags])
            assert numpy.all(vresult == reorderedInput[roiToSlice(roi[0], roi[1])])

if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    unittest.main()
