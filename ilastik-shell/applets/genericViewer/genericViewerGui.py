from PyQt4.QtCore import pyqtSignal, QTimer, QRectF, Qt, SIGNAL, QObject
from PyQt4.QtGui import *

from shellwidgets.viewerAppletGuiBase import ViewerAppletGuiBase

from PyQt4 import uic
import os

class GenericViewerGui( ViewerAppletGuiBase ):
    """
    The central widget of the Input Data Selection Applet.
    Provides controls for adding/removing input data images and stacks.
    """
    def __init__(self, mainOperator):
        super( GenericViewerGui, self ).__init__(mainOperator.OutputLayers)
        
        #self.initAppletDrawerUi()
        self.mainOperator = mainOperator
        
    def initMainUi(self):
        # Load the ui file (find it in our own directory)
        localDir = os.path.split(__file__)[0]
        uic.loadUi(localDir+"/centralWidget.ui", self)
        
#    def initAppletDrawerUi(self):
#        # Load the ui file (find it in our own directory)
#        localDir = os.path.split(__file__)[0]
#        self._drawer = uic.loadUi(localDir+"/drawer.ui")
#        
#        def enableDrawerControls(enabled):
#            pass
#        # Expose the enable function with the name the shell expects
#        self._drawer.enableControls = enableDrawerControls
    
    def getAppletDrawerUi(self):
        return self._drawer
        
    def enableControls(self, enabled):
        """
        Enable or disable all of the controls in this applet's central widget.
        """
        # All the controls in our GUI
        controlList = [  ]

        # Enable/disable all of them
        for control in controlList:
            control.setEnabled(enabled)








