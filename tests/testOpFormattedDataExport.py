import os
import tempfile
import shutil

import numpy
import vigra

from lazyflow.graph import Graph
from lazyflow.roi import roiToSlice
from lazyflow.operators.ioOperators import OpInputDataReader, OpFormattedDataExport

class TestOpFormattedDataExport(object):
    
    @classmethod
    def setupClass(cls):
        cls._tmpdir = tempfile.mkdtemp()

    @classmethod
    def teardownClass(cls):
        shutil.rmtree(cls._tmpdir) 

    def testBasic(self):
        graph = Graph()
        opExport = OpFormattedDataExport(graph=graph)
        
        data = numpy.random.random( (100,100) ).astype( numpy.float32 ) * 100
        data = vigra.taggedView( data, vigra.defaultAxistags('xy') )
        opExport.Input.setValue(data)

        sub_roi = [(10, 0), (None, 80)]
        opExport.RegionStart.setValue( sub_roi[0] )
        opExport.RegionStop.setValue( sub_roi[1] )
        
        opExport.ExportDtype.setValue( numpy.uint8 )

        opExport.InputMin.setValue( 0.0 )
        opExport.InputMax.setValue( 100.0 )
        opExport.ExportMin.setValue( 100 )
        opExport.ExportMax.setValue( 200 )
        
        opExport.OutputFormat.setValue( 'hdf5' )
        opExport.OutputFilenameFormat.setValue( self._tmpdir + '/export_x{x_start}-{x_stop}_y{y_start}-{y_stop}' )
        opExport.OutputInternalPath.setValue('volume/data')
        
        opExport.TransactionSlot.setValue( True )

        assert opExport.ImageToExport.ready()
        assert opExport.ExportPath.ready()
        assert opExport.ImageToExport.meta.drange == (100,200)
        
        #print "exporting data to: {}".format( opExport.ExportPath.value )
        assert opExport.ExportPath.value == self._tmpdir + '/' + 'export_x10-100_y0-80.h5/volume/data'
        opExport.run_export()
        
        opRead = OpInputDataReader( graph=graph )
        opRead.FilePath.setValue( opExport.ExportPath.value )

        # Compare with the correct subregion and convert dtype.
        sub_roi[1] = (100, 80) # Replace 'None' with full extent
        expected_data = data.view(numpy.ndarray)[roiToSlice(*sub_roi)]
        expected_data = expected_data.astype(numpy.uint8)
        expected_data += 100 # see renormalization settings
        read_data = opRead.Output[:].wait()
        assert numpy.allclose(read_data, expected_data), "Read data didn't match exported data!"

if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)


