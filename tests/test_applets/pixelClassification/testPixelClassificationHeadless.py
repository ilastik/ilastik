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
from __future__ import print_function
import os
import sys
import imp
import numpy
import h5py
import tempfile

from lazyflow.graph import Graph
from lazyflow.operators.ioOperators import OpStackLoader
from lazyflow.operators.opReorderAxes import OpReorderAxes

import ilastik
from lazyflow.utility.timer import timeLogged
from ilastik.utility.slicingtools import sl, slicing2shape
from ilastik.shell.projectManager import ProjectManager
from ilastik.shell.headless.headlessShell import HeadlessShell
from ilastik.workflows.pixelClassification import PixelClassificationWorkflow

import logging
logger = logging.getLogger(__name__)
#logger.setLevel(logging.DEBUG)

class TestPixelClassificationHeadless(object):
    
    # Project and data are kept in different directories so we can test both absolute and relative paths.
    project_dir = tempfile.mkdtemp()
    data_dir = tempfile.mkdtemp()
    PROJECT_FILE = os.path.join(project_dir, 'test_project.ilp')
    PROJECT_FILE_RAW_DATA = os.path.join(project_dir, 'test_project_raw_data.ilp')
    # To be deleted after creating the project file in order to test headless with no raw data
    RAW_DATA = os.path.join(data_dir, 'raw_data.npy')
    SAMPLE_DATA = os.path.join(data_dir, 'random_data.npy')
    SAMPLE_MASK = os.path.join(data_dir, 'mask.npy')

    @classmethod
    def setup_class(cls):
        print('looking for ilastik.py...')
        # Load the ilastik startup script as a module.
        # Do it here in setupClass to ensure that it isn't loaded more than once.
        ilastik_entry_file_path = os.path.join( os.path.split( os.path.realpath(ilastik.__file__) )[0], "../ilastik.py" )
        if not os.path.exists( ilastik_entry_file_path ):
            raise RuntimeError("Couldn't find ilastik.py startup script: {}".format( ilastik_entry_file_path ))
            
        print('starting setup...')
        cls.original_cwd = os.getcwd()
        os.chdir(cls.data_dir)

        cls.create_random_data(cls.RAW_DATA)
        cls.create_random_data(cls.SAMPLE_DATA)
        cls.create_mask(cls.SAMPLE_MASK)

        cls.create_new_project(cls.PROJECT_FILE, cls.SAMPLE_DATA)
        cls.create_new_project(cls.PROJECT_FILE_RAW_DATA, cls.RAW_DATA)

        cls.ilastik_startup = imp.load_source( 'ilastik_startup', ilastik_entry_file_path )

    @classmethod
    def teardown_class(cls):
        os.chdir(cls.original_cwd)
        # Clean up: Delete any test files we generated
        removeFiles = [cls.PROJECT_FILE, cls.PROJECT_FILE_RAW_DATA, cls.SAMPLE_DATA, cls.SAMPLE_MASK]

        for f in removeFiles:
            try:
                os.remove(f)
            except:
                pass

    @classmethod
    def create_random_data(cls, file_path):
        numpy.save(file_path, numpy.random.randint(0, 256, (2, 20, 20, 5, 1), dtype=numpy.uint8))

    @classmethod
    def create_mask(cls, file_path):
        numpy.save(file_path, numpy.ones((2, 20, 20, 5, 1), dtype=numpy.uint8))

    @classmethod
    def create_new_project(cls, project_file_path, dataset_path):
        # Instantiate 'shell'
        shell = HeadlessShell()
        
        # Create a blank project file and load it.
        newProjectFile = ProjectManager.createBlankProjectFile(project_file_path, PixelClassificationWorkflow, [])
        newProjectFile.close()
        shell.openProjectFile(project_file_path)
        workflow = shell.workflow
        
        # Add a file
        from ilastik.applets.dataSelection.opDataSelection import DatasetInfo
        info = DatasetInfo()
        info.filePath = dataset_path
        opDataSelection = workflow.dataSelectionApplet.topLevelOperator
        opDataSelection.DatasetGroup.resize(1)
        opDataSelection.DatasetGroup[0][0].setValue(info)
        
        
        # Set some features
        ScalesList = [0.3, 0.7, 1, 1.6, 3.5, 5.0, 10.0]    
        FeatureIds = [ 'GaussianSmoothing',
                       'LaplacianOfGaussian',
                       'StructureTensorEigenvalues',
                       'HessianOfGaussianEigenvalues',
                       'GaussianGradientMagnitude',
                       'DifferenceOfGaussians' ]

        opFeatures = workflow.featureSelectionApplet.topLevelOperator
        opFeatures.Scales.setValue( ScalesList )
        opFeatures.FeatureIds.setValue( FeatureIds )

        #                    sigma:   0.3    0.7    1.0    1.6    3.5    5.0   10.0
        selections = numpy.array( [[True, False, False, False, False, False, False],
                                   [True, False, False, False, False, False, False],
                                   [True, False, False, False, False, False, False],
                                   [False, False, False, False, False, False, False],
                                   [False, False, False, False, False, False, False],
                                   [False, False, False, False, False, False, False]] )
        opFeatures.SelectionMatrix.setValue(selections)
    
        # Add some labels directly to the operator
        opPixelClass = workflow.pcApplet.topLevelOperator

        opPixelClass.LabelNames.setValue(['Label 1', 'Label 2'])

        slicing1 = sl[0:1,0:10,0:10,0:1,0:1]
        labels1 = 1 * numpy.ones(slicing2shape(slicing1), dtype=numpy.uint8)
        opPixelClass.LabelInputs[0][slicing1] = labels1

        slicing2 = sl[0:1,0:10,10:20,0:1,0:1]
        labels2 = 2 * numpy.ones(slicing2shape(slicing2), dtype=numpy.uint8)
        opPixelClass.LabelInputs[0][slicing2] = labels2

        # Train the classifier
        opPixelClass.FreezePredictions.setValue(False)
        _ = opPixelClass.Classifier.value

        # Save and close
        shell.projectManager.saveProject()
        del shell
        
    @timeLogged(logger)
    def testBasic(self):
        # NOTE: In this test, cmd-line args to tests will also end up getting "parsed" by ilastik.
        #       That shouldn't be an issue, since the pixel classification workflow ignores unrecognized options.
        #       See if __name__ == __main__ section, below.
        args = "--project=" + self.PROJECT_FILE
        args += " --headless"
        
        #args += " --sys_tmp_dir=/tmp"

        # Batch export options
        args += " --output_format=hdf5"
        args += " --output_filename_format={dataset_dir}/{nickname}_prediction.h5"
        args += " --output_internal_path=volume/pred_volume"
        args += " --raw_data"
        # test that relative path works correctly: should be relative to cwd, not project file.
        args += " " + os.path.normpath(os.path.relpath(self.SAMPLE_DATA, os.getcwd()))
        args += " --prediction_mask"
        args += " " + self.SAMPLE_MASK

        old_sys_argv = list(sys.argv)
        sys.argv = ['ilastik.py'] # Clear the existing commandline args so it looks like we're starting fresh.
        sys.argv += args.split()

        # Start up the ilastik.py entry script as if we had launched it from the command line
        try:
            self.ilastik_startup.main()
        finally:
            sys.argv = old_sys_argv
        
        # Examine the output for basic attributes
        output_path = self.SAMPLE_DATA[:-4] + "_prediction.h5"
        with h5py.File(output_path, 'r') as f:
            assert "/volume/pred_volume" in f
            pred_shape = f["/volume/pred_volume"].shape
            # Assume channel is last axis
            assert pred_shape[:-1] == (2, 20, 20, 5), "Prediction volume has wrong shape: {}".format( pred_shape )
            assert pred_shape[-1] == 2, "Prediction volume has wrong shape: {}".format( pred_shape )
        
    @timeLogged(logger)
    def testLotsOfOptions(self):
        #OLD_LAZYFLOW_STATUS_MONITOR_SECONDS = os.getenv("LAZYFLOW_STATUS_MONITOR_SECONDS", None)
        #os.environ["LAZYFLOW_STATUS_MONITOR_SECONDS"] = "1"
        
        # NOTE: In this test, cmd-line args to tests will also end up getting "parsed" by ilastik.
        #       That shouldn't be an issue, since the pixel classification workflow ignores unrecognized options.
        #       See if __name__ == __main__ section, below.
        args = []
        args.append( "--project=" + self.PROJECT_FILE )
        args.append( "--headless" )
        #args.append( "--sys_tmp_dir=/tmp" )
 
        # Batch export options
        args.append( '--export_source=Simple Segmentation' )
        args.append( '--output_format=png sequence' ) # If we were actually launching from the command line, 'png sequence' would be in quotes...
        args.append( "--output_filename_format={dataset_dir}/{nickname}_segmentation_z{slice_index}.png" )
        args.append( "--export_dtype=uint8" )
        args.append( "--output_axis_order=zxyc" )
         
        args.append( "--pipeline_result_drange=(0,2)" )
        args.append( "--export_drange=(0,255)" )
 
        args.append( "--cutout_subregion=[(0,10,10,0,0), (1, 20, 20, 5, 1)]" )
        args.append( self.SAMPLE_DATA )
 
        old_sys_argv = list(sys.argv)
        sys.argv = ['ilastik.py'] # Clear the existing commandline args so it looks like we're starting fresh.
        sys.argv += args
 
        # Start up the ilastik.py entry script as if we had launched it from the command line
        # This will execute the batch mode script
        try:
            self.ilastik_startup.main()
        finally:
            sys.argv = old_sys_argv
