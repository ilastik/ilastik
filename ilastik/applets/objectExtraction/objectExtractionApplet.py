from ilastik.applets.base.applet import Applet

from opObjectExtraction import OpObjectExtraction
from objectExtractionGui import ObjectExtractionGui
from objectExtractionSerializer import ObjectExtractionSerializer

from lazyflow.graph import OperatorWrapper

class ObjectExtractionApplet( Applet ):
    def __init__( self, graph, guiName="Object Extraction", projectFileGroupName="ObjectExtraction" ):
        super(ObjectExtractionApplet, self).__init__( guiName )
        self._topLevelOperator = OperatorWrapper(OpObjectExtraction, graph=graph)

        self._gui = ObjectExtractionGui(self._topLevelOperator)
        
        self._serializableItems = [ ObjectExtractionSerializer(self._topLevelOperator, projectFileGroupName) ]

    @property
    def topLevelOperator(self):
        return self._topLevelOperator

    @property
    def dataSerializers(self):
        return self._serializableItems

    @property
    def viewerControlWidget(self):
        return self._centralWidget.viewerControlWidget

    @property
    def gui(self):
        return self._gui
