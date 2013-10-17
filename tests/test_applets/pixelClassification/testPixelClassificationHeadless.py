import os
import sys
import imp
import numpy
import h5py
import unittest
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

class TestPixelClassificationHeadless(unittest.TestCase):
    dir = tempfile.mkdtemp()
    PROJECT_FILE = os.path.join(dir, 'test_project.ilp')
    #SAMPLE_DATA = os.path.split(__file__)[0] + '/synapse_small.npy'

    @classmethod
    def setUpClass(cls):
        if hasattr(cls, 'SAMPLE_DATA'):
            cls.using_random_data = False
        else:
            cls.using_random_data = True
            cls.create_random_tst_data()

        cls.create_new_tst_project()

    @classmethod
    def tearDownClass(cls):
        # Clean up: Delete any test files we generated
        removeFiles = [ TestPixelClassificationHeadless.PROJECT_FILE ]
        if cls.using_random_data:
            removeFiles += [ TestPixelClassificationHeadless.SAMPLE_DATA ]

        for f in removeFiles:        
            try:
                os.remove(f)
            except:
                pass

    @classmethod
    def create_random_tst_data(cls):
        cls.SAMPLE_DATA = os.path.join(cls.dir, 'random_data.npy')
        cls.data = numpy.random.random((1,200,200,50,1))
        cls.data *= 256
        numpy.save(cls.SAMPLE_DATA, cls.data.astype(numpy.uint8))

    @classmethod
    def create_new_tst_project(cls):
        # Instantiate 'shell'
        shell = HeadlessShell(  )
        
        # Create a blank project file and load it.
        newProjectFilePath = cls.PROJECT_FILE
        newProjectFile = ProjectManager.createBlankProjectFile(newProjectFilePath, PixelClassificationWorkflow, [])
        newProjectFile.close()
        shell.openProjectFile(newProjectFilePath)
        workflow = shell.workflow
        
        # Add a file
        from ilastik.applets.dataSelection.opDataSelection import DatasetInfo
        info = DatasetInfo()
        info.filePath = cls.SAMPLE_DATA
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

        # Save and close
        shell.projectManager.saveProject()
        del shell
        
    @timeLogged(logger)
    def testBasic(self):
        # NOTE: In this test, cmd-line args to nosetests will also end up getting "parsed" by ilastik.
        #       That shouldn't be an issue, since the pixel classification workflow ignores unrecognized options.
        #       See if __name__ == __main__ section, below.
        args = "--project=" + self.PROJECT_FILE
        args += " --headless"
        args += " --sys_tmp_dir=/tmp"

        # Batch export options
        args += " --output_format=hdf5"
        args += " --output_filename_format={dataset_dir}/{nickname}_prediction.h5"
        args += " --output_internal_path=volume/pred_volume"
        args += " " + self.SAMPLE_DATA

        sys.argv = ['ilastik.py'] # Clear the existing commandline args so it looks like we're starting fresh.
        sys.argv += args.split()

        # Start up the ilastik.py entry script as if we had launched it from the command line
        ilastik_entry_file_path = os.path.join( os.path.split( ilastik.__file__ )[0], "../ilastik.py" )
        imp.load_source( 'main', ilastik_entry_file_path )
        
        # Examine the output for basic attributes
        output_path = self.SAMPLE_DATA[:-4] + "_prediction.h5"
        with h5py.File(output_path, 'r') as f:
            assert "/volume/pred_volume" in f
            pred_shape = f["/volume/pred_volume"].shape
            # Assume channel is last axis
            assert pred_shape[:-1] == self.data.shape[:-1], "Prediction volume has wrong shape: {}".format( pred_shape )
            assert pred_shape[-1] == 2, "Prediction volume has wrong shape: {}".format( pred_shape )
        
    @timeLogged(logger)
    def testLotsOfOptions(self):
        # NOTE: In this test, cmd-line args to nosetests will also end up getting "parsed" by ilastik.
        #       That shouldn't be an issue, since the pixel classification workflow ignores unrecognized options.
        #       See if __name__ == __main__ section, below.
        args = []
        args.append( "--project=" + self.PROJECT_FILE )
        args.append( "--headless" )
        args.append( "--sys_tmp_dir=/tmp" )

        # Batch export options
        args.append( '--output_format=png sequence' ) # If we were actually launching from the command line, 'png sequence' would be in quotes...
        args.append( "--output_filename_format={dataset_dir}/{nickname}_prediction_z{slice_index}.png" )
        args.append( "--export_dtype=uint8" )
        args.append( "--output_axis_order=zxyc" )
        
        args.append( "--pipeline_result_drange=(0.0,1.0)" )
        args.append( "--export_drange=(0,255)" )

        args.append( "--cutout_subregion=[(0,50,50,0,0), (1, 150, 150, 50, 2)]" )
        args.append( self.SAMPLE_DATA )

        sys.argv = ['ilastik.py'] # Clear the existing commandline args so it looks like we're starting fresh.
        sys.argv += args

        # Start up the ilastik.py entry script as if we had launched it from the command line
        # This will execute the batch mode script
        ilastik_entry_file_path = os.path.join( os.path.split( ilastik.__file__ )[0], "../ilastik.py" )
        imp.load_source( 'main', ilastik_entry_file_path )

        output_path = self.SAMPLE_DATA[:-4] + "_prediction_z{slice_index}.png"
        globstring = output_path.format( slice_index=999 )
        globstring = globstring.replace('999', '*')

        opReader = OpStackLoader( graph=Graph() )
        opReader.globstring.setValue( globstring )

        # (The OpStackLoader produces txyzc order.)
        opReorderAxes = OpReorderAxes( graph=Graph() )
        opReorderAxes.AxisOrder.setValue( 'txyzc' )
        opReorderAxes.Input.connect( opReader.stack )
        
        readData = opReorderAxes.Output[:].wait()

        # Check basic attributes
        assert readData.shape[:-1] == self.data[0:1, 50:150, 50:150, 0:50, 0:2].shape[:-1] # Assume channel is last axis
        assert readData.shape[-1] == 2, "Wrong number of channels.  Expected 2, got {}".format( readData.shape[-1] )

if __name__ == "__main__":
    #make the program quit on Ctrl+C
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
