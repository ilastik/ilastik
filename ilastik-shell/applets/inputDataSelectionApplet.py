from ilastikshell.applet import Applet

from PyQt4.QtCore import pyqtSignal, QTimer, QRectF, Qt, SIGNAL, QObject
from PyQt4.QtGui import *

from PyQt4 import uic
import os

from simpleSignal import SimpleSignal

class DataSetInfo(object):
    """
    Simple struct-like class for storing info about a dataset.
    """
    def __init__(self):
        self.dataSetName = ""
        self.labelNames = []
        self.fileNamesAndInfos = {} # dict of names to os.stat tuples
    
    def __eq__(self, other):
        eq = True
        eq &= (self.dataSetName == other.dataSetName)
        eq &= (self.labelNames == other.labelNames)
        eq &= (self.fileNamesAndInfos == other.fileNamesAndInfos)
        

class ProjectInfo(object):
    """
    Stores project info.  Uses 'simple signals' to notify views of any updates.
    """
    def __init__(self):
        self.projectName = ""
        self.labeler = ""
        self.description = ""
        self.dataSetInfos = []

        self.dataSetsChanged = SimpleSignal()
        self.projectAttributesChanged = SimpleSignal()

class InputDataSelectionGui( QWidget ):
    """
    The central widget of the Input Data Selection Applet.
    Provides controls for adding/removing input data images and stacks.
    """
    def __init__(self, projectInfo):
        QWidget.__init__(self)
        
        self._projectInfo = projectInfo
        self._projectInfo.projectAttributesChanged.connect(self.handleProjectAttributesChangedExternally)
        self._projectInfo.dataSetsChanged.connect(self.handleDataSetsChangedExternally)
        
        self.initMainUi()
        self.initAppletBarUi()
        
    def getPathToLocalDirectory(self):
        # Determines the path of this python file so we can refer to other files relative to it.
        p = os.path.split(__file__)[0]+'/'
        if p == "/":
            p = "."+p
        return p
    
    def initMainUi(self):
        p = self.getPathToLocalDirectory()
        uic.loadUi(p+"/inputDataSelection.ui", self)
        
    def initAppletBarUi(self):
        p = self.getPathToLocalDirectory()
        self._appletBarUi = uic.loadUi(p+"/inputDataSelectionAppletBar.ui")
    
    def getAppletBarUi(self):
        return self._appletBarUi
    
    def handleDataSetsChangedExternally(self):
        # Show the new dataset info in the GUI
        pass
    
    def handleProjectAttributesChangedExternally(self):
        # Show the new project attributes
        #self.
        pass

class ProjectInfoSerializer(object):
    def __init__(self):
        pass
    
    def serializeToHdf5(self, hdf5Group):
        pass
    
    def deserializeFromHdf5(self, hdf5Group):
        pass

    def isDirty(self):
        """ Return true if the current state of this item 
            (in memory) does not match the state of the HDF5 group on disk.
            SerializableItems are responsible for tracking their own dirty/notdirty state."""
        pass

    def unload(self):
        """ Called if either
            (1) the user closed the project or
            (2) the project opening process needs to be aborted for some reason
                (e.g. not all items could be deserialized properly due to a corrupted ilp)
            This way we can avoid invalid state due to a partially loaded project. """ 
        pass

class Ilastik05ProjectInfoImportDeserializer(object):
    def __init__(self, projectInfo):
        self.projectInfo = projectInfo
    
    def serializeToHdf5(self, hdf5Group):
        pass
    
    def deserializeFromHdf5(self, hdf5File):
        labeler = hdf5File["Project/Labeler"].value
        name = hdf5File["Project/Name"].value
        description = hdf5File["Project/Description"].value

    def isDirty(self):
        """ Return true if the current state of this item 
            (in memory) does not match the state of the HDF5 group on disk.
            SerializableItems are responsible for tracking their own dirty/notdirty state."""
        pass

    def unload(self):
        """ Called if either
            (1) the user closed the project or
            (2) the project opening process needs to be aborted for some reason
                (e.g. not all items could be deserialized properly due to a corrupted ilp)
            This way we can avoid invalid state due to a partially loaded project. """ 
        pass

class InputDataSelectionApplet( Applet ):
    """
    Implements the pixel classification "applet", which allows the ilastik shell to use it.
    """
    def __init__( self ):
        # (No need to call the base class constructor here.)
        # Applet.__init__( self )
        
        self._projectInfo = ProjectInfo()

        self.name = "Input Data Selection"
        self._centralWidget = InputDataSelectionGui(self._projectInfo)

        # No menu items for this applet, just give an empty menu
        self._menuWidget = QMenuBar()
        
        # For now, the central widget owns the applet bar gui
        self._controlWidgets = [ ( "Project Data", self._centralWidget.getAppletBarUi() ) ]

        # No serializable items for now ...
        self._serializableItems = [ Ilastik05ProjectInfoImportDeserializer(self._projectInfo) ]

