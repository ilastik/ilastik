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

import os
import tempfile
import shutil

import nose
import numpy
import vigra

from lazyflow.graph import Graph
from lazyflow.utility import PathComponents
from lazyflow.operators.operators import OpArrayCache
from lazyflow.operators.opReorderAxes import OpReorderAxes
from lazyflow.operators.ioOperators import OpInputDataReader, OpExportSlot, OpStackLoader

try:
    import dvidclient
    _skip_dvid = False
except ImportError:
    _skip_dvid = True

class TestOpExportSlot(object):
    
    @classmethod
    def setupClass(cls):
        cls._tmpdir = tempfile.mkdtemp()

    @classmethod
    def teardownClass(cls):
        shutil.rmtree(cls._tmpdir) 
    
    def testBasic_Hdf5(self):
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
        export_file = PathComponents( opExport.ExportPath.value ).externalPath
        assert os.path.split(export_file)[1] == 'test_export_x10-110_y20-120.h5'
        #print "exporting data to: {}".format( opExport.ExportPath.value )
        opExport.run_export()
        
        opRead = OpInputDataReader( graph=graph )
        opRead.FilePath.setValue( opExport.ExportPath.value )
        expected_data = data.view(numpy.ndarray)
        read_data = opRead.Output[:].wait()
        assert (read_data == expected_data).all(), "Read data didn't match exported data!"

    def testBasic_Npy(self):
        data = numpy.random.random( (100,100) ).astype( numpy.float32 )
        data = vigra.taggedView( data, vigra.defaultAxistags('xy') )
        
        graph = Graph()
        opExport = OpExportSlot(graph=graph)
        opExport.Input.setValue(data)
        opExport.OutputFormat.setValue( 'npy' )
        opExport.OutputFilenameFormat.setValue( self._tmpdir + '/test_export_x{x_start}-{x_stop}_y{y_start}-{y_stop}' )
        opExport.CoordinateOffset.setValue( (10, 20) )
        
        assert opExport.ExportPath.ready()
        assert os.path.split(opExport.ExportPath.value)[1] == 'test_export_x10-110_y20-120.npy'
        #print "exporting data to: {}".format( opExport.ExportPath.value )
        opExport.run_export()
        
        opRead = OpInputDataReader( graph=graph )
        opRead.FilePath.setValue( opExport.ExportPath.value )
        expected_data = data.view(numpy.ndarray)
        read_data = opRead.Output[:].wait()
        assert (read_data == expected_data).all(), "Read data didn't match exported data!"

    def testBasic_Dvid(self):
        if _skip_dvid:
            raise nose.SkipTest
        
        # Spin up a mock dvid server to test with.
        from mockserver.h5mockserver import H5MockServerDataFile, H5MockServer
        dvid_dataset, data_uuid, data_name = "datasetA", "abcde", "indices_data"
        mockserver_data_file = self._tmpdir + '/mockserver_data.h5'
        with H5MockServerDataFile( mockserver_data_file ) as test_h5file:
            test_h5file.add_node( dvid_dataset, data_uuid )
        server_proc, shutdown_event = H5MockServer.create_and_start( mockserver_data_file, "localhost", 8000,
                                                                     same_process=False, disable_server_logging=True )

        try:            
            data = 255 * numpy.random.random( (100,100, 4) )
            data = data.astype( numpy.uint8 )
            data = vigra.taggedView( data, vigra.defaultAxistags('xyc') )
            
            graph = Graph()
            opExport = OpExportSlot(graph=graph)
            opExport.Input.setValue( data )
            opExport.OutputFormat.setValue( 'dvid' )
            url = 'http://localhost:8000/api/node/{data_uuid}/{data_name}'.format( **locals() )
            opExport.OutputFilenameFormat.setValue( url )
            
            assert opExport.ExportPath.ready()
            assert opExport.ExportPath.value == url
            opExport.run_export()
            
            opRead = OpInputDataReader( graph=graph )
            opRead.FilePath.setValue( opExport.ExportPath.value )
            expected_data = data.view(numpy.ndarray)
            read_data = opRead.Output[:].wait()
            assert (read_data == expected_data).all(), "Read data didn't match exported data!"
        finally:
            shutdown_event.set()
            server_proc.join()

    def testBasic_2d(self):
        data = 255 * numpy.random.random( (50,100) )
        data = data.astype( numpy.uint8 )
        data = vigra.taggedView( data, vigra.defaultAxistags('xy') )
        
        graph = Graph()
        opExport = OpExportSlot(graph=graph)
        opExport.Input.setValue(data)
        opExport.OutputFormat.setValue( 'png' )
        opExport.OutputFilenameFormat.setValue( self._tmpdir + '/test_export_x{x_start}-{x_stop}_y{y_start}-{y_stop}' )
        opExport.CoordinateOffset.setValue( (10, 20) )
        
        assert opExport.ExportPath.ready()
        assert os.path.split(opExport.ExportPath.value)[1] == 'test_export_x10-60_y20-120.png'
        opExport.run_export()
        
        opRead = OpInputDataReader( graph=graph )
        opRead.FilePath.setValue( opExport.ExportPath.value )
        expected_data = data.view(numpy.ndarray)
        read_data = opRead.Output[:].wait()
        
        # Note: vigra inserts a channel axis, so read_data is xyc
        assert (read_data[...,0] == expected_data).all(), "Read data didn't match exported data!"

    def testBasic_2d_Sequence(self):
        data = 255 * numpy.random.random( (10, 50,100, 3) )
        data = data.astype( numpy.uint8 )
        data = vigra.taggedView( data, vigra.defaultAxistags('zyxc') )

        # Must run this through an operator
        # Can't use opExport.setValue() because because OpStackWriter can't work with ValueRequests
        graph = Graph()
        opData = OpArrayCache( graph=graph )
        opData.blockShape.setValue( data.shape )
        opData.Input.setValue( data )
        
        filepattern = self._tmpdir + '/test_export_x{x_start}-{x_stop}_y{y_start}-{y_stop}_z{slice_index}'
        opExport = OpExportSlot(graph=graph)
        opExport.Input.connect( opData.Output )
        opExport.OutputFormat.setValue( 'png sequence' )
        opExport.OutputFilenameFormat.setValue( filepattern )
        opExport.CoordinateOffset.setValue( (10, 20, 30, 0) )

        opExport.run_export()
        
        export_pattern = opExport.ExportPath.value
        globstring = export_pattern.format( slice_index=999 )
        globstring = globstring.replace('999', '*')

        opReader = OpStackLoader( graph=graph )
        opReader.globstring.setValue( globstring )

        # (The OpStackLoader produces txyzc order.)
        opReorderAxes = OpReorderAxes( graph=graph )
        opReorderAxes.AxisOrder.setValue( 'zyxc' )
        opReorderAxes.Input.connect( opReader.stack )
        
        assert opReorderAxes.Output.meta.shape == data.shape, "Exported files were of the wrong shape or number."
        assert (opReorderAxes.Output[:].wait() == data.view( numpy.ndarray )).all(), "Exported data was not correct"

    def testBasic_MultipageTiffSequence(self):
        data = 255 * numpy.random.random( (5, 10, 50,100, 3) )
        data = data.astype( numpy.uint8 )
        data = vigra.taggedView( data, vigra.defaultAxistags('tzyxc') )

        # Must run this through an operator
        # Can't use opExport.setValue() because because OpStackWriter can't work with ValueRequests
        graph = Graph()
        opData = OpArrayCache( graph=graph )
        opData.blockShape.setValue( data.shape )
        opData.Input.setValue( data )
        
        filepattern = self._tmpdir + '/test_export_x{x_start}-{x_stop}_y{y_start}-{y_stop}_t{slice_index}'
        opExport = OpExportSlot(graph=graph)
        opExport.Input.connect( opData.Output )
        opExport.OutputFormat.setValue( 'multipage tiff sequence' )
        opExport.OutputFilenameFormat.setValue( filepattern )
        opExport.CoordinateOffset.setValue( (7, 10, 20, 30, 0) )

        opExport.run_export()
        
        export_pattern = opExport.ExportPath.value
        globstring = export_pattern.format( slice_index=999 )
        globstring = globstring.replace('999', '*')

        opReader = OpStackLoader( graph=graph )
        opReader.globstring.setValue( globstring )

        # (The OpStackLoader produces txyzc order.)
        opReorderAxes = OpReorderAxes( graph=graph )
        opReorderAxes.AxisOrder.setValue( 'tzyxc' )
        opReorderAxes.Input.connect( opReader.stack )
        
        assert opReorderAxes.Output.meta.shape == data.shape, "Exported files were of the wrong shape or number."
        assert (opReorderAxes.Output[:].wait() == data.view( numpy.ndarray )).all(), "Exported data was not correct"

if __name__ == "__main__":
    import sys
    import nose
    import logging
    handler = logging.StreamHandler( sys.stdout )
    logging.getLogger().addHandler( handler )

    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)

