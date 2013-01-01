import os
from lazyflow.blockwiseFileset import BlockwiseFileset
from lazyflow.RESTfulVolumeDescription import parseRESTfulVolumeDescriptionFile
from lazyflow.roi import getIntersectingBlocks


class RESTfulBlockwiseFileset(BlockwiseFileset):
    
    def __init__(self, localDescriptionPath, remoteDescriptionPath):
        super( RESTfulBlockwiseFileset, self ).__init__( localDescriptionPath, 'r' )
        self.RESTfulDescription = parseRESTfulVolumeDescriptionFile( remoteDescriptionPath )

    def readData(self, roi, out_array=None):
        # Before reading the data, check each of the needed blocks and download them first
        block_starts = getIntersectingBlocks(self.description.block_shape, roi)

        missing_blocks = []
        for block_start in block_starts:
            if self.getBlockStatus(block_start) == BlockwiseFileset.BLOCK_NOT_AVAILABLE:
                missing_blocks.append( block_start )

        self._waitForBlocks( missing_blocks )
        
        return super( RESTfulBlockwiseFileset, self ).readData()

    def _waitForBlocks(self, missing_blocks):
        """
        Initiate downloads for those blocks that need it.
        (Some blocks in the list may already be downloading.)
        Then wait for all necessary downloads to complete (including the ones that we didn't initiate).
        """
        for block_start in missing_blocks:
            entire_block_roi = self.getEntireBlockRoi(block_start) # Roi of this whole block within the whole dataset
            roiString = "{}".format( (list(entire_block_roi[0]), list(entire_block_roi[1]) ) )
            datasetFilename = self.description.block_file_name_format.format( roiString=roiString )
            datasetDir = self.getDatasetDirectory( entire_block_roi[0] )
            datasetPath = os.path.join( datasetDir, datasetFilename )
            
            lockFilePath = datasetPath + ".lock"
            try:
                