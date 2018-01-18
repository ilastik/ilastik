import numpy
from functools import partial
import os

from collections import OrderedDict
import logging

from volumina.api import LazyflowSource, AlphaModulatedLayer, GrayscaleLayer, ColortableLayer


from PyQt5 import uic
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtWidgets import QWidget, QHeaderView, QStackedWidget, QTableWidgetItem, QPushButton, QMessageBox
from PyQt5.QtGui import QColor, QIcon, QCursor
from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui
import vigra
from lazyflow.classifiers import TikTorchLazyflowClassifier

logger = logging.getLogger(__name__)



class NNClassGui(LayerViewerGui):

    def viewerControlWidget(self):
        return self._viewerControlUi

    def centralWidget( self ):
        return self

    def stopAndCleanUp(self):
        for fn in self.__cleanup_fns:
            fn()

    def menus( self ):
        return []

    def appletDrawer(self):
        return self.drawer



    def __init__(self, parentApplet, topLevelOperator):
        super(NNClassGui, self).__init__(parentApplet, topLevelOperator)

        self.parentApplet = parentApplet
        self.drawer = None
        self.topLevelOperator = topLevelOperator

        self.__cleanup_fns = []

        self._initAppletDrawerUic()
        self.initViewerControls()
        self.initViewerControlUi() #ToDO


    



    def _initAppletDrawerUic(self, drawerPath=None):
        """
        Load the ui file for the applet drawer, which we own.
        """
        if drawerPath is None:
            localDir = os.path.split(__file__)[0]
            drawerPath = os.path.join( localDir, "nnClassAppletUiTest.ui")
        self.drawer = uic.loadUi(drawerPath)

        self.drawer.comboBox.clear()

        self.classifier_factories = self.get_NN_classifier()

        self.drawer.comboBox.addItems(self.classifier_factories)

        self.drawer.predictButton.clicked.connect(self.pred_nn)
        


    def initViewerControls(self):
        self._viewerControlWidgetStack = QStackedWidget(parent=self)



    def initViewerControlUi(self):
        """
        Load the viewer controls GUI, which appears below the applet bar.
        In our case, the viewer control GUI consists mainly of a layer list.
        """
        localDir = os.path.split(__file__)[0]
        self._viewerControlUi = uic.loadUi( os.path.join( localDir, "viewerControls.ui" ) )

        def nextCheckState(checkbox):
            checkbox.setChecked( not checkbox.isChecked() )
        self._viewerControlUi.checkShowPredictions.nextCheckState = partial(nextCheckState, self._viewerControlUi.checkShowPredictions)

        self._viewerControlUi.checkShowPredictions.clicked.connect( self.handleShowPredictionsClicked )

        model = self.editor.layerStack
        self._viewerControlUi.viewerControls.setupConnections(model)



    def setupLayers(self):
        """
        which layers will be shown in the layerviewergui
        """

        layers = super(NNClassGui, self).setupLayers()

        inputSlot = self.topLevelOperator.InputImage

        
        # layers = []

        # if inputSlot.ready(): 
        #     rawLayer = self.createStandardLayerFromSlot(inputSlot)
        #     rawLayer.visible = True
        #     rawLayer.opacity = 1.0
        #     rawLayer.name = "Raw Data (display only)" 
        #     layers.append(rawLayer)

        predictionSlot = self.topLevelOperator.CachedPredictionProbabilities

        if predictionSlot.ready():
            print ("RDYY")
            predictsrc = LazyflowSource(predictionSlot)
            predictionLayer = GrayscaleLayer(predictsrc)
            predictionLayer.visible = self.drawer.liveUpdateButton.isChecked()
            predictionLayer.opacity = 1.0
            predictionLayer.name = "Prediction" 
            predictionLayer.visibleChanged.connect(self.updateShowPredictionCheckbox)
            layers.append(predictionLayer)


        return layers
       

    def get_NN_classifier(self):

        classifiers = OrderedDict()
        PYTORCH_MODEL_FILE_PATH = '/Users/jmassa/Downloads/dunet-cpu-chaubold-new.nn' #HARDCODED!!!!!!

        # try:

        classifiers['DUNet Prediction'] = TikTorchLazyflowClassifier(None, PYTORCH_MODEL_FILE_PATH)
 
        # except ImportError:
        #     logger.warn("gui: Could not import pytorch classifier")

        classifiers['Dummy1'] = 0
        classifiers['Dummy2'] = 1 

        return classifiers

    def pred_nn(self):

        classifier_key = self.drawer.comboBox.itemText(0)
        print (classifier_key)

        # print (self.topLevelOperator.InputImage.meta.shape)
        blockshape = numpy.array([1,448,448,None])

        self.topLevelOperator.BlockShape.setValue(blockshape)
        print ("blockshape", blockshape )

        # result = self.classifier_factories[classifier_key].predict_probabilities_pixelwise(self.topLevelOperator.InputImage.value, roi, axistags)
        self.topLevelOperator.Classifier.setValue(self.classifier_factories[classifier_key])

        predict = self.topLevelOperator.CachedPredictionProbabilities[:].wait()
        print ("Done")

        # numpy.save("/Users/jmassa/Desktop/predictions",predict)

  
    @pyqtSlot()
    def handleShowPredictionsClicked(self):
        checked = self._viewerControlUi.checkShowPredictions.isChecked()
        for layer in self.layerstack:
            if "Prediction" in layer.name:
                layer.visible = checked

    @pyqtSlot()
    def updateShowPredictionCheckbox(self):
        predictLayerCount = 0
        visibleCount = 0
        for layer in self.layerstack:
            if "Prediction" in layer.name:
                predictLayerCount += 1
                if layer.visible:
                    visibleCount += 1

        if visibleCount == 0:
            self._viewerControlUi.checkShowPredictions.setCheckState(Qt.Unchecked)
        elif predictLayerCount == visibleCount:
            self._viewerControlUi.checkShowPredictions.setCheckState(Qt.Checked)
        else:
            self._viewerControlUi.checkShowPredictions.setCheckState(Qt.PartiallyChecked)

