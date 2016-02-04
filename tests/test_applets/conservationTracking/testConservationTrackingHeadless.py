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
#           http://ilastik.org/license.html
###############################################################################
import os
import sys
import imp
import numpy
import h5py
import tempfile
import csv
import nose

from lazyflow.graph import Graph
from lazyflow.operators.ioOperators import OpStackLoader
from lazyflow.operators.opReorderAxes import OpReorderAxes

import ilastik
from lazyflow.utility.timer import timeLogged

from ilastik.config import cfg as ilastik_config

import logging
logger = logging.getLogger(__name__)

class TestConservationTrackingHeadless(object):
    # NOTE: In order for this tests to work, you need to include the following files in the same directory:
    # * miceConservationTracking.ilp
    # * mice.h5
    # * mice_prediction.h5
    # These files can be downloaded from the following GitHub repository: https://github.com/ilastik/ilastik_testdata
    
    EXPECTED_SHAPE = (5,840,840,1,1) # Expected shape for HDF5 files
    EXPECTED_NUM_LINES = 21 # Number of lines expected in csv file
    
    PROJECT_FILE = 'miceConservationTracking.ilp'
    RAW_DATA_FILE = 'mice.h5'
    PREDICTION_MAPS_FILE = 'mice_prediction.h5'

    @classmethod
    def setupClass(cls):
        logger.info('starting setup...')
        cls.original_cwd = os.getcwd()

        # Load the ilastik startup script as a module.
        # Do it here in setupClass to ensure that it isn't loaded more than once.
        logger.info('looking for ilastik.py...')
        ilastik_entry_file_path = os.path.join( os.path.split( os.path.realpath(ilastik.__file__) )[0], "../ilastik.py" )
        if not os.path.exists( ilastik_entry_file_path ):
            raise RuntimeError("Couldn't find ilastik.py startup script: {}".format( ilastik_entry_file_path ))
            
        cls.ilastik_startup = imp.load_source( 'ilastik_startup', ilastik_entry_file_path )


    @classmethod
    def teardownClass(cls):
        removeFiles = ['mice-exported_data_table.csv', 'mice_Tracking-Result.h5', 'mice_Object-Identities.h5']
        
        # Clean up: Delete any test files we generated
        for f in removeFiles:
            try:
                os.remove(f)
            except:
                pass


    @timeLogged(logger)
    def testTrackingResultHeadless(self):
        # Skip test because there are missing files
        if not os.path.isfile(self.PROJECT_FILE) or not os.path.isfile(self.RAW_DATA_FILE) or not os.path.isfile(self.PREDICTION_MAPS_FILE):
            raise nose.SkipTest   
        
        args = ' --project=miceConservationTracking.ilp'
        args += ' --headless'
        
        args += ' --export_source=Tracking-Result'
        args += ' --raw_data ./mice.h5/exported_data'
        args += ' --prediction_maps ./mice_prediction.h5/exported_data'

        sys.argv = ['ilastik.py'] # Clear the existing commandline args so it looks like we're starting fresh.
        sys.argv += args.split()

        # Start up the ilastik.py entry script as if we had launched it from the command line
        self.ilastik_startup.main()
        
        # Examine the HDF5 output for basic attributes
        with h5py.File('mice_Tracking-Result.h5', 'r') as f:
            assert 'exported_data' in f, 'Dataset does not exist in mice_Tracking-Result.h5 file'
            shape = f["exported_data"].shape
            assert shape == self.EXPECTED_SHAPE, "Exported data has wrong shape: {}".format(shape)
        
        # Examine the csv output for basic attributes    
        with  open('mice-exported_data_table.csv', 'r') as csvfile:
            reader = csv.reader(csvfile)
            numlines =  sum(1 for lines in reader)
            assert numlines == self.EXPECTED_NUM_LINES


    @timeLogged(logger)
    def testObjectIdentitiesHeadless(self):
        # Skip test because there are missing files
        if not os.path.isfile(self.PROJECT_FILE) or not os.path.isfile(self.RAW_DATA_FILE) or not os.path.isfile(self.PREDICTION_MAPS_FILE):
            raise nose.SkipTest   
        
        args = ' --project=miceConservationTracking.ilp'
        args += ' --headless'
        
        args += ' --export_source=Object-Identities'
        args += ' --raw_data ./mice.h5/exported_data'
        args += ' --prediction_maps ./mice_prediction.h5/exported_data'

        sys.argv = ['ilastik.py'] # Clear the existing commandline args so it looks like we're starting fresh.
        sys.argv += args.split()

        # Start up the ilastik.py entry script as if we had launched it from the command line
        self.ilastik_startup.main()
        
        # Examine the HDF5 output for basic attributes
        with h5py.File('mice_Object-Identities.h5', 'r') as f:
            assert 'exported_data' in f, 'Dataset does not exist in mice_Tracking-Result.h5 file'
            shape = f["exported_data"].shape
            assert shape == self.EXPECTED_SHAPE, "Exported data has wrong shape: {}".format(shape)
        
        # Examine the csv output for basic attributes     
        with  open('mice-exported_data_table.csv', 'r') as csvfile:
            reader = csv.reader(csvfile)
            numlines =  sum(1 for lines in reader)
            assert numlines == self.EXPECTED_NUM_LINES


if __name__ == "__main__":
    #make the program quit on Ctrl+C
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
