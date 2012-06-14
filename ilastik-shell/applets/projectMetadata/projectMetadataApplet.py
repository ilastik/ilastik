from ilastikshell.applet import Applet
from projectMetadataSerializer import ProjectMetadataSerializer, Ilastik05ProjectMetadataDeserializer
from projectMetadataGui import ProjectMetadataGui
from projectMetadata import ProjectMetadata

class ProjectMetadataApplet( Applet ):
    """
    This applet allows the user to enter project metadata (e.g. Project name, labeler name, etc.)
    """
    def __init__( self ):
        Applet.__init__( self, "Project Metadata" )
        
        self._projectMetadata = ProjectMetadata()
        self._gui = ProjectMetadataGui(self._projectMetadata)
        self._serializableItems = [ ProjectMetadataSerializer(self._projectMetadata),
                                    Ilastik05ProjectMetadataDeserializer(self._projectMetadata) ]

    @property
    def dataSerializers(self):
        return self._serializableItems

    @property
    def gui(self):
        return self._gui

    @property
    def topLevelOperator(self):
        # This applet provides a GUI and serializers, but does not affect the graph in any way.
        return None




