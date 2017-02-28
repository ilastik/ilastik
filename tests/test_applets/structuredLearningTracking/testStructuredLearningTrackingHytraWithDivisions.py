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
import numpy as np
import h5py
import tempfile
import csv
import nose

from lazyflow.graph import Graph
from lazyflow.operators.ioOperators import OpStackLoader
from lazyflow.operators.opReorderAxes import OpReorderAxes

import ilastik
from lazyflow.utility.timer import timeLogged

import logging
logger = logging.getLogger(__name__)

class TestStructuredLearningTrackingHeadless(object):    

    PROJECT_FILE = 'data/inputdata/mitocheckStructuredLearningTrackingHytraWithDivisions.ilp'
    RAW_DATA_FILE = 'data/inputdata/mitocheck_2d+t/mitocheck_small_2D+t.h5'
    PREDICTION_FILE = 'data/inputdata/mitocheck_2d+t/mitocheck_small_2D+t_export.h5'

    EXPECTED_TRACKING_RESULT_FILE = 'data/inputdata/mitocheck_2d+t/mitocheck_small_2D+t_Tracking-Result.h5'
    EXPECTED_DIVISIONS_CSV_FILE = 'data/inputdata/mitocheck_2d+t/mitocheck_small_2D+t-tracking_exported_data_divisions.csv'
    EXPECTED_CSV_FILE = 'data/inputdata/mitocheck_2d+t/mitocheck_small_2D+t-tracking_exported_data_table.csv'
    EXPECTED_SHAPE = (9, 99, 105, 1, 1) # Expected shape for tracking results HDF5 files
    EXPECTED_NUM_LINES_TRACKING = 25 # Number of lines expected in exported csv file
    EXPECTED_NUM_LINES_DIVISIONS = 2 # Number of lines expected in exported csv file
    EXPECTED_MERGER_NUM = 0 # Number of mergers expected in exported csv file
    EXPECTED_FALSE_DETECTIONS_NUM = 1 # Number of false detections expected in exported csv file

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
        removeFiles = ['data/inputdata/mitocheck_2d+t/mitocheck_small_2D+t_Tracking-Result.h5',
                       'data/inputdata/mitocheck_2d+t/mitocheck_small_2D+t-tracking_exported_data_table.csv',
                       'data/inputdata/mitocheck_2d+t/mitocheck_small_2D+t-tracking_exported_data_divisions.csv']

        # Clean up: Delete any test files we generated
        for f in removeFiles:
            try:
                os.remove(f)
            except:
                pass
        pass


    @timeLogged(logger)
    def testStructuredLearningTrackingHeadless(self):
        # Skip test if structured learning tracking can't be imported. If it fails the problem is most likely that CPLEX is not installed.
        try:
            import ilastik.workflows.tracking.structured
        except ImportError as e:
            logger.warn( "Structured learning tracking could not be imported. CPLEX is most likely missing: " + str(e) )
            raise nose.SkipTest 
        
        # Skip test because there are missing files
        if not os.path.isfile(self.PROJECT_FILE) or not os.path.isfile(self.RAW_DATA_FILE) or not os.path.isfile(self.PREDICTION_FILE):
            logger.info("Test files not found.")   
        
        args = ' --project='+self.PROJECT_FILE
        args += ' --headless'
        args += ' --testFullAnnotations'
        args += ' --export_source=Tracking-Result'
        args += ' --raw_data '+self.RAW_DATA_FILE
        args += ' --prediction_maps '+self.PREDICTION_FILE

        sys.argv = ['ilastik.py'] # Clear the existing commandline args so it looks like we're starting fresh.
        sys.argv += args.split()

        # Start up the ilastik.py entry script as if we had launched it from the command line
        self.ilastik_startup.main()

        print self

        # Examine the HDF5 output for basic attributes
        with h5py.File(self.EXPECTED_TRACKING_RESULT_FILE, 'r') as f:
            assert 'exported_data' in f, 'Dataset does not exist in the tracking result file'
            shape = f['exported_data'].shape
            assert shape == self.EXPECTED_SHAPE, 'Exported data has a wrong shape: {}'.format(shape)

        # Load csv file
        data = np.genfromtxt(self.EXPECTED_CSV_FILE, dtype=float, delimiter=',', names=True)

        # Check for expected number of lines
        logger.info("Number of rows in the csv file: {}".format(data.shape[0]))
        print "Number of rows in the csv file: {}".format(data.shape[0])
        assert data.shape[0] == self.EXPECTED_NUM_LINES_TRACKING, 'Number of rows in the csv file differs from expected'

        # Check that the csv file contains the default fields.
        assert 'object_id' in data.dtype.names, "'object_id' not found in the csv file!"
        assert 'timestep' in data.dtype.names, "'timestep' not found in the csv file!"
        assert 'labelimage_oid' in data.dtype.names, "'labelimage_oid' not found in the csv file!"
        assert 'lineage_id' in data.dtype.names, "'lineage_id' not found in the csv file!"
        assert 'track_id' in data.dtype.names, "'track_id' not found in the csv file!"
        assert 'Size_in_pixels' in data.dtype.names, "'Size_in_pixels' not found in the csv file!"
        assert 'Bounding_Box_Minimum_0' in data.dtype.names, "'Bounding_Box_Minimum_0' not found in the csv file!"
        assert 'Bounding_Box_Minimum_1' in data.dtype.names, "'Bounding_Box_Minimum_1' not found in the csv file!"
        assert 'Center_of_the_object_0' in data.dtype.names, "'Center_of_the_object_0' not found in the csv file!"
        assert 'Center_of_the_object_1' in data.dtype.names, "'Center_of_the_object_1' not found in the csv file!"
        assert 'Bounding_Box_Maximum_0' in data.dtype.names, "'Bounding_Box_Maximum_0' not found in the csv file!"
        assert 'Bounding_Box_Maximum_1' in data.dtype.names, "'Bounding_Box_Maximum_1' not found in the csv file!"

        # Check for expected number of mergers
        merger_count = 0
        for id in data['lineage_id']:
            if id == 0:
                merger_count += 1
        logger.info("Number of mergers in the csv file: {}".format(merger_count))
        assert merger_count == self.EXPECTED_MERGER_NUM, 'Number of mergers {} in the csv file differs from expected {}.'.format(merger_count, self.EXPECTED_MERGER_NUM)

        # Check for expected number of false detections
        false_detection_count = 0
        for id in data['lineage_id']:
            if id == 1:
                false_detection_count += 1
        logger.info("Number of false detections in the csv file: {}".format(false_detection_count))
        assert false_detection_count == self.EXPECTED_FALSE_DETECTIONS_NUM, 'Number of false detections {} in the csv file differs from expected {}.'.format(false_detection_count,self.EXPECTED_FALSE_DETECTIONS_NUM)


        # Load divisions csv file
        data = np.genfromtxt(self.EXPECTED_DIVISIONS_CSV_FILE, dtype=float, delimiter=',', names=True)

        # Check for expected number of lines
        logger.info("Number of rows in the divisions csv file: {}".format(data.shape[0]))
        print "Number of rows in the divisions csv file: {}".format(data.shape[0])
        assert data.shape[0] == self.EXPECTED_NUM_LINES_DIVISIONS, 'Number of rows {} in the divisions csv file differs from expected {}.'.format(data.shape[0],self.EXPECTED_NUM_LINES_DIVISIONS)

        # Check that the csv file contains the default fields.
        assert 'object_id' in data.dtype.names, "'object_id' not found in the csv file!"
        assert 'timestep' in data.dtype.names, "'timestep' not found in the csv file!"
        assert 'lineage_id' in data.dtype.names, "'lineage_id' not found in the csv file!"
        assert 'track_id' in data.dtype.names, "'track_id' not found in the csv file!"
        assert 'child1_object_id' in data.dtype.names, "'child1_object_id' not found in the csv file!"
        assert 'child1_track_id' in data.dtype.names, "'child1_track_id' not found in the csv file!"
        assert 'child2_object_id' in data.dtype.names, "'child2_object_id' not found in the csv file!"
        assert 'child2_track_id' in data.dtype.names, "'child2_track_id' not found in the csv file!"

if __name__ == "__main__":
    # Make the program quit on Ctrl+C
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
