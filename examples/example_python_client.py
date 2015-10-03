import collections

import numpy
import vigra

import ilastik_main
from ilastik.applets.dataSelection import DatasetInfo
from ilastik.workflows.pixelClassification import PixelClassificationWorkflow

# Programmatically set the command-line arguments directly into the argparse.Namespace object
# Provide your project file, and don't forget to specify headless.
args = ilastik_main.parser.parse_args([])
args.headless = True
args.project = '/Users/bergs/MyProject.ilp'

# Instantiate the 'shell', (in this case, an instance of ilastik.shell.HeadlessShell)
# This also loads the project file into shell.projectManager
shell = ilastik_main.main( args )
assert isinstance(shell.workflow, PixelClassificationWorkflow)

# Obtain the training operator
opPixelClassification = shell.workflow.pcApplet.topLevelOperator

# Sanity checks
assert len(opPixelClassification.InputImages) > 0
assert opPixelClassification.Classifier.ready()

# For this example, we'll use random input data to "batch process"
input_data1 = numpy.random.randint(0,255, (200,200,1) ).astype(numpy.uint8)
input_data2 = numpy.random.randint(0,255, (300,300,1) ).astype(numpy.uint8)
print input_data1.shape

input_data1 = vigra.taggedView( input_data1, 'yxc' )
input_data2 = vigra.taggedView( input_data2, 'yxc' )

label_names = opPixelClassification.LabelNames.value
label_colors = opPixelClassification.LabelColors.value
probability_colors = opPixelClassification.PmapColors.value

print label_names, label_colors, probability_colors

# See PixelClassificationWorkflow.ROLE_NAMES
role_data_dict = collections.OrderedDict([ ("Raw Data", [ DatasetInfo(preloaded_array=input_data1),
                                                          DatasetInfo(preloaded_array=input_data2) ]) ]) 

# Run the export via the BatchProcessingApplet
# TODO: This still outputs to disk.
#       Need to implement run_export_to_array()
shell.workflow.batchProcessingApplet.run_export(role_data_dict)
