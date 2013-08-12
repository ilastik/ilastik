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
    
    _standardPatchSizes = [1,2,4,8] + [16*i for i in range(1,6)]
    _standardHaloSizes = [8*i for i in range(7)]
    
    def initAppletDrawerUi(self):
        """
        
        """
        # Load the ui file (find it in our own directory)
        localDir = os.path.split(__file__)[0]
        self._drawer = uic.loadUi(localDir+"/drawer.ui")
        
        self._drawer.loadDetectorButton.clicked.connect(self._loadDetectorButtonPressed)
        self._drawer.loadHistogramsButton.clicked.connect(self._loadHistogramsButtonPressed)
        self._drawer.exportDetectorButton.clicked.connect(self._exportDetectorButtonPressed)
        self._drawer.trainButton.clicked.connect(self._trainButtonPressed)
        
        self._drawer.patchSizeComboBox.activated.connect(self._patchSizeComboBoxActivated)
        for s in self._standardPatchSizes:
            self._drawer.patchSizeComboBox.addItem(str(s))
        
        self._drawer.haloSizeComboBox.activated.connect(self._haloSizeComboBoxActivated)
        for s in self._standardHaloSizes:
            self._drawer.haloSizeComboBox.addItem(str(s))
            
        self._setInitialComboBoxValues()
        
        
    def _loadDetectorButtonPressed(self):
        fname = QFileDialog.getOpenFileName(self, caption='Open Detector File', 
                                            filter="Pickled Objects (*.pkl);;All Files (*)",
                                            directory=QDir.homePath(),
                                            )
        if len(fname)>0: #not cancelled
            with open(fname, 'r') as f:
                pkl = f.read()
            
            # reset it first
            self.topLevelOperatorView.OverloadDetector.setValue('')
            
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
        
    def _patchSizeComboBoxActivated(self, i):
        desiredPatchSize = self._standardPatchSizes[i]
        self.topLevelOperatorView.PatchSize.setValue(desiredPatchSize)
        
    def _haloSizeComboBoxActivated(self, i):
        desiredHaloSize = self._standardHaloSizes[i]
        self.topLevelOperatorView.HaloSize.setValue(desiredHaloSize)
        
    def _setInitialComboBoxValues(self):
        patchSize = self.topLevelOperatorView.PatchSize.value
        haloSize = self.topLevelOperatorView.HaloSize.value
        
        index = -1
        for i in range(len(self._standardPatchSizes)):
            if patchSize==self._standardPatchSizes[i]:
                index = i
        self._patchSizeComboBoxActivated(0 if index < -1 else index)
        
        index = -1
        for i in range(len(self._standardHaloSizes)):
            if haloSize==self._standardHaloSizes[i]:
                index = i
        self._haloSizeComboBoxActivated(0 if index < -1 else index)
        
        
        
        
        
        
        
        
