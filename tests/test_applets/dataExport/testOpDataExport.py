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
import os
import tempfile
import shutil

import numpy
import vigra

from lazyflow.graph import Graph
from lazyflow.roi import roiToSlice
from lazyflow.operators.ioOperators import OpInputDataReader

from ilastik.applets.dataExport.opDataExport import OpDataExport

class TestOpDataExport(object):
    
    @classmethod
    def setup_class(cls):
        cls._tmpdir = tempfile.mkdtemp()

    @classmethod
    def teardown_class(cls):
        shutil.rmtree(cls._tmpdir) 

    def testBasic(self):
        graph = Graph()
        opExport = OpDataExport(graph=graph)
        try:
            opExport.TransactionSlot.setValue(True)        
            opExport.WorkingDirectory.setValue( self._tmpdir )
            
            # Simulate the important fields of a DatasetInfo object
            class MockDatasetInfo(object): pass
            rawInfo = MockDatasetInfo()
            rawInfo.nickname = 'test_nickname'
            rawInfo.filePath = './somefile.h5'
            opExport.RawDatasetInfo.setValue( rawInfo )
    
            opExport.SelectionNames.setValue(['Mock Export Data'])
    
            data = numpy.random.random( (100,100) ).astype( numpy.float32 ) * 100
            data = vigra.taggedView( data, vigra.defaultAxistags('xy') )
            
            opExport.Inputs.resize(1)
            opExport.Inputs[0].setValue(data)
    
            sub_roi = [(10, 20), (90, 80)]
            opExport.RegionStart.setValue( sub_roi[0] )
            opExport.RegionStop.setValue( sub_roi[1] )
            
            opExport.ExportDtype.setValue( numpy.uint8 )
            
            opExport.OutputFormat.setValue( 'hdf5' )
            opExport.OutputFilenameFormat.setValue( '{dataset_dir}/{nickname}_export_x{x_start}-{x_stop}_y{y_start}-{y_stop}' )
            opExport.OutputInternalPath.setValue('volume/data')
    
            assert opExport.ImageToExport.ready()
            assert opExport.ExportPath.ready()
            
            expected_path = self._tmpdir + '/' + rawInfo.nickname + '_export_x10-90_y20-80.h5/volume/data'
            computed_path = opExport.ExportPath.value
            assert os.path.normpath(computed_path) == os.path.normpath(expected_path), \
                "Expected {}\nGot: {}".format( expected_path, computed_path )
            opExport.run_export()
        finally:
            opExport.cleanUp()
        
        opRead = OpInputDataReader( graph=graph )
        try:
            opRead.FilePath.setValue( computed_path )
    
            # Compare with the correct subregion and convert dtype.
            expected_data = data.view(numpy.ndarray)[roiToSlice(*sub_roi)]
            expected_data = expected_data.astype(numpy.uint8)
            read_data = opRead.Output[:].wait()
            assert (read_data == expected_data).all(), "Read data didn't match exported data!"
        finally:
            opRead.cleanUp()
