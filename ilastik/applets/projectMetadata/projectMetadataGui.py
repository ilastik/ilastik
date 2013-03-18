from PyQt4.QtGui import *

from PyQt4 import uic
import os

import logging
logger = logging.getLogger(__name__)
traceLogger = logging.getLogger('TRACE.' + __name__)
from lazyflow.utility import Tracer

class ProjectMetadataGui( QWidget ):
    """
    """
    ###########################################
    ### AppletGuiInterface Concrete Methods ###
    ###########################################
    
    def centralWidget( self ):
        return self

    def appletDrawer(self):
        return self.getAppletDrawerUi()

    def menus( self ):
        return []

    def viewerControlWidget(self):
        return QWidget() # No viewer controls for this applet.

    def setImageIndex(self, index):
        pass # This applet does't deal with images.
    
    def stopAndCleanUp(self):
        pass

    def imageLaneAdded(self, laneIndex):
        pass

    def imageLaneRemoved(self, laneIndex, finalLength):
        pass

    ###########################################
    ###########################################
    
    def __init__(self, projectMetadata):
        QWidget.__init__(self)
        
        self._projectMetadata = projectMetadata
        
        self.initMainUi()
        self.initAppletDrawerUi()
        
    def initMainUi(self):
        with Tracer(traceLogger):
            # Load the ui file (find it in our own directory)
            localDir = os.path.split(__file__)[0]
            uic.loadUi(localDir+"/centralWidget.ui", self)
            
            # Handle changes to the project widget
            def handleProjectNameWidgetChanged(newText):
                self._projectMetadata.projectName = str(newText)
            self.projectNameEdit.textChanged.connect( handleProjectNameWidgetChanged )
    
            # Handle changes to the labeler widget
            def handleLabelerWidgetChanged(newText):
                self._projectMetadata.labeler = str(newText)
            self.labelerEdit.textChanged.connect( handleLabelerWidgetChanged )
    
            # Handle changes to the description widget
            def handleDescriptionWidgetChanged():
                self._projectMetadata.description = str(self.descriptionEdit.toPlainText())
            self.descriptionEdit.textChanged.connect( handleDescriptionWidgetChanged )
    
            # Update the GUI with new values if someone else modifies our metadata externally
            def handleMetadataChanged():
                if self.projectNameEdit.text() != self._projectMetadata.projectName:
                    self.projectNameEdit.setText( self._projectMetadata.projectName )
                if self.labelerEdit.text() != self._projectMetadata.labeler:
                    self.labelerEdit.setText( self._projectMetadata.labeler )
                if self.descriptionEdit.toPlainText() != self._projectMetadata.description:
                    self.descriptionEdit.setText( self._projectMetadata.description )
            self._projectMetadata.changedSignal.connect(handleMetadataChanged)
                
        
    def initAppletDrawerUi(self):
        with Tracer(traceLogger):
            # Load the ui file (find it in our own directory)
            localDir = os.path.split(__file__)[0]
            self._drawer = uic.loadUi(localDir+"/drawer.ui")
                
    def getAppletDrawerUi(self):
        return self._drawer









