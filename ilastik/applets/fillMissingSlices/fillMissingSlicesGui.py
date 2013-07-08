from ilastik.applets.layerViewer import LayerViewerGui

import os.path

from PyQt4.QtGui import QWidget, QProgressDialog, \
    QMessageBox, QFileDialog
from PyQt4 import uic
from PyQt4.QtCore import Qt, QString, QVariant, pyqtSignal, QObject, QDir

import logging
from lazyflow.operators.opInterpMissingData import logger as remoteLogger

remoteLogger.setLevel(logging.DEBUG)
loggerName = __name__ 
logger = logging.getLogger(loggerName)
logger.setLevel(logging.DEBUG)


class FillMissingSlicesGui(LayerViewerGui):
    
    def initAppletDrawerUi(self):
        """
        
        """
        # Load the ui file (find it in our own directory)
        localDir = os.path.split(__file__)[0]
        self._drawer = uic.loadUi(localDir+"/drawer.ui")
        
        self._drawer.loadDetectorButton.pressed.connect(self._loadDetectorButtonPressed)
        
    def _loadDetectorButtonPressed(self):
        fname = QFileDialog.getOpenFileName(self, caption='Open Detector File', 
                                            #filter="Pickled Objects (*.pkl);;All Files (*)",
                                            directory=QDir.homePath(),
                                            )
        if len(fname)>0: #not cancelled
            with open(fname, 'r') as f:
                pkl = f.read()
            
            self.topLevelOperatorView.loads(pkl)
            logger.debug("Loaded detector from file '{}'".format(fname))