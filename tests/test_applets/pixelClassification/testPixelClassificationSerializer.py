import os
import numpy
import h5py
import vigra
from lazyflow.graph import Graph, Operator, InputSlot, OutputSlot, MultiInputSlot, MultiOutputSlot
from lazyflow.operators import OpTrainRandomForestBlocked, OpValueCache
from ilastik.applets.pixelClassification.opPixelClassification import OpPixelClassification
from ilastik.applets.pixelClassification.pixelClassificationSerializer import PixelClassificationSerializer

import ilastik.ilastik_logging
ilastik.ilastik_logging.default_config.init()

class OpMockPixelClassifier(Operator):
    """
    This class is a simple stand-in for the real pixel classification operator.
    Uses hard-coded data shape and block shape.
    Provides hard-coded outputs.
    """
    name = "OpMockPixelClassifier"

    LabelInputs = MultiInputSlot(optional = True) # Input for providing label data from an external source

    NonzeroLabelBlocks = MultiOutputSlot(stype='object') # A list if slices that contain non-zero label values
    LabelImages = MultiOutputSlot() # Labels from the user
    
    Classifier = OutputSlot(stype='object')
    
    PredictionProbabilities = MultiOutputSlot()
    
    def __init__(self, *args, **kwargs):
        super(OpMockPixelClassifier, self).__init__(*args, **kwargs)
        self._data = []
        self.shape = (1,10,100,100,1)
        self.prediction_shape = self.shape[:-1] + (2,) # Hard-coded to provide 2 classes
        
        self.opClassifier = OpTrainRandomForestBlocked(graph=self.graph, parent=self)
        self.opClassifier.Labels.connect(self.LabelImages)
        self.opClassifier.nonzeroLabelBlocks.connect(self.NonzeroLabelBlocks)
        self.opClassifier.fixClassifier.setValue(False)
        
        self.classifier_cache = OpValueCache(graph=self.graph, parent=self)
        self.classifier_cache.Input.connect( self.opClassifier.Classifier )
        
        p1 = numpy.indices(self.shape).sum(0) / 207.0
        p2 = 1 - p1

        self.predictionData = numpy.concatenate((p1,p2), axis=4)
    
    def setupOutputs(self):
        numImages = len(self.LabelInputs)

        self.NonzeroLabelBlocks.resize( numImages )
        self.LabelImages.resize( numImages )
        self.PredictionProbabilities.resize( numImages )
        self.opClassifier.Images.resize( numImages )

        for i in range(numImages):
            self._data.append( numpy.zeros(self.shape) )
            self.NonzeroLabelBlocks[i].meta.shape = (1,)
            self.NonzeroLabelBlocks[i].meta.dtype = object

            self.LabelImages[i].meta.shape = self.shape
            self.LabelImages[i].meta.dtype = numpy.float64
            
            # Hard-coded: Two prediction classes
            self.PredictionProbabilities[i].meta.shape = self.prediction_shape
            self.PredictionProbabilities[i].meta.dtype = numpy.float64
            self.PredictionProbabilities[i].meta.axistags = vigra.defaultAxistags('txyzc')
            
            # Classify with random data
            self.opClassifier.Images[i].setValue( numpy.random.random(self.shape) )
        
        self.Classifier.connect( self.opClassifier.Classifier )
        
    def setSubInSlot(self, multislot, slot, index, key, value):
        assert slot.name == "LabelInputs"
        self._data[index][key] = value
        self.LabelImages[index].setDirty(key)
    
    def getSubOutSlot(self, slots, indexes, key, result):
        slot = slots[0]
        index = indexes[0]
        if slot.name == "NonzeroLabelBlocks":
            # Split into 10 chunks
            blocks = []
            slicing = [slice(0,max) for max in self.shape]
            chunks = numpy.split(self._data[index], 10, 2)
            for i in range(10):
                slicing[2] = slice(i*10, (i+1)*10)
                if not (self._data[index][slicing] == 0).all():
                    blocks.append( list(slicing) )

            result[0] = blocks
        if slot.name == "LabelImages":
            result[...] = self._data[index][key]
        if slot.name == "PredictionProbabilities":
            result[...] = self.predictionData[key]
            
class TestOpMockPixelClassifier(object):
    """
    Quick test for the stand-in operator we're using for the serializer test.
    """
    def test(self):
        g = Graph()
        op = OpMockPixelClassifier(graph=g)
        
        op.LabelInputs.resize( 1 )

        # Create some labels
        labeldata = numpy.zeros(op.shape)
        labeldata[:,:,0:5,:,:] = 7
        labeldata[:,:,50:60,:] = 8

        # Slice them into our operator
        op.LabelInputs[0][:,:,0:5,:,:] = labeldata[:,:,0:5,:,:]
        op.LabelInputs[0][:,:,50:60,:,:] = labeldata[:,:,50:60,:,:]

        assert (op._data[0] == labeldata).all()

        nonZeroBlocks = op.NonzeroLabelBlocks[0].value
        assert len(nonZeroBlocks) == 2
        assert nonZeroBlocks[0][2].start == 0
        assert nonZeroBlocks[1][2].start == 50
        
        assert op.Classifier.ready()
        

class TestPixelClassificationSerializer(object):

    def test(self):    
        # Define the files we'll be making    
        testProjectName = 'test_project.ilp'
        # Clean up: Remove the test data files we created last time (just in case)
        for f in [testProjectName]:
            try:
                os.remove(f)
            except:
                pass
    
        # Create an empty project
        testProject = h5py.File(testProjectName)
        testProject.create_dataset("ilastikVersion", data=0.6)
        
        # Create an operator to work with and give it some input
        g = Graph()
        op = OpMockPixelClassifier(graph=g)
        operatorToSave = op
        serializer = PixelClassificationSerializer(operatorToSave, 'PixelClassificationTest')
        
        op.LabelInputs.resize( 1 )

        # Create some labels
        labeldata = numpy.zeros(op.shape)
        labeldata[:,:,0:5,:,:] = 1
        labeldata[:,:,50:60,:] = 2

        # Slice them into our operator
        op.LabelInputs[0][:,:,0:5,:,:] = labeldata[:,:,0:5,:,:]
        op.LabelInputs[0][:,:,50:60,:,:] = labeldata[:,:,50:60,:,:]
        
        # Simulate the predictions changing by setting the prediction output dirty
        op.PredictionProbabilities[0].setDirty(slice(None))

        # Enable prediction storage
        serializer.predictionStorageEnabled = True
            
        # Serialize!
        serializer.serializeToHdf5(testProject, testProjectName)

        # Check that the prediction data was written to the file
        assert (testProject['PixelClassificationTest/Predictions/predictions0000'][...] == op.PredictionProbabilities[0][...].wait()).all()
        
        # Deserialize into a fresh operator
        operatorToLoad = OpMockPixelClassifier(graph=g)
        deserializer = PixelClassificationSerializer(operatorToLoad, 'PixelClassificationTest')
        deserializer.deserializeFromHdf5(testProject, testProjectName)

        # Did the data go in and out of the file without problems?
        assert len(operatorToLoad.LabelImages) == 1
        assert (operatorToSave.LabelImages[0][...].wait() == operatorToLoad.LabelImages[0][...].wait()).all()
        assert (operatorToSave.LabelImages[0][...].wait() == labeldata[...]).all()
        
        os.remove(testProjectName)

if __name__ == "__main__":
    import nose
    nose.run(defaultTest=__file__, env={'NOSE_NOCAPTURE' : 1})

