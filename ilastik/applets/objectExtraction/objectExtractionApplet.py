from ilastik.applets.base.standardApplet import StandardApplet
from ilastik.applets.base.applet import ControlCommand
from ilastik.applets.objectExtraction.opObjectExtraction import OpObjectExtraction
from ilastik.applets.objectExtraction.objectExtractionSerializer import ObjectExtractionSerializer

class ObjectExtractionApplet( StandardApplet ):
    
    _downstreamEnabled = True

    def __init__( self, name="Object Extraction", workflow=None, projectFileGroupName="ObjectExtraction" ):
        super(ObjectExtractionApplet, self).__init__( name=name, workflow=workflow )
        self._serializableItems = [ ObjectExtractionSerializer(self.topLevelOperator, projectFileGroupName) ]

    @property
    def singleLaneOperatorClass( self ):
        return OpObjectExtraction

    @property
    def broadcastingSlots( self ):
        return []

    @property
    def singleLaneGuiClass( self ):
        from ilastik.applets.objectExtraction.objectExtractionGui import ObjectExtractionGui
        return ObjectExtractionGui

    @property
    def dataSerializers(self):
        return self._serializableItems

    def enableDownstream(self, enable=True):
        if self._downstreamEnabled and not enable: # we have to emit a disable signal
            self._downstreamEnabled = False
            self.guiControlSignal.emit(ControlCommand.DisableDownstream)
        if not self._downstreamEnabled and enable: # we have to take back our disable signal
            self._downstreamEnabled = True
            self.guiControlSignal.emit(ControlCommand.Pop)

    