#             if OLD_LAZYFLOW_STATUS_MONITOR_SECONDS:
#                 os.environ["LAZYFLOW_STATUS_MONITOR_SECONDS"] = OLD_LAZYFLOW_STATUS_MONITOR_SECONDS
 
        output_path = self.SAMPLE_DATA[:-4] + "_segmentation_z{slice_index}.png"
        globstring = output_path.format( slice_index=999 )
        globstring = globstring.replace('999', '*')
 
        opReader = OpStackLoader( graph=Graph() )
        opReader.globstring.setValue( globstring )
 
        # (The OpStackLoader produces txyzc order.)
        opReorderAxes = OpReorderAxes( graph=Graph() )
        opReorderAxes.AxisOrder.setValue( 'tzyxc' )
        opReorderAxes.Input.connect( opReader.stack )
         
        try:
            readData = opReorderAxes.Output[:].wait()
     
            # Check basic attributes
            assert readData.shape[:-1] == (1, 10, 10, 5), readData.shape[:-1]  # Assume channel is last axis
            assert readData.shape[-1] == 1, "Wrong number of channels.  Expected 1, got {}".format( readData.shape[-1] )
        finally:
            # Clean-up.
            opReorderAxes.cleanUp()
            opReader.cleanUp()

    def testHeadlessNoRawData(self):
        # Delete raw data first
        os.remove(self.RAW_DATA)

        args = []
        # Use the project with RAW_DATA
        args.append("--project=" + self.PROJECT_FILE_RAW_DATA)
        args.append("--headless")

        # Batch export options
        args.append("--export_source=Simple Segmentation")
        args.append("--output_internal_path=volume/segm_volume")
        args.append("--output_format=hdf5")
        args.append("--output_filename_format={dataset_dir}/{nickname}_segm.h5")
        args.append("--export_dtype=uint8")
        args.append(self.SAMPLE_DATA)

        old_sys_argv = list(sys.argv)
        sys.argv = ['ilastik.py']
        sys.argv += args

        # Start up the ilastik.py entry script as if we had launched it from the command line
        try:
            self.ilastik_startup.main()
        finally:
            sys.argv = old_sys_argv

        # Examine the output for basic attributes
        output_path = self.SAMPLE_DATA[:-4] + "_segm.h5"
        with h5py.File(output_path, 'r') as f:
            assert "/volume/segm_volume" in f
            segm_shape = f["/volume/segm_volume"].shape
            # Assume channel is last axis
            assert segm_shape[:-1] == (2, 20, 20, 5), "Segmentation volume has wrong shape: {}".format(segm_shape)
            assert segm_shape[-1] == 1, "Segmentation volume has wrong shape: {}".format(segm_shape)
