###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
#		   http://ilastik.org/license.html
###############################################################################
import os
import logging
logger = logging.getLogger(__name__)

from PyQt4 import uic
from PyQt4.QtGui import QWidget

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

    def allowLaneSelectionChange(self):
        return False

    ###########################################
    ###########################################
    
    def __init__(self, projectMetadata):
        QWidget.__init__(self)
        
        self._projectMetadata = projectMetadata
        
        self.initMainUi()
        self.initAppletDrawerUi()
        
    def initMainUi(self):
        # Load the ui file (find it in our own directory)
        localDir = os.path.split(__file__)[0]
        uic.loadUi(localDir+"/centralWidget.ui", self)
        
        # Handle changes to the project widget
        def handleProjectNameWidgetChanged(newText):
            self._projectMetadata.projectName = newText
        self.projectNameEdit.textChanged.connect( handleProjectNameWidgetChanged )

        # Handle changes to the labeler widget
        def handleLabelerWidgetChanged(newText):
            self._projectMetadata.labeler = newText
        self.labelerEdit.textChanged.connect( handleLabelerWidgetChanged )

        # Handle changes to the description widget
        def handleDescriptionWidgetChanged():
            self._projectMetadata.description = self.descriptionEdit.toPlainText()
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
        # Load the ui file (find it in our own directory)
        localDir = os.path.split(__file__)[0]
        self._drawer = uic.loadUi(localDir+"/drawer.ui")
                
    def getAppletDrawerUi(self):
        return self._drawer









