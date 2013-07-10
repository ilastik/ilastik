import ilastik.ilastik_logging
ilastik.ilastik_logging.default_config.init()

import unittest
import numpy
import vigra
from lazyflow.graph import Graph
from ilastik.applets.objectClassification.opObjectClassification import \
    OpRelabelSegmentation, OpObjectTrain, OpObjectPredict, OpObjectClassification
    
from ilastik.applets import objectExtraction
from ilastik.applets.objectExtraction.opObjectExtraction import \
    OpRegionFeatures, OpAdaptTimeListRoi, OpObjectExtraction

import h5py

class TestWithCube(object):
    def setUp(self):
        
        self.features = {"Vigra Object Features": {\
                                     "Count":{}, \
                                     "Mean":{}, \
                                     "Mean in neighborhood":{"margin":(5, 5, 2)}}}

        self.rawimg = numpy.zeros((200, 200, 20, 1), dtype=numpy.uint8)
        self.binimg = numpy.zeros((200, 200, 20, 1), dtype=numpy.uint8)
        
        self.rawimg[0:100, :, :, :] = 50
        #small white
        self.rawimg[5:10, 5:10, 9:11, :] = 255
        self.rawimg[20:25, 20:25, 9:11, :] = 255
        self.rawimg[35:40, 30:35, 9:11, :] = 255
        self.rawimg[50:55, 50:55, 9:11, :] = 255
        
        self.rawimg[105:110, 5:10, 9:11, :] = 255
        self.rawimg[120:125, 20:25, 9:11, :] = 255
        self.rawimg[135:140, 30:35, 9:11, :] = 255
        self.rawimg[150:155, 150:155, 9:11, :] = 255
        
        #small grey
        self.rawimg[145:150, 5:10, 9:11, :] = 150
        self.rawimg[160:165, 40:45, 9:11, :] = 150
        self.rawimg[175:180, 20:25, 9:11, :] = 150
        self.rawimg[175:180, 5:10, 9:11, :] = 150
        
        self.rawimg[45:50, 5:10, 9:11, :] = 150
        self.rawimg[60:65, 40:45, 9:11, :] = 150
        self.rawimg[75:80, 20:25, 9:11, :] = 150
        self.rawimg[75:80, 5:10, 9:11, :] = 150
        
        #large white
        self.rawimg[50:70, 150:170, 9:11, :] = 255
        self.rawimg[5:25, 60:80, 9:11, :] = 255
        self.rawimg[5:25, 170:190, 9:11, :] = 255
        self.rawimg[70:90, 90:110, 9:11, :] = 255
        
        self.rawimg[150:170, 150:170, 9:11, :] = 255
        self.rawimg[105:125, 60:80, 9:11, :] = 255
        self.rawimg[105:125, 170:190, 9:11, :] = 255
        self.rawimg[170:190, 90:110, 9:11, :] = 255
        
        #large grey
        self.rawimg[5:25, 90:110, 9:11, :] = 150
        self.rawimg[30:50, 90:110, 9:11, :] = 150
        self.rawimg[5:25, 120:140, 9:11, :] = 150
        self.rawimg[30:50, 120:140, 9:11, :] = 150
        
        self.rawimg[105:125, 90:110, 9:11, :] = 150
        self.rawimg[130:150, 90:110, 9:11, :] = 150
        self.rawimg[105:125, 120:140, 9:11, :] = 150
        self.rawimg[130:150, 120:140, 9:11, :] = 150
        
        self.binimg = (self.rawimg>55).astype(numpy.uint8)
        
        #make 5d, the workflow has a make 5d in the beginning of the pipeline
        self.rawimg = self.rawimg.reshape((1,)+self.rawimg.shape)
        self.rawimg = vigra.taggedView(self.rawimg, 'txyzc')
        self.binimg = self.binimg.reshape((1,)+self.binimg.shape)
        self.binimg = vigra.taggedView(self.binimg, 'txyzc')

    def test(self):
        gr = Graph()
        opExtract = OpObjectExtraction(graph=gr)
        opPredict = OpObjectClassification(graph=gr)
        
        opExtract.RawImage.setValue(self.rawimg)
        opExtract.BinaryImage.setValue(self.binimg)
        opExtract.Features.setValue(self.features)
        
        opPredict.RawImages.setValues([self.rawimg])
        opPredict.BinaryImages.setValues([self.binimg])
        opPredict.SegmentationImages.resize(1)
        opPredict.SegmentationImages[0].connect(opExtract.LabelImage)
        opPredict.ObjectFeatures.resize(1)
        opPredict.ObjectFeatures[0].connect(opExtract.RegionFeatures)
        opPredict.ComputedFeatureNames.connect(opExtract.ComputedFeatureNames)
        
        #run the workflow with the test blocks in the gui, 
        #if you want to see why these labels are chosen
        #object 11 -small white square
        #object 27 -large grey square
        labelArray = numpy.zeros((28,))
        labelArray[11] = 1
        labelArray[27] = 2
        labelDict = {0: labelArray}
        opPredict.LabelInputs.setValues([labelDict])
        
        #Predict by size
        selFeatures = {"Vigra Object Features": {"Count":{}}}
        opPredict.SelectedFeatures.setValue(selFeatures)
        #[0][0] - first image, first time slice
        predictions = opPredict.Predictions[0][0].wait()
        predicted_labels = predictions[0]
        assert predicted_labels[0]==0
        assert numpy.all(predicted_labels[1:16]==1)
        assert numpy.all(predicted_labels[16:]==2)
        
        #Predict by color
        selFeatures = {"Vigra Object Features": {"Mean":{}}}
        opPredict.SelectedFeatures.setValue(selFeatures)
        predictions = opPredict.Predictions[0][0].wait()
        predicted_labels = predictions[0]
        assert predicted_labels[0]==0
        assert predicted_labels[1]==1
        assert predicted_labels[11]==1
        assert predicted_labels[16]==1
        assert predicted_labels[23]==1
        assert predicted_labels[2]==2
        assert predicted_labels[18]==2
        assert predicted_labels[24]==2
        assert predicted_labels[26]==2        
        
        #Predict by neighborhood color
        selFeatures = {"Vigra Object Features": {"Mean in neighborhood":{"margin": (5, 5, 2)}}}
        opPredict.SelectedFeatures.setValue(selFeatures)
        predictions = opPredict.Predictions[0][0].wait()
        predicted_labels = predictions[0]
        assert predicted_labels[0]==0
        assert predicted_labels[1]==1
        assert predicted_labels[8]==1
        assert predicted_labels[24]==1
        assert predicted_labels[28]==1
        assert predicted_labels[9]==2
        assert predicted_labels[14]==2
        assert predicted_labels[26]==2
        assert predicted_labels[29]==2


if __name__ == '__main__':
    import sys
    import nose

    # Don't steal stdout. Show it on the console as usual.
    sys.argv.append("--nocapture")

    # Don't set the logging level to DEBUG. Leave it alone.
    sys.argv.append("--nologcapture")

    nose.run(defaultTest=__file__)
