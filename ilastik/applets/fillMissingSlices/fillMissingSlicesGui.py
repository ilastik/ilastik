from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui

import os.path

from PyQt4.QtGui import QWidget, QProgressDialog, \
    QMessageBox, QFileDialog
from PyQt4 import uic
from PyQt4.QtCore import Qt, QString, QVariant, pyqtSignal, QObject, QDir

import logging
from lazyflow.operators.opInterpMissingData import logger as remoteLogger

from vigra.impex import readHDF5

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
        self._drawer.loadHistogramsButton.pressed.connect(self._loadHistogramsButtonPressed)
        self._drawer.exportDetectorButton.pressed.connect(self._exportDetectorButtonPressed)
        self._drawer.trainButton.pressed.connect(self._trainButtonPressed)
        
    def _loadDetectorButtonPressed(self):
        fname = QFileDialog.getOpenFileName(self, caption='Open Detector File', 
                                            filter="Pickled Objects (*.pkl);;All Files (*)",
                                            directory=QDir.homePath(),
                                            )
        if len(fname)>0: #not cancelled
            with open(fname, 'r') as f:
                pkl = f.read()
            
            self.topLevelOperatorView.OverloadDetector.setValue(pkl)
            logger.debug("Loaded detectors from file '{}'".format(fname))
    
    def _loadHistogramsButtonPressed(self):
        fname = QFileDialog.getOpenFileName(self, caption='Open Histogram File', 
                                            filter="HDF5 Files (*.h5 *.hdf5);;All Files (*)",
                                            directory=QDir.homePath(),
                                            )
        if len(fname)>0: #not cancelled
            #FIXME where do we get the real h5 path form???
            h5path = 'volume/data'
            
            # no try-catch because we want to propagate errors to the GUI
            histos = readHDF5(str(fname), h5path)
            
            self.topLevelOperatorView.setPrecomputedHistograms(histos)
            logger.debug("Loaded histograms from file '{}' (shape: {})".format(fname, histos.shape))
            
    def _exportDetectorButtonPressed(self):
        fname = QFileDialog.getSaveFileName(self, caption='Export Trained Detector', 
                                            filter="Pickled Objects (*.pkl);;All Files (*)",
                                            directory=QDir.homePath(),
                                            )
        if len(fname)>0: #not cancelled
            with open(fname, 'w') as f:
                f.write(self.topLevelOperatorView.Detector[:].wait())
            
            
            logger.debug("Exported detectors to file '{}'".format(fname))
            
    def _trainButtonPressed(self):
        self.topLevelOperatorView.train()
            