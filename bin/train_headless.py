"""
Create a new project from scratch using a grayscale volume and label volume of the same shape.

At this time, this script does not provide a command-line API for selecting the features to train with.
Edit the feature matrix in the code below.

Also, this script's cmdline API supports only a single grayscale and label volume as input, 
but it can work with multiple input volumes if you simply edit RAW_DATA_FILEPATHS and LABEL_DATA_FILEPATHS in the code below.

Lastly, this script assumes you have only two label classes.  Edit NUM_LABEL_CLASSES to change.

Example usage (Mac):
    ./ilastik.app/Contents/MacOS/mac_execfile train_headless.py MyNewProject.ilp "/tmp/grayscale_stack/*.png" /tmp/labels.h5/data

Example usage (Linux):
    ./ilastik_python.sh train_headless.py MyNewProject.ilp "/tmp/grayscale_stack/*.png" /tmp/labels.h5/data

Note: This script does not make any attempt to be efficient with RAM usage.
      (The entire label volume is loaded at once.)  As a result, each image volume you 
      train with must be significantly smaller than the available RAM on your machine.
"""
import os
import argparse

import numpy

##
## READ BASIC CMDLINE PATHS
##

# Cmd-line args to this script.
parser = argparse.ArgumentParser()
parser.add_argument("new_project_name")
parser.add_argument("raw_data")
parser.add_argument("label_data")

parsed_args = parser.parse_args()

# Change these variables as needed.
NEW_PROJECT_NAME = parsed_args.new_project_name
RAW_DATA_FILEPATHS = [parsed_args.raw_data]
LABEL_DATA_FILEPATHS = [parsed_args.label_data]
NUM_LABEL_CLASSES = 2   # FIXME: This is hard-coded for now.  
                        #        Could be read from label volumes instead...

assert len(RAW_DATA_FILEPATHS) == len(LABEL_DATA_FILEPATHS)

##
## CONSTRUCT FEATURE MATRIX
## FIXME: Provide a cmdline API for this...
##

# Don't touch these lists!
ScalesList = [0.3, 0.7, 1, 1.6, 3.5, 5.0, 10.0]
FeatureIds = [ 'GaussianSmoothing',
               'LaplacianOfGaussian',
               'StructureTensorEigenvalues',
               'HessianOfGaussianEigenvalues',
               'GaussianGradientMagnitude',
               'DifferenceOfGaussians' ]

# #                    sigma:   0.3    0.7    1.0    1.6    3.5    5.0   10.0
# selections = numpy.array( [[False, False, False, False, False, False, False],
#                            [False, False, False, False, False, False, False],
#                            [False, False, False, False, False, False, False],
#                            [False, False, False, False, False, False, False],
#                            [False, False, False, False, False, False, False],
#                            [False, False, False, False, False, False, False]] )

# Start with an all-False matrix and apply the features we want.
selections = numpy.zeros( (len(FeatureIds), len(ScalesList)), dtype=bool )
def set_feature(feature_id, scale):
    selections[ FeatureIds.index(feature_id), ScalesList.index(scale) ] = True

set_feature('GaussianSmoothing',         1.0)
set_feature('LaplacianOfGaussian',       1.0)
set_feature('GaussianGradientMagnitude', 1.0)


###################################################################################################
###################################################################################################
## Shouldn't need to edit below this line...
###################################################################################################
###################################################################################################

import ilastik_main
from ilastik.workflows.pixelClassification import PixelClassificationWorkflow
from lazyflow.graph import Graph
from lazyflow.operators.ioOperators import OpInputDataReader
from lazyflow.roi import roiToSlice, roiFromShape

##
## CREATE PROJECT
##

# Manually configure the arguments to ilastik, as if they were parsed from the command line.
# (Start with empty args and fill in below.)
ilastik_args = ilastik_main.parser.parse_args([])
ilastik_args.new_project = NEW_PROJECT_NAME
ilastik_args.headless = True
ilastik_args.workflow = 'Pixel Classification'

shell = ilastik_main.main( ilastik_args )
assert isinstance(shell.workflow, PixelClassificationWorkflow)

##
## CONFIGURE GRAYSCALE INPUT
##

data_selection_applet = shell.workflow.dataSelectionApplet

# To configure data selection, start with empty cmdline args and manually fill them in
data_selection_args, _ = data_selection_applet.parse_known_cmdline_args([])
data_selection_args.raw_data = RAW_DATA_FILEPATHS
data_selection_args.preconvert_stacks = True

# Configure 
data_selection_applet.configure_operator_with_parsed_args(data_selection_args)

##
## APPLY FEATURE MATRIX (from matrix above)
##

opFeatures = shell.workflow.featureSelectionApplet.topLevelOperator
opFeatures.Scales.setValue( ScalesList )
opFeatures.FeatureIds.setValue( FeatureIds )
opFeatures.SelectionMatrix.setValue(selections)

##
## READ/APPLY LABEL VOLUMES
##

# The training operator
opPixelClassification = shell.workflow.pcApplet.topLevelOperator
label_names = map(str, range(NUM_LABEL_CLASSES))
opPixelClassification.LabelNames.setValue(label_names) 

# Read each label volume and inject the label data into the appropriate training slot
cwd = os.getcwd()
for lane, label_data_path in enumerate(LABEL_DATA_FILEPATHS):
    graph = Graph()
    opReader = OpInputDataReader(graph=graph)
    opReader.WorkingDirectory.setValue( cwd )
    opReader.FilePath.setValue( label_data_path )
    
    print "Reading label volume: {}".format( label_data_path )
    label_volume = opReader.Output[:].wait()
    axiskeys = opPixelClassification
    raw_shape = opPixelClassification.InputImages[lane].meta.shape
    if label_volume.ndim != len(raw_shape):
        # Append a singleton channel axis
        assert label_volume.ndim == len(raw_shape)-1
        label_volume = label_volume[...,None]

    print "Applying label volume to lane #{}".format(lane)
    entire_volume_slicing = roiToSlice(*roiFromShape(label_volume.shape))
    opPixelClassification.LabelInputs[lane][entire_volume_slicing] = label_volume

##
## REQUEST TRAINED CLASSIFIER
##

opPixelClassification.FreezePredictions.setValue(False)
_ = opPixelClassification.Classifier.value

##
## SAVE PROJECT
##

# save project file (saves new classifier).
shell.projectManager.saveProject(force_all_save=False)

print "DONE."
