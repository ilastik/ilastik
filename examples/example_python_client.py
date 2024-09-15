from collections import OrderedDict

import numpy
import vigra
import os

from ilastik import app
from ilastik.applets.dataSelection.opDataSelection import PreloadedArrayDatasetInfo
from ilastik.workflows.pixelClassification import PixelClassificationWorkflow

args = app.parse_args([])
args.headless = True
args.project = "/Users/bergs/MyProject.ilp"  # REPLACE WITH YOUR PROJECT FILE

# Instantiate the 'shell', (in this case, an instance of ilastik.shell.HeadlessShell)
# This also loads the project file into shell.projectManager
shell = app.main(args)
assert isinstance(shell.workflow, PixelClassificationWorkflow)

# Obtain the training operator
opPixelClassification = shell.workflow.pcApplet.topLevelOperator

# Sanity checks
assert len(opPixelClassification.InputImages) > 0
assert opPixelClassification.Classifier.ready()

# For this example, we'll use random input data to "batch process"
input_data1 = numpy.random.randint(0, 255, (200, 200, 1)).astype(numpy.uint8)
input_data2 = numpy.random.randint(0, 255, (300, 300, 1)).astype(numpy.uint8)
print(input_data1.shape)

input_data1 = vigra.taggedView(input_data1, "yxc")
input_data2 = vigra.taggedView(input_data2, "yxc")

# Construct an OrderedDict of role-names -> DatasetInfos
# (See PixelClassificationWorkflow.ROLE_NAMES)
role_data_dict = OrderedDict(
    [
        (
            "Raw Data",
            [
                PreloadedArrayDatasetInfo(preloaded_array=input_data1),
                PreloadedArrayDatasetInfo(preloaded_array=input_data2),
            ],
        )
    ]
)

predictions = shell.workflow.batchProcessingApplet.run_export(role_data_dict, export_to_array=True)
