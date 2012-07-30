from ilastik.ilastikshell.appletSerializer import AppletSerializer

class ThresholdMaskingSerializer(AppletSerializer):
    """
    Serializes the user's pixel feature selections to an ilastik v0.6 project file.
    """
    SerializerVersion = 0.1
    
    def __init__(self, mainOperator, projectFileGroupName):
        super( ThresholdMaskingSerializer, self ).__init__( projectFileGroupName, self.SerializerVersion )
        self.mainOperator = mainOperator
        self._dirty = False
        self.mainOperator.MinValue.notifyDirty( self.handleDirty )
        self.mainOperator.MaxValue.notifyDirty( self.handleDirty )
    
    def _serializeToHdf5(self, topGroup, hdf5File, projectFilePath):
        # Ensure the operator has input values before continuing
        if not self.mainOperator.MinValue.ready() \
        or not self.mainOperator.MaxValue.ready():
            return
    
        # Delete previous entries if they exist
        self.deleteIfPresent(topGroup, 'MinValue')
        self.deleteIfPresent(topGroup, 'MaxValue')
        
        # Store the new values
        topGroup.create_dataset('MinValue', data=self.mainOperator.MinValue.value)
        topGroup.create_dataset('MaxValue', data=self.mainOperator.MaxValue.value)
        self._dirty = False

    def _deserializeFromHdf5(self, topGroup, groupVersion, hdf5File, projectFilePath):
        minValue = topGroup['MinValue'][()]
        maxValue = topGroup['MaxValue'][()]
        
        self.mainOperator.MinValue.setValue( minValue )
        self.mainOperator.MaxValue.setValue( maxValue )
        self._dirty = False

    def isDirty(self):
        return self._dirty

    def handleDirty(self, slot, roi):
        self._dirty = True

    def unload(self):
        self.mainOperator.MinValue.disconnect()
        self.mainOperator.MaxValue.disconnect()

