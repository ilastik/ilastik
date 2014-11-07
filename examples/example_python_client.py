import numpy
import vigra

import ilastik_main
from ilastik.workflows.pixelClassification import PixelClassificationWorkflow

args = ilastik_main.parser.parse_args([])
args.headless = True
args.project = '/Users/bergs/MyProject.ilp'

shell = ilastik_main.main( args )
assert isinstance(shell.workflow, PixelClassificationWorkflow)

# The training operator
opPixelClassification = shell.workflow.pcApplet.topLevelOperator

# Sanity checks
assert len(opPixelClassification.InputImages) > 0
assert opPixelClassification.Classifier.ready()

# For this example, we'll use random input data to "batch process"
input_data = numpy.random.randint(0,255, (200,200,1) ).astype(numpy.uint8)
print input_data.shape
input_data = vigra.taggedView( input_data, 'yxc' )

label_names = opPixelClassification.LabelNames.value
label_colors = opPixelClassification.LabelColors.value
probability_colors = opPixelClassification.PmapColors.value

print label_names, label_colors, probability_colors

# Change the connections of the batch prediction pipeline so we can supply our own data.
opBatchFeatures = shell.workflow.opBatchFeatures
opBatchPredictionPipeline = shell.workflow.opBatchPredictionPipeline

opBatchFeatures.InputImage.disconnect()
opBatchFeatures.InputImage.resize(1)
opBatchFeatures.InputImage[0].setValue( input_data )

# Run prediction.
assert len(opBatchPredictionPipeline.HeadlessPredictionProbabilities) == 1
assert opBatchPredictionPipeline.HeadlessPredictionProbabilities[0].ready()
predictions = opBatchPredictionPipeline.HeadlessPredictionProbabilities[0][:].wait()

print "Prediction shape: {}".format( predictions.shape )




