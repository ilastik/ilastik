from PyQt4.QtCore import pyqtSignal, QTimer, QRectF, Qt, SIGNAL, QObject
from PyQt4.QtGui import *

from PyQt4 import uic
import os

import logging
from ilastik.applets.tracking.trackingGuiNN import TrackingGuiNN
logger = logging.getLogger(__name__)
traceLogger = logging.getLogger('TRACE.' + __name__)
from lazyflow.tracer import Tracer

class TrackingTabsGui( QTabWidget ):
    """
    """
    ###########################################
    ### AppletGuiInterface Concrete Methods ###
    ###########################################
    
    def centralWidget( self ):
        return self

    def appletDrawers(self):
        return self.trackingGui.appletDrawers()

    def menus( self ):
        return []

    def viewerControlWidget(self):
#        return self.trackingGui.viewerControlWidget()
        if self.currentIndex() == 0:
            return self.trackingGui.viewerControlWidget()
        else:   
            return None # No viewer controls

    def setImageIndex(self, index):
        self.trackingGui.setImageIndex(index)        
    
    def reset(self):
        self.trackingGui.reset()

    ###########################################
    ###########################################
    
    def __init__(self, mainOperator):
        QWidget.__init__(self)
        
#        self._projectMetadata = projectMetadata
        self.mainOperator = mainOperator
        self.trackingGui = TrackingGuiNN(self.mainOperator)

        
        self.initMainUi()
#        self.initAppletDrawerUi()
        
        
    def initMainUi(self):
        with Tracer(traceLogger):
            # Load the ui file (find it in our own directory)
            localDir = os.path.split(__file__)[0]
            uic.loadUi(localDir+"/centralWidget.ui", self)

            self.lineageWidget = QWidget()
            self.label = QLabel('Lineage trees not yet computed')
            self.refreshButton = QPushButton('refresh')            
            vbox = QVBoxLayout()
            vbox.addWidget(self.label)
            vbox.addWidget(self.refreshButton)
            self.lineageWidget.setLayout(vbox)
            
            def onRefreshButtonPressed():
                if self.mainOperator[0].scene is None:
                    text = self.label.text()
                    self.label.setText(text + " ...still")
                else:                    
                    self.lineageWidget.setLayout(self.mainOperator[0].scene)                    
            self.refreshButton.pressed.connect(onRefreshButtonPressed)
            
            
            self.addTab(self.trackingGui.volumeEditorWidget, "Volume")            
            self.addTab(self.lineageWidget, "Lineage Trees")
            
            
#            def handleTabChanged():
#                if self.outputTabs.currentIndex == 0:
#                    do
#                if self.outputTabs.currentIndex == 1:
#                    do
#            self.outputTabs.tabChanged.connect (handleTabChanged)
            
                
        
#    def initAppletDrawerUi(self):
#        with Tracer(traceLogger):
#            # Load the ui file (find it in our own directory)
#            localDir = os.path.split(__file__)[0]
#            self._drawer = uic.loadUi(localDir+"/drawer.ui")
#                
#    def getAppletDrawerUi(self):
#        return self._drawer


    






