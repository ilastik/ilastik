#Python
import os
import logging
logger = logging.getLogger(__name__)
traceLogger = logging.getLogger('TRACE.' + __name__)

#PyQt
from PyQt4.QtGui import *
from PyQt4 import uic

#lazyflow
from lazyflow.utility import Tracer

#ilastik
from ilastik.shell.gui.iconMgr import ilastikIcons
from ilastik.utility.gui import ThreadRouter, threadRouted
from preprocessingViewerGui import PreprocessingViewerGui

class PreprocessingGui(QMainWindow):
    def __init__(self, topLevelOperatorView):
        super(PreprocessingGui,self).__init__()
        
        self.drawer = None
        self.threadRouter = ThreadRouter(self)
        self.guiMode = 1
        self.topLevelOperatorView = topLevelOperatorView
        self.initAppletDrawerUic()
        self.centralGui = PreprocessingViewerGui(self.topLevelOperatorView)
        
    def initAppletDrawerUic(self):
        """
        Load the ui file for the applet drawer, which we own.
        """
        with Tracer(traceLogger):
            # Load the ui file (find it in our own directory)
            localDir = os.path.split(__file__)[0]+'/'
            # (We don't pass self here because we keep the drawer ui in a separate object.)
            self.drawer = uic.loadUi(localDir+"/preprocessingDrawer.ui")
            
            # Set up radiobox layout
            self.filterbuttons = [self.drawer.filter1,
                                    self.drawer.filter2,
                                    self.drawer.filter3,
                                    self.drawer.filter4,
                                    self.drawer.filter5]
            
            self.filterbuttons[self.topLevelOperatorView.Filter.value].setChecked(True)
            self.correspondingSigmaMins = [0.9,0.9,0.6,-float("infinity"),-float("infinity")]
            
            # Set up our handlers
            for f in self.filterbuttons:
                f.clicked.connect(self.handleFilterChanged)
            
            self.drawer.runButton.clicked.connect(self.handleRunButtonClicked)
            self.drawer.runButton.setIcon( QIcon(ilastikIcons.Play) )
            
            self.drawer.sigmaSpin.setValue(self.topLevelOperatorView.Sigma.value)
            self.drawer.sigmaSpin.valueChanged.connect(self.handleSigmaValueChanged)
            
            self.drawer.resetButton.clicked.connect(self.topLevelOperatorView.reset)
            self.drawer.writeprotectBox.stateChanged.connect(self.handleWriterprotectStateChanged)
    
    def handleFilterChanged(self):
        choice =  [f.isChecked() for f in self.filterbuttons].index(True)
        self.topLevelOperatorView.Filter.setValue(choice)
        
        #update lower bound for sigma
        self.drawer.sigmaSpin.setMinimum(self.correspondingSigmaMins[choice])
    
    def handleSigmaValueChanged(self):
        self.topLevelOperatorView.Sigma.setValue(self.drawer.sigmaSpin.value())
    
    @threadRouted 
    def onFailed(self, exception, exc_info):
        import traceback
        traceback.print_tb(exc_info[2])
        QMessageBox.critical(self, "error", str(exception))
    
    def handleRunButtonClicked(self):
        self.setWriteprotect()
        r = self.topLevelOperatorView.PreprocessedData[:]
        r.notify_failed(self.onFailed)
        r.submit()
        
    def handleWriterprotectStateChanged(self):
        iswriteprotect = self.drawer.writeprotectBox.checkState()
        for f in self.filterbuttons:
            f.setEnabled(not iswriteprotect)
        self.drawer.sigmaSpin.setEnabled(not iswriteprotect)
        self.drawer.runButton.setEnabled(not iswriteprotect)
    
    def setWriteprotect(self):
        self.drawer.writeprotectBox.setChecked(True)
    
    def setFilter(self,s,propagate = False):
        self.filterbuttons[s].setChecked(True)
        self.handleFilterChanged()
    
    def setSigma(self,sigma):
        self.drawer.sigmaSpin.setValue(sigma)
    
    def enableReset(self,er):
        self.drawer.resetButton.setEnabled(er)
    
    def centralWidget( self ):
        return self.centralGui
    
    def appletDrawer( self ):
        return self.drawer
        
    def menus( self ):
        return []
        
    def viewerControlWidget(self):
        return QWidget()
    
    def setImageIndex(self,imageIndex):
        pass
    def imageLaneAdded(self,imageIndex):
        pass
    def imageLaneRemoved(self,laneIndex,finalLength):
        pass
    def stopAndCleanUp(self):
        self.centralGui.stopAndCleanUp()
        
        
        
