import copy
import numpy
import vigra
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.roi import roiFromShape, roiToSlice, getIntersectingBlocks, getBlockBounds

from ilastik.workflows.carving.opCarving import OpCarving

import logging
logger = logging.getLogger(__name__)

class OpSplitBodyCarving( OpCarving ):

    RavelerLabels = InputSlot()
    CurrentRavelerLabel = InputSlot(value=0)

    AnnotationFilepath = InputSlot(optional=True, stype='filepath') # Included as a slot here for easy serialization
    
    CurrentRavelerObject = OutputSlot()
    CurrentRavelerObjectRemainder = OutputSlot()
    MaskedSegmentation = OutputSlot()
    CurrentFragmentSetLut = OutputSlot()

    BLOCK_SIZE = 520
    SEED_MARGIN = 10

    def __init__(self, *args, **kwargs):
        super( OpSplitBodyCarving, self ).__init__( *args, **kwargs )
        self._opSelectRavelerObject = OpSelectLabel( parent=self )
        self._opSelectRavelerObject.SelectedLabel.connect( self.CurrentRavelerLabel )
        self._opSelectRavelerObject.Input.connect( self.RavelerLabels )
        self.CurrentRavelerObject.connect( self._opSelectRavelerObject.Output )
        
        self._opFragmentSetLut = OpFragmentSetLut( parent=self )
        self._opFragmentSetLut.MST.connect( self.MST )
        self._opFragmentSetLut.RavelerLabel.connect( self.CurrentRavelerLabel )
        

    @classmethod
    def autoSeedBackground(cls, laneView, foreground_label):
        # Seed the entire image with background labels, except for the individual label in question
        # To save memory, we'll do this in blocks instead of all at once

        volume_shape = laneView.RavelerLabels.meta.shape
        volume_roi = roiFromShape( volume_shape )
        block_shape = (OpSplitBodyCarving.BLOCK_SIZE,) * len( volume_shape ) 
        block_shape = numpy.minimum( block_shape, volume_shape )
        block_starts = getIntersectingBlocks( block_shape, volume_roi )

        logger.debug("Auto-seeding {} blocks for label".format( len(block_starts), foreground_label ))
        for block_index, block_start in enumerate(block_starts):
            block_roi = getBlockBounds( volume_shape, block_shape, block_start )
            label_block = laneView.RavelerLabels(*block_roi).wait()
            background_block = numpy.where( label_block == foreground_label, 0, 1 )
            background_block = numpy.asarray( background_block, numpy.float32 ) # Distance transform requires float
            if (background_block == 0.0).any():
                # We need to leave a small border between the background seeds and the object membranes
                background_block_view = background_block.view( vigra.VigraArray )
                background_block_view.axistags = copy.copy( laneView.RavelerLabels.meta.axistags )
                
                background_block_view_4d = background_block_view.bindAxis('t', 0)
                background_block_view_3d = background_block_view_4d.bindAxis('c', 0)
                
                distance_transformed_block = vigra.filters.distanceTransform3D(background_block_view_3d, background=False)
                distance_transformed_block = distance_transformed_block.astype( numpy.uint8 )
                
                # Create a 'hull' surrounding the foreground, but leave some space.
                background_seed_block = (distance_transformed_block == OpSplitBodyCarving.SEED_MARGIN)
                background_seed_block = background_seed_block.astype(numpy.uint8) * 1 # (In carving, background is label 1)

