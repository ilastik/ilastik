from ilastik.applets.base.applet import Applet
#from labelingSerializer import LabelingSerializer

class PixelClassificationApplet( Applet ):
    """
    Implements the pixel classification "applet", which allows the ilastik shell to use it.
    """
    def __init__( self, graph, projectFileGroupName ):
        Applet.__init__( self, "Generic Labeling" )

        self._topLevelOperator = None

        self._serializableItems = []
#        # We provide two independent serializing objects:
#        #  one for the current scheme and one for importing old projects.
#        self._serializableItems = [PixelClassificationSerializer(self._topLevelOperator, projectFileGroupName), # Default serializer for new projects
#                                   Ilastik05ImportDeserializer(self._topLevelOperator)]   # Legacy (v0.5) importer

        self._gui = None
            
    @property
    def topLevelOperator(self):
        return self._topLevelOperator

    @property
    def dataSerializers(self):
        return self._serializableItems

    @property
    def gui(self):
        if self._gui is None:
            from labelingGui import LabelingGui
            self._gui = LabelingGui( self._topLevelOperator, self.guiControlSignal )        
        return self._gui
