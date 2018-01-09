import numpy
import os

from collections import OrderedDict
import logging

from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QHeaderView, QStackedWidget, QTableWidgetItem, QPushButton, QMessageBox
from PyQt5.QtGui import QColor, QIcon, QCursor
from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui
import vigra

logger = logging.getLogger(__name__)



class NNClassGui(LayerViewerGui):

    def viewerControlWidget(self):
        return self._viewerControlWidgetStack

    def centralWidget( self ):
        return self

    def stopAndCleanUp(self):
        for fn in self.__cleanup_fns:
            fn()

    def menus( self ):
        return []

    def setImageIndex(self, index):
        pass

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
        self. initViewerControlUi() #ToDO


    



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

        return 0


    def setupLayers(self):
        """
        which layers will be shown in the layerviewergui
        """
        opFeatureSelection = self.topLevelOperator
        inputSlot = opFeatureSelection.InputImage
        
        layers = []

        if inputSlot.ready(): 
            rawLayer = self.createStandardLayerFromSlot(inputSlot)
            rawLayer.visible = True
            rawLayer.opacity = 1.0
            rawLayer.name = "Raw Data (display only)" 
            layers.append(rawLayer)

        return layers
       

    def get_NN_classifier(self):

        classifiers = OrderedDict()
        PYTORCH_MODEL_FILE_PATH = '/Users/jmassa/Downloads/dunet-cpu-chaubold.nn' #HARDCODED!!!!!!

        # try:
        from lazyflow.classifiers import TikTorchLazyflowClassifier

        classifiers['PyTorch CNN Prediction'] = TikTorchLazyflowClassifier(None, PYTORCH_MODEL_FILE_PATH)
 
        # except ImportError:
        #     logger.warn("gui: Could not import pytorch classifier")

        classifiers['Dummy1'] = 0
        classifiers['Dummy2'] = 1

        return classifiers

    def pred_nn(self):

        classifier_key = self.drawer.comboBox.itemText(0)
        print (classifier_key)

        print (self.topLevelOperator.InputImage.meta.shape)

        roi = ([0,0,0],self.topLevelOperator.InputImage.meta.shape[1:])
        print(roi)

        result = self.classifier_factories[classifier_key].predict_probabilities_pixelwise(self.topLevelOperator.InputImage.value, roi, vigra.defaultAxistags('xyzc'))

        predict = self.topLevelOperator.predict

        # predict.Classifier.setValue(self.classifier_factories[classifier_key])
        # predict.Image.setValue(self.topLevelOperator.InputImage.value)
        # predict.Labelscount.setValue(self.NumClasses)

        # output = predict.Output([]).wait()



