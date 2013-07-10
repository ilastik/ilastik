import os
import tempfile
import shutil

import numpy
import vigra

from lazyflow.graph import Graph
from lazyflow.operators.ioOperators import OpInputDataReader

from ilastik.applets.dataExport.opDataExport import OpExportSlot

class TestOpExportSlot(object):
    
    @classmethod
    def setupClass(cls):
        cls._tmpdir = tempfile.mkdtemp()

    @classmethod
    def teardownClass(cls):
        shutil.rmtree(cls._tmpdir) 
    
    def testBasic(self):
        data = numpy.random.random( (100,100) ).astype( numpy.float32 )
        data = vigra.taggedView( data, vigra.defaultAxistags('xy') )
        
        graph = Graph()
        opExport = OpExportSlot(graph=graph)
        opExport.Input.setValue(data)
        opExport.OutputFormat.setValue( 'hdf5' )
        opExport.OutputFilenameFormat.setValue( self._tmpdir + '/test_export_x{x_start}-{x_stop}_y{y_start}-{y_stop}' )
        opExport.OutputInternalPath.setValue('volume/data')
        opExport.CoordinateOffset.setValue( (10, 20) )
        
        assert opExport.ExportPath.ready()
        assert os.path.split(opExport.ExportPath.value)[1] == 'test_export_x10-110_y20-120.h5'
        #print "exporting data to: {}".format( opExport.ExportPath.value )
        opExport.run_export()
        
        opRead = OpInputDataReader( graph=graph )
        opRead.FilePath.setValue( opExport.ExportPath.value + '/volume/data' )
        expected_data = data.view(numpy.ndarray)
        read_data = opRead.Output[:].wait()
        assert (read_data == expected_data).all(), "Read data didn't match exported data!"



if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
        