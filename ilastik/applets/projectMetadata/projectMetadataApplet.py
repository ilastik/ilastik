from ilastik.applets.base.applet import Applet
from projectMetadataSerializer import ProjectMetadataSerializer, Ilastik05ProjectMetadataDeserializer
from projectMetadata import ProjectMetadata

class ProjectMetadataApplet( Applet ):
    """
    This applet allows the user to enter project metadata (e.g. Project name, labeler name, etc.).
    
    Note that this applet does not affect the processing pipeline and has no top-level operator.
    """
    def __init__( self ):
        Applet.__init__( self, "Project Metadata" )
        
        self._projectMetadata = ProjectMetadata()

        self._gui = None # Created on first acess

        self._serializableItems = [ ProjectMetadataSerializer(self._projectMetadata, "ProjectMetadata"),
                                    Ilastik05ProjectMetadataDeserializer(self._projectMetadata) ]

    @property
    def dataSerializers(self):
        return self._serializableItems

    @property
    def gui(self):
        if self._gui is None:
            from projectMetadataGui import ProjectMetadataGui
            self._gui = ProjectMetadataGui(self._projectMetadata)
        return self._gui

    @property
    def topLevelOperator(self):
        # This applet provides a GUI and serializers, but does not affect the graph in any way.
        return None

    def addLane(self, laneIndex):
        """
        Add an image processing lane to the top-level operator.
        """
        pass

    def removeLane(self, laneIndex, finalLength):
        """
        Remove an image processing lane from the top-level operator.
        """
        pass


