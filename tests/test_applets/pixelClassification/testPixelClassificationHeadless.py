import os
import numpy
import h5py
import unittest
import tempfile

from ilastik.utility.slicingtools import sl, slicing2shape
from workflows.pixelClassification import PixelClassificationWorkflow
from ilastik.shell.headless.startShellHeadless import startShellHeadless

import workflows.pixelClassification.pixelClassificationWorkflowMainHeadless as pcMainHeadless

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
        shell, workflow = startShellHeadless( PixelClassificationWorkflow )
        
        # Create a blank project file and load it.
        newProjectFilePath = cls.PROJECT_FILE
        newProjectFile = shell.projectManager.createBlankProjectFile(newProjectFilePath)
        shell.projectManager.loadProject(newProjectFile, newProjectFilePath)
        
        # Add a file
        from ilastik.applets.dataSelection.opDataSelection import DatasetInfo
        info = DatasetInfo()
        info.filePath = cls.SAMPLE_DATA
        opDataSelection = workflow.dataSelectionApplet.topLevelOperator
        opDataSelection.Dataset.resize(1)
        opDataSelection.Dataset[0].setValue(info)
        
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

        slicing1 = sl[0:1,0:10,0:10,0:1,0:1]
        labels1 = 1 * numpy.ones(slicing2shape(slicing1), dtype=numpy.uint8)
        opPixelClass.LabelInputs[0][slicing1] = labels1

        slicing2 = sl[0:1,0:10,10:20,0:1,0:1]
        labels2 = 2 * numpy.ones(slicing2shape(slicing2), dtype=numpy.uint8)
        opPixelClass.LabelInputs[0][slicing2] = labels2
        
        # Save and close
        shell.projectManager.saveProject()
        shell.projectManager.closeCurrentProject()

    def test(self):
        args = "ilastik_headless"
        args += " --project=" + self.PROJECT_FILE
        args += " " + self.SAMPLE_DATA
        args += " --batch_output_dataset_name=/volume/pred_volume"
        args += " --sys_tmp_dir=/tmp"

        argv = args.split()
        return_code = pcMainHeadless.main(argv)
        assert return_code == 0
        
        # Examine the output for basic attributes
        outputFilePath = self.SAMPLE_DATA[:-4] + "_prediction.h5"
        with h5py.File(outputFilePath, 'r') as f:
            assert "/volume/pred_volume" in f
            assert f["/volume/pred_volume"].shape[:-1] == self.data.shape[:-1] # Assume channel is last axis
            assert f["/volume/pred_volume"].shape[-1] == 2
        
if __name__ == "__main__":
    unittest.main()

#if __name__ == "__main__":
#    import sys
#    import nose
#    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
#    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
#    nose.run(defaultTest=__file__)
