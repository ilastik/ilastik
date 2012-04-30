from ilastikshell.applet import Applet
from projectMetadataSerializer import ProjectMetadataSerializer, Ilastik05ProjectMetadataDeserializer
from projectMetadataGui import ProjectMetadataGui
from projectMetadata import ProjectMetadata

from PyQt4.QtGui import QMenuBar

class ProjectMetadataApplet( Applet ):
    """
    Implements the pixel classification "applet", which allows the ilastik shell to use it.
    """
    def __init__( self ):
        Applet.__init__( self, "Input Data Selection" )
        
        self._projectMetadata = ProjectMetadata()
        self._centralWidget = ProjectMetadataGui(self._projectMetadata)

        # No menu items for this applet, just give an empty menu
        self._menuWidget = QMenuBar()
        
        # For now, the central widget owns the applet bar gui
        self._drawers = [ ( "Project Metadata", self._centralWidget.getAppletDrawerUi() ) ]

        # No serializable items for now ...
        self._serializableItems = [ Ilastik05ProjectMetadataDeserializer(self._projectMetadata) ]

    @property
    def centralWidget( self ):
        return self._centralWidget

    @property
    def appletDrawers(self):
        return self._drawers
    
    @property
    def menuWidget( self ):
        return self._menuWidget

    @property
    def dataSerializers(self):
        return self._serializableItems
