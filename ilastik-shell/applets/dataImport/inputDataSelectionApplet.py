from ilastikshell.applet import Applet
import utility

from PyQt4.QtCore import pyqtSignal, QTimer, QRectF, Qt, SIGNAL, QObject
from PyQt4.QtGui import *

from PyQt4 import uic
import os

from utility.simpleSignal import SimpleSignal

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
        

class ProjectAttributes(object):
    """
    Simple struct-like class for storing basic project attributes.
    """
    def __init__(self):
        self.projectName = ""
        self.labeler = ""
        self.description = ""
    
    def __eq__(self, other):
        eq = True
        eq &= (self.projectName == other.projectName)
        eq &= (self.labeler == other.labeler)
        eq &= (self.description == other.description)

class ProjectInfo(object):
    """
    Stores project info.  Uses 'simple signals' to notify views of any updates.
    """
    def __init__(self):
        self._projectAttributes = ProjectAttributes()
        self.projectAttributesChangedSignal = SimpleSignal()

        self._dataSetInfos = []
        self.dataSetsChangedSignal = SimpleSignal()
    
    @property
    def projectAttributes(self):
        """
        Access the project attribute fields.
        Note: Do not modify the attributes directly.
              Assign new attributes via the setter fn (below).
        """
        return self._projectAttributes
    
    @projectAttributes.setter
    def projectAttributes(self, newProjectAttributes):
        self._projectAttributes = newProjectAttributes
        self.projectAttributesChangedSignal.emit()
        
    @property
    def dataSetInfos(self):
        """
        Provide access to the list of datasets.
        Note: Do not modify this list or its elements.
              Assign new values via the setter fn (below).
        """
        return self._dataSetInfos
    
    @dataSetInfos.setter
    def dataSetInfos(self, newInfos):
        self._dataSetInfos = newInfos
        self.dataSetsChangedSignal.emit()

class InputDataSelectionGui( QWidget ):
    """
    The central widget of the Input Data Selection Applet.
    Provides controls for adding/removing input data images and stacks.
    """
    def __init__(self, projectInfo):
        QWidget.__init__(self)
        
        self.projectOpenAction = None
        self.projectSaveAction = None
        
        self._projectInfo = projectInfo
        self._projectInfo.projectAttributesChangedSignal.connect(self.handleProjectAttributesChangedExternally)
        self._projectInfo.dataSetsChangedSignal.connect(self.handleDataSetsChangedExternally)
        
        self.initMainUi()
        self.initAppletBarUi()
            
    def initMainUi(self):
        p = utility.getPathToLocalDirectory(__file__)
        uic.loadUi(p+"/inputDataSelection.ui", self)
        
    def initAppletBarUi(self):
        p = utility.getPathToLocalDirectory(__file__)
        self._appletBarUi = uic.loadUi(p+"/inputDataSelectionAppletBar.ui")
    
    def getAppletBarUi(self):
        return self._appletBarUi
    
    def handleDataSetsChangedExternally(self):
        # Show the new dataset info in the GUI
        pass
    
    def handleProjectAttributesChangedExternally(self):
        # Show the new project attributes
        self.projectNameEdit.setText(self._projectInfo.projectAttributes.projectName)
        self.labelerEdit.setText(self._projectInfo.projectAttributes.labeler)
        self.descriptionEdit.setText(self._projectInfo.projectAttributes.description)

    def acceptShellActions(self, shellActions):
        """
        Connect appropriate GUI elements to shell actions.
        """
        self._appletBarUi.openProjectButton.clicked.connect(shellActions.openProjectAction.trigger)
        self._appletBarUi.saveProjectButton.clicked.connect(shellActions.saveProjectAction.trigger)

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
    """
    Imports the project metadata (e.g. project name) from an v0.5 .ilp file.
    """
    def __init__(self, projectInfo):
        self.projectInfo = projectInfo
    
    def serializeToHdf5(self, hdf5Group):
        pass
    
    def deserializeFromHdf5(self, hdf5File):
        projectAttributes = ProjectAttributes()

        # Read in what values we can, without failing if any of them are missing
        try:
            projectAttributes.labeler = hdf5File["Project/Labeler"].value
        except KeyError:
            pass

        try:
            projectAttributes.projectName = hdf5File["Project/Name"].value
        except KeyError:
            pass
            
        try:
            projectAttributes.description = hdf5File["Project/Description"].value
        except KeyError:
            pass
        
        # Now give the values to the project info
        self.projectInfo.projectAttributes = projectAttributes

    def isDirty(self):
        """
        For now, this class is import-only.
        We always report our data as "clean" because we have nothing to write.
        """
        return False

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
        Applet.__init__( self, "Input Data Selection" )
        
        self._projectInfo = ProjectInfo()
        self._centralWidget = InputDataSelectionGui(self._projectInfo)

        # No menu items for this applet, just give an empty menu
        self._menuWidget = QMenuBar()
        
        # For now, the central widget owns the applet bar gui
        self._controlWidgets = [ ( "Project Data", self._centralWidget.getAppletBarUi() ) ]

        # No serializable items for now ...
        self._serializableItems = [ Ilastik05ProjectInfoImportDeserializer(self._projectInfo) ]
    
    @property
    def centralWidget( self ):
        return self._centralWidget

    @property
    def appletDrawers(self):
        return self._controlWidgets
    
    @property
    def menuWidget( self ):
        return self._menuWidget

    @property
    def dataSerializers(self):
        return self._serializableItems

    def setShellActions(self, shellActions):
        """
        (See base class for details.)
        """ 
        self._centralWidget.acceptShellActions(shellActions)

