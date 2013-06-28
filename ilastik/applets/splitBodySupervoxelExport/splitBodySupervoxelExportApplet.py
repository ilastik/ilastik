from ilastik.applets.base.standardApplet import StandardApplet
from opSplitBodySupervoxelExport import OpSplitBodySupervoxelExport

class SplitBodySupervoxelExportApplet( StandardApplet ):
    def __init__( self, workflow ):
        super(SplitBodySupervoxelExportApplet, self).__init__("Split-body supervoxel export", workflow)

    @property
    def singleLaneOperatorClass(self):
        return OpSplitBodySupervoxelExport
    
    @property
    def singleLaneGuiClass(self):
        from splitBodySupervoxelExportGui import SplitBodySupervoxelExportGui
        return SplitBodySupervoxelExportGui

    @property
    def broadcastingSlots(self):
        return []
    
    @property
    def dataSerializers(self):
        return []
