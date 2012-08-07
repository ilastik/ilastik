from ilastik.applets.base.appletSerializer import AppletSerializer
import vigra

class TrackingSerializer(AppletSerializer):
    """
    Serializes the user's pixel feature selections to an ilastik v0.6 project file.
    """
    SerializerVersion = 0.1
    
    def __init__(self, mainOperator, projectFileGroupName):
        super( TrackingSerializer, self ).__init__( projectFileGroupName, self.SerializerVersion )
        self.mainOperator = mainOperator
        self._dirty = False
        # self.mainOperator.MinValue.notifyDirty( self.handleDirty )
        # self.mainOperator.MaxValue.notifyDirty( self.handleDirty )
    
    def _serializeToHdf5(self, topGroup, hdf5File, projectFilePath):
        print "tracking: serializeToHdf5", topGroup, hdf5File, projectFilePath
        # # Ensure the operator has input values before continuing
        # if not self.mainOperator.MinValue.ready() \
        # or not self.mainOperator.MaxValue.ready():
        #     return
    
        # # Delete previous entries if they exist
        # self.deleteIfPresent(topGroup, 'MinValue')
        # self.deleteIfPresent(topGroup, 'MaxValue')
        
        # # Store the new values
        # topGroup.create_dataset('MinValue', data=self.mainOperator.MinValue.value)
        # topGroup.create_dataset('MaxValue', data=self.mainOperator.MaxValue.value)
        self._dirty = False

    def _deserializeFromHdf5(self, topGroup, groupVersion, hdf5File, projectFilePath):
        print "tracking: deserializeFromHdf5", topGroup, groupVersion, hdf5File, projectFilePath
        if topGroup is None: # new project
             return

        import h5py

        #with h5py.File('/home/bkausler/src/ilastik/tracking/relabeled-stack/raw.h5', 'r') as f:
        #    raw = f['raw.h5'][0:3,...]

        with h5py.File('/home/bkausler/src/ilastik/tracking/relabeled-stack/labeledtracking.h5', 'r') as f:
            tracked = f['labeledtracking'][0:3,...]
        print tracked.shape, tracked.dtype

        # tracked = tracked.view(vigra.VigraArray)
        # tracked.axistags=vigra.AxisTags(
        #         vigra.AxisInfo('t', vigra.AxisType.Time),
        #         vigra.AxisInfo('x', vigra.AxisType.Space),
        #         vigra.AxisInfo('y', vigra.AxisType.Space),
        #         vigra.AxisInfo('z', vigra.AxisType.Space),
        #         vigra.AxisInfo('c', vigra.AxisType.Channels))

        #raw = raw.view(vigra.VigraArray)
        #raw.axistags=vigra.AxisTags(
        #        vigra.AxisInfo('t', vigra.AxisType.Time),
        #        vigra.AxisInfo('x', vigra.AxisType.Space),
        #        vigra.AxisInfo('y', vigra.AxisType.Space),
        #        vigra.AxisInfo('z', vigra.AxisType.Space),
        #        vigra.AxisInfo('c', vigra.AxisType.Channels))


        print "vigraarray" ,tracked.dtype
        #self.mainOperator.RawData.setValue( raw, check_changed=False )
        #self.mainOperator.Output.setValue( tracked, check_changed=False )
        # minValue = topGroup['MinValue'][()]
        # maxValue = topGroup['MaxValue'][()]
        
        # self.mainOperator.MinValue.setValue( minValue )
        # self.mainOperator.MaxValue.setValue( maxValue )
        self._dirty = False

    def isDirty(self):
        return True
        return self._dirty

    def handleDirty(self, slot, roi):
        self._dirty = True

    def unload(self):
        pass
        # self.mainOperator.MinValue.disconnect()
        # self.mainOperator.MaxValue.disconnect()