#                # Make the hull VERY sparse to avoid over-biasing graph cut toward the background class
#                # FIXME: Don't regenerate this random block on every loop iteration
#                rand_bytes = numpy.random.randint(0, 1000, background_seed_block.shape)
#                background_seed_block = numpy.where( rand_bytes < 1, background_seed_block, 0 )
#                background_seed_block = background_seed_block.view(vigra.VigraArray)
#                background_seed_block.axistags = background_block_view_3d.axistags
                
                axisorder = laneView.RavelerLabels.meta.getTaggedShape().keys()
                
                logger.debug("Writing backgound seeds: {}/{}".format( block_index, len(block_starts) ))
                laneView.WriteSeeds[ roiToSlice( *block_roi ) ] = background_seed_block.withAxes(*axisorder)
            else:
                logger.debug("Skipping all-background block: {}/{}".format( block_index, len(block_starts) ))

    def setupOutputs(self):
        super( OpSplitBodyCarving, self ).setupOutputs()
        self.MaskedSegmentation.meta.assignFrom(self.Segmentation.meta)
        def handleDirtySegmentation(slot, roi):
            self.MaskedSegmentation.setDirty( roi )
        self.Segmentation.notifyDirty( handleDirtySegmentation )
        self.CurrentRavelerObjectRemainder.meta.assignFrom( self.RavelerLabels.meta )
            
    def execute(self, slot, subindex, roi, result):
        if slot == self.MaskedSegmentation:
            return self._executeMaskedSegmentation(roi, result)
        elif slot == self.CurrentRavelerObjectRemainder:
            return self._executeCurrentRavelerObjectRemainder(roi, result)
        else:
            return super( OpSplitBodyCarving, self ).execute( slot, subindex, roi, result )
    
    def _executeMaskedSegmentation(self, roi, result):
        result = self.Segmentation(roi.start, roi.stop).writeInto(result).wait()
        result[:] = numpy.array([0,0,1])[result] # Keep only the pixels whose value is '2' (the foreground)
        currentRemainder = self.CurrentRavelerObjectRemainder(roi.start, roi.stop).wait()
        numpy.logical_and( result, currentRemainder, out=result )
        result[:] *= 2 # In carving, background is always 1 and segmentation pixels are always 2
        return result

    def _executeCurrentRavelerObjectRemainder(self, roi, result):        
        # Start with the original raveler object
        self.CurrentRavelerObject(roi.start, roi.stop).writeInto(result).wait()

        lut = self._opFragmentSetLut.Lut[:].wait()

        # Save memory: Implement (A - B) == (A & ~B), and do it with in-place operations
        slicing = roiToSlice( roi.start[1:4], roi.stop[1:4] )
        a = result[0,...,0]
        b = lut[self._mst.regionVol[slicing]]
        numpy.logical_not( b, out=b ) # ~B
        numpy.logical_and(a, b, out=a) # A & ~B
        
        return result
    
    def propagateDirty(self, slot, subindex, roi):
        if slot == self.RavelerLabels:
            self.MaskedSegmentation.setDirty( roi.start, roi.stop )
        elif slot == self.CurrentRavelerLabel:
            self.MaskedSegmentation.setDirty( slice(None) )
        elif slot == self.AnnotationFilepath:
            return
        else:
            super( OpSplitBodyCarving, self ).propagateDirty( slot, subindex, roi )        
    
    def getSavedObjectNamesForRavelerLabel(self, ravelerLabel):
        return OpSplitBodyCarving.getSavedObjectNamesForMstAndRavelerLabel(self._mst, ravelerLabel)

    @classmethod
    def getSavedObjectNamesForMstAndRavelerLabel(self, mst, ravelerLabel):
        # Find the saved objects that were split from this raveler object
        # Names should match <raveler label>.<object id>
        pattern = "{}.".format( ravelerLabel )
        return filter( lambda s: s.startswith(pattern), mst.object_names.keys() )


class OpFragmentSetLut(Operator):
    MST = InputSlot()
    RavelerLabel = InputSlot()
    
    Lut = OutputSlot()

    def setupOutputs(self):
        self.Lut.meta.shape = ( len(self.MST.value.objects.lut), )
        self.Lut.meta.dtype = numpy.int32
        
    def execute(self, slot, subindex, roi, result):
        assert slot == self.Lut
        assert roi.stop - roi.start == self.Lut.meta.shape
        
        ravelerLabel = self.RavelerLabel.value
        if ravelerLabel == 0:
            result[:] = 0
            return result

        mst = self.MST.value
        names = sorted(OpSplitBodyCarving.getSavedObjectNamesForMstAndRavelerLabel(mst, ravelerLabel))
        
        # Accumulate the objects objects from this raveler object that we've already split off
        result[:] = 0
        for name in names:
            objectSupervoxels = mst.object_lut[name]
            result[objectSupervoxels] = 1
        
        return result
    
    def propagateDirty(self, slot, subindex, roi):
        self.Lut.setDirty( slice(None) )

class OpSelectLabel(Operator):
    Input = InputSlot()
    SelectedLabel = InputSlot()
    Output = OutputSlot()
    
    def __init__(self, *args, **kwargs):
        super( OpSelectLabel, self ).__init__( *args, **kwargs )
    
    def setupOutputs(self):
        self.Output.meta.assignFrom(self.Input.meta)
    
    def execute(self, slot, subindex, roi, result):
        assert slot == self.Output, "Unknown output slot: {}".format( slot.name )
        if self.SelectedLabel.value == 0:
            result[:] = 0
        else:
            self.Input(roi.start, roi.stop).writeInto(result).wait()
            result[:] = numpy.where( result == self.SelectedLabel.value, 1, 0 )
        return result
    
    def propagateDirty(self, slot, subindex, roi):
        if slot == self.Input:
            self.Output.setDirty( roi.start, roi.stop )
        elif slot == self.SelectedLabel:
            self.Output.setDirty( slice(None) )
        else:
            assert False, "Dirty slot is unknown: {}".format( slot.name )



