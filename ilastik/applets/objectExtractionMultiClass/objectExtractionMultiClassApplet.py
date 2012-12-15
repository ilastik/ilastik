from ilastik.applets.base.applet import Applet

from lazyflow.graph import OperatorWrapper
from ilastik.applets.objectExtractionMultiClass.opObjectExtractionMultiClass import OpObjectExtractionMultiClass
from ilastik.applets.objectExtractionMultiClass.objectExtractionMultiClassSerializer import ObjectExtractionMultiClassSerializer

class ObjectExtractionMultiClassApplet( Applet ):
    def __init__( self, graph, guiName="Object Extraction", projectFileGroupName="ObjectExtraction" ):
        super(ObjectExtractionMultiClassApplet, self).__init__( guiName )
        self._topLevelOperator = OperatorWrapper(OpObjectExtractionMultiClass, graph=graph)        

        self._gui = None
        
        self._serializableItems = [ ObjectExtractionMultiClassSerializer(self._topLevelOperator, projectFileGroupName) ]

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
        if self._gui is None:
            from ilastik.applets.objectExtractionMultiClass.objectExtractionMultiClassGui import ObjectExtractionMultiClassGui            
            self._gui = ObjectExtractionMultiClassGui(self._topLevelOperator)        
        return self._gui
