from lazyflow.operators.ioOperators import OpStackWriter
from lazyflow.operators.ioOperators import OpStackToH5Writer
import numpy
import vigra
import h5py
import os
import sys
import glob
import lazyflow.graph

#import logging
#logger = logging.getLogger(__file__)
#logger.addHandler(logging.StreamHandler(sys.stdout))
#logger.setLevel(logging.DEBUG)

class TestOpStackWriter(object):

    def setUp(self):
        self.graph = lazyflow.graph.Graph()
        self.testFilePath = ''
        self.testDataFileName = "stackWriter"
        self.testFileType = "png"
        self.testH5Group = "comparison.h5"
        self.testH5Path = "/volume/data"

        # Generate some test data
        self.dataShape = (1, 10, 64, 128, 1)
        self.testData = vigra.VigraArray( self.dataShape,
                                         axistags=vigra.defaultAxistags('txyzc'),
                                         order='C' ).astype(numpy.uint8)
        self.testData[...] = numpy.indices(self.dataShape).sum(0)

    def tearDown(self):
        # Clean up: Delete the test file.
        try:
            os.remove(self.testDataFileName)
            os.remove(self.testH5Group)
        except:
            pass

    def test_Writer(self):
        # Create the h5 file
        
        opWriter = OpStackWriter(graph=self.graph)
        opWriter.Filename.setValue(self.testDataFileName)
        opWriter.Image.setValue( self.testData )

        # Force the operator to execute by asking for the output (a bool)
        success = opWriter.WriteImage.value
        assert success

        f = h5py.File(self.testH5Group, 'a')
        opStackToH5Writer = OpStackToH5Writer(graph = self.graph)
        opStackToH5Writer.GlobString.setValue(self.testDataFileName + "*" +
                                              self.testFileType)
        opStackToH5Writer.hdf5Group.setValue(f)
        opStackToH5Writer.hdf5Path.setValue(self.testH5Path)
        opStackToH5Writer.WriteImage[:].wait()
        f.close()
        try:
            files = glob.glob(self.testDataFileName + "*" + self.testFileType)
            for file in files:
                os.remove(file)
        except IOError as e:
            print e 
            pass

        
        f = h5py.File(self.testH5Group, 'r')
        # Check the file.
        dataset = f[self.testH5Path]
        compdata = dataset.value.reshape(self.dataShape)
        assert compdata.shape == self.dataShape
        assert numpy.all( compdata[...] == self.testData.view(numpy.ndarray)[...] )
        f.close()

    def test_Writer2(self):
        # Create the h5 file
        
        opWriter = OpStackWriter(graph=self.graph)
        opWriter.Filename.setValue(self.testDataFileName)
        opWriter.Image.setValue( self.testData )
        opWriter.ImageAxesNames.setValue("yx")

        # Force the operator to execute by asking for the output (a bool)
        success = opWriter.WriteImage.value
        assert success

        f = h5py.File(self.testH5Group, 'a')
        opStackToH5Writer = OpStackToH5Writer(graph = self.graph)
        opStackToH5Writer.GlobString.setValue(self.testDataFileName + "*" +
                                              self.testFileType)
        opStackToH5Writer.hdf5Group.setValue(f)
        opStackToH5Writer.hdf5Path.setValue(self.testH5Path)
        opStackToH5Writer.WriteImage[:].wait()
        f.close()
        try:
            files = glob.glob(self.testDataFileName + "*" + self.testFileType)
            for file in files:
                os.remove(file)
        except IOError as e:
            print e 
            pass

        
        f = h5py.File(self.testH5Group, 'r')
        # Check the file.
        dataset = f[self.testH5Path]
        compdata = dataset.value.transpose(1,0,2,3).reshape(self.dataShape)
        assert compdata.shape == self.dataShape
        assert numpy.all( compdata[...] == self.testData.view(numpy.ndarray)[...] )
        f.close()
if __name__ == "__main__":
    import nose
    ret = nose.run(defaultTest=__file__, env={'NOSE_NOCAPTURE' : 1})
