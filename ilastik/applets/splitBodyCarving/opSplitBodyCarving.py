import sys
import os
import copy
import collections
import json
import numpy
import vigra
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.roi import roiFromShape, roiToSlice, getIntersectingBlocks, getBlockBounds, TinyVector
from lazyflow.operators import OpCrosshairMarkers, OpSelectLabel
from lazyflow.operators.operators import OpArrayCache

from ilastik.workflows.carving.opCarving import OpCarving

from ilastik.utility import bind

import logging
logger = logging.getLogger(__name__)

class OpSplitBodyCarving( OpCarving ):

    RavelerLabels = InputSlot()
    CurrentRavelerLabel = InputSlot(value=0)
    CurrentEditingFragment = InputSlot(value="", stype='string')
    AnnotationFilepath = InputSlot(optional=True, stype='filepath') # Included as a slot here for easy serialization

    NavigationCoordinates = InputSlot(optional=True) # Display-only: For passing navigation request coordinates downstream
    
    CurrentRavelerObject = OutputSlot()
    CurrentRavelerObjectRemainder = OutputSlot()
    CurrentFragmentSegmentation = OutputSlot()
    MaskedSegmentation = OutputSlot()

    EditedRavelerBodyList = OutputSlot() # A single object: a list of strings
    
    AnnotationCrosshairs = OutputSlot()
    AnnotationLocations = OutputSlot()
    AnnotationBodyIds = OutputSlot()
    Annotations = OutputSlot()
    
    BLOCK_SIZE = 520
    SEED_MARGIN = 10

    def __init__(self, *args, **kwargs):
        super( OpSplitBodyCarving, self ).__init__( *args, **kwargs )

        self._opParseAnnotations = OpParseAnnotations( parent=self )
        self._opParseAnnotations.AnnotationFilepath.connect( self.AnnotationFilepath )
        self._opParseAnnotations.BodyLabels.connect( self.RavelerLabels )
        self.AnnotationLocations.connect( self._opParseAnnotations.AnnotationLocations )
        self.AnnotationBodyIds.connect( self._opParseAnnotations.AnnotationBodyIds )
        self.Annotations.connect( self._opParseAnnotations.Annotations )
        
        self._opSelectRavelerObject = OpSelectLabel( parent=self )
        self._opSelectRavelerObject.SelectedLabel.connect( self.CurrentRavelerLabel )
        self._opSelectRavelerObject.Input.connect( self.RavelerLabels )
        self.CurrentRavelerObject.connect( self._opSelectRavelerObject.Output )
        
        # LUTs of all fragments of the current Raveler body are combined into a single LUT
        self._opFragmentSetLut = OpFragmentSetLut( parent=self )
        self._opFragmentSetLut.MST.connect( self._opMstCache.Output )
        self._opFragmentSetLut.RavelerLabel.connect( self.CurrentRavelerLabel )
        self._opFragmentSetLut.CurrentEditingFragment.connect( self.CurrentEditingFragment )
        self._opFragmentSetLut.Trigger.connect( self.Trigger )

        # The combined LUT is cached to avoid recomputing it for every orthoview.
        self._opFragmentSetLutCache = OpArrayCache( parent=self )
        self._opFragmentSetLutCache.blockShape.setValue( (1e10,) ) # Something big (always get the whole thing)
        
        # Display-only: Show the annotations as crosshairs
        self._opCrosshairs = OpCrosshairMarkers( parent=self )
        self._opCrosshairs.CrosshairRadius.setValue( 5 )
        self._opCrosshairs.Input.connect( self.RavelerLabels )
        self._opCrosshairs.PointList.connect( self.AnnotationLocations )
        self.AnnotationCrosshairs.connect( self._opCrosshairs.Output )

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
        self._opFragmentSetLutCache.Input.connect( self._opFragmentSetLut.Lut )
            
        super( OpSplitBodyCarving, self ).setupOutputs()
        self.MaskedSegmentation.meta.assignFrom(self.Segmentation.meta)
        def handleDirtySegmentation(slot, roi):
            self.MaskedSegmentation.setDirty( roi )
        self.Segmentation.notifyDirty( handleDirtySegmentation )
        
        self.CurrentRavelerObjectRemainder.meta.assignFrom( self.RavelerLabels.meta )
        self.CurrentRavelerObjectRemainder.meta.dtype = numpy.uint8
        self.CurrentFragmentSegmentation.meta.assignFrom( self.RavelerLabels.meta )
        self.CurrentFragmentSegmentation.meta.dtype = numpy.uint8

        if not self._opFragmentSetLutCache.Output.ready():
            self.MaskedSegmentation.meta.NOTREADY = True
            self.CurrentRavelerObjectRemainder.meta.NOTREADY = True

        self.EditedRavelerBodyList.meta.dtype = object
        self.EditedRavelerBodyList.meta.shape = (1,)
        
    def execute(self, slot, subindex, roi, result):
        if slot == self.EditedRavelerBodyList:
            return self._executeEditedRavelerBodyList(roi, result)
        elif slot == self.MaskedSegmentation:
            return self._executeMaskedSegmentation(roi, result)
        elif slot == self.CurrentRavelerObjectRemainder:
            return self._executeCurrentRavelerObjectRemainder(roi, result)
        elif slot == self.CurrentFragmentSegmentation:
            return self._executeCurrentFragmentSegmentation(roi, result)
        else:
            return super( OpSplitBodyCarving, self ).execute( slot, subindex, roi, result )

    def _executeEditedRavelerBodyList(self, roi, result):
        savedLabels = set()
        if self._mst is None:
            result[0] = []
        else:
            for fragmentName in self._mst.object_names.keys():
                bodyName = fragmentName[0:fragmentName.find('.')]
                savedLabels.add( int(bodyName) )
    
            result[0] = sorted( savedLabels )
        return result
    
    def _executeMaskedSegmentation(self, roi, result):
        result = self.Segmentation(roi.start, roi.stop).writeInto(result).wait()
        result[:] = numpy.array([0,0,1])[result] # Keep only the pixels whose value is '2' (the foreground)
        currentRemainder = self.CurrentRavelerObjectRemainder(roi.start, roi.stop).wait()
        numpy.logical_and( result, currentRemainder, out=result )
        result[:] *= 2 # In carving, background is always 1 and segmentation pixels are always 2
        return result

    def _executeCurrentRavelerObjectRemainder(self, roi, result):        
        # Start with the original raveler object
        self._opSelectRavelerObject.Output(roi.start, roi.stop).writeInto(result).wait()

        lut = self._opFragmentSetLutCache.Output[:].wait()

        # Save memory: Implement (A - B) == (A & ~B), and do it with in-place operations
        slicing = roiToSlice( roi.start[1:4], roi.stop[1:4] )
        a = result[0,...,0]
        b = lut[self._mst.regionVol[slicing]] # (Advanced indexing)
        numpy.logical_not( b, out=b ) # ~B
        numpy.logical_and(a, b, out=a) # A & ~B
        
        return result

    def _executeCurrentFragmentSegmentation(self, roi, result):
        # Start with the original raveler object
        self.CurrentRavelerObject(roi.start, roi.stop).writeInto(result).wait()

        lut = self._opFragmentSetLutCache.Output[:].wait()

        slicing = roiToSlice( roi.start[1:4], roi.stop[1:4] )
        a = result[0,...,0]
        b = lut[self._mst.regionVol[slicing]] # (Advanced indexing)

        # Use bitwise_and instead of numpy.where to avoid the temporary caused by a == 0
        #a[:] = numpy.where( a == 0, 0, b )
        assert self.CurrentFragmentSegmentation.meta.dtype == numpy.uint8, "This code assumes uint8 as the dtype!"
        a[:] *= 0xFF # Assumes uint8
        numpy.bitwise_and( a, b, out=a )
        return result
    
    def propagateDirty(self, slot, subindex, roi):
        if slot == self.RavelerLabels:
            self.MaskedSegmentation.setDirty( roi.start, roi.stop )
        elif slot == self.CurrentRavelerLabel:
            self.MaskedSegmentation.setDirty( slice(None) )
        elif slot == self.AnnotationFilepath or \
             slot == self.CurrentEditingFragment or \
             slot == self.AnnotationLocations:
            self.EditedRavelerBodyList.setDirty()
            return
        elif slot == self.NavigationCoordinates or \
             slot == self.AnnotationBodyIds:
            pass
        else:
            super( OpSplitBodyCarving, self ).propagateDirty( slot, subindex, roi )
    
    def getFragmentNames(self, ravelerLabel):
        names = OpSplitBodyCarving.getSavedObjectNamesForMstAndRavelerLabel(self._mst, ravelerLabel)
        if self.CurrentEditingFragment.ready():
            pattern = "{}.".format( ravelerLabel )
            currentFragment = self.CurrentEditingFragment.value
            # If the "current fragment" belongs to this label, make sure it is in the list
            #  (even if it isn't saved yet)
            if ( currentFragment != ""
                 and currentFragment.startswith( pattern ) 
                 and (len(names) == 0 or currentFragment != names[-1] )):
                names.append(currentFragment)
        return names

    @classmethod
    def getSavedObjectNamesForMstAndRavelerLabel(self, mst, ravelerLabel):
        # Find the saved objects that were split from this raveler object
        # Names should match <raveler label>.<object id>
        pattern = "{}.".format( ravelerLabel )
        if mst is not None:
            names = sorted(filter( lambda s: s.startswith(pattern), mst.object_names.keys() ))
            return names            
        return []
    
    def saveObjectAs(self, name):
        """
        Overridden from base class.
        """
        is_new = ( name in self._mst.object_names.keys() )
        super( OpSplitBodyCarving, self ).saveObjectAs(name)
        if is_new:
            self.EditedRavelerBodyList.setDirty()

    def deleteObject(self, name):
        """
        Overridden from base class.
        """
        deleted = super( OpSplitBodyCarving, self ).deleteObject(name)
        if deleted:
            self.EditedRavelerBodyList.setDirty()
        return deleted

class OpFragmentSetLut(Operator):
    MST = InputSlot()
    RavelerLabel = InputSlot()
    CurrentEditingFragment = InputSlot()
    Trigger = InputSlot(optional=True) # For dirty notifications only
    
    Lut = OutputSlot()

    def __init__(self, *args, **kwargs):
        super( OpFragmentSetLut, self ).__init__(*args, **kwargs)
        
        # HACK: See setupOutputs
        self.MST.notifyDirty( bind(self._setupOutputs) )

    def setupOutputs(self):
        self.Lut.meta.shape = ( len(self.MST.value.objects.lut), )
        self.Lut.meta.dtype = numpy.uint8
        
    def execute(self, slot, subindex, roi, result):
        assert slot == self.Lut
        assert roi.stop - roi.start == self.Lut.meta.shape
        
        ravelerLabel = self.RavelerLabel.value
        if ravelerLabel == 0:
            result[:] = 0
            return result

        print "Requesting fragment names"
        mst = self.MST.value
        names = OpSplitBodyCarving.getSavedObjectNamesForMstAndRavelerLabel(mst, ravelerLabel)
        print "Got fragment names: {}".format( names )
        
        # Accumulate the supervoxels from each fragment that came from the current raveler object
        result[:] = 0
        for i, name in reversed(list(enumerate(names))):
            if name != self.CurrentEditingFragment.value:
                objectSupervoxels = mst.object_lut[name]
                # Give each fragment it's own label to support different colors for each
                result[objectSupervoxels] = i+1

        print "Finished accumulating fragments into lut"
        return result
    
    def propagateDirty(self, slot, subindex, roi):
        self.Lut.setDirty( slice(None) )


# Example Raveler bookmark json file:
"""
{
  "data": [
    {
      "text": "split <username=ogundeyio> <time=1370275410> <status=review>", 
      "body ID": 4199, 
      "location": [
        361, 
        478, 
        1531
      ]
    }, 
    {
      "text": "split <username=ogundeyio> <time=1370275416> <status=review>", 
      "body ID": 4199, 
      "location": [
        301, 
        352, 
        1531
      ]
    }, 
    {
      "text": "Separate from bottom merge", 
      "body ID": 4182, 
      "location": [
        176, 
        419, 
        1556
      ]
    }, 
    {
      "text": "Needs to be separate", 
      "body ID": 4199, 
      "location": [
        163, 
        244, 
        1564
      ]
    }
  ],
  "metadata": {
    "username": "ogundeyio", 
    "software version": "1.7.15", 
    "description": "bookmarks", 
    "file version": 1, 
    "software revision": "4406", 
    "computer": "emrecon11.janelia.priv", 
    "date": "03-June-2013 14:49", 
    "session path": "/groups/flyem/data/medulla-FIB-Z1211-25-production/align2/substacks/00051_3508-4007_3759-4258_1500-1999/focused-910-sessions/ogundeyio.910", 
    "software": "Raveler"
  }
}
"""

# Example Raveler substack.json file.
# Note that raveler substacks are viewed as 500**3 volumes with a 10 pixel border on all sides,
#  which means that the volume ilastik actually loads is 520**3
# The bookmark Z-coordinates are GLOBAL to the entire stack, but the XY coordinates are relative 
#  to the 520**3 volume we have loaded.
# Therefore, we need to offset the Z-coordinates in any bookmarks we load using the idz1 and border fields below.
# In this example, idz1 = 1500, and border=10, which means the first Z-slice in the volume we loaded is slice 1490.
"""
{
    "idz1": 1500, 
    "gray_view": true, 
    "idz2": 1999, 
    "substack_id": 51, 
    "stack_path": "/groups/flyem/data/medulla-FIB-Z1211-25-production/align2", 
    "ry2": 4268, 
    "basename": "iso.%05d.png", 
    "substack_path": "/groups/flyem/data/medulla-FIB-Z1211-25-production/align2/substacks/00051_3508-4007_3759-4258_1500-1999", 
    "idx2": 4007, 
    "rz2": 2009, 
    "rz1": 1490, 
    "raveler_view": true, 
    "rx1": 3498, 
    "idy1": 3759, 
    "idx1": 3508, 
    "rx2": 4017, 
    "border": 10, 
    "idy2": 4258, 
    "ry1": 3749
}
"""



class OpParseAnnotations(Operator):
    AnnotationFilepath = InputSlot(stype='filepath')
    BodyLabels = InputSlot()

    # All outputs have dtype=object (2 are lists, one is a dict)    
    AnnotationLocations = OutputSlot()
    AnnotationBodyIds = OutputSlot()
    
    Annotations = OutputSlot()

    # Annotation type
    Annotation = collections.namedtuple( 'Annotation', ['ravelerLabel', 'comment'] )
            
    def __init__(self, *args, **kwargs):
        super( OpParseAnnotations, self ).__init__(*args, **kwargs)
        self._annotations = None
    
    def setupOutputs(self):
        self.AnnotationLocations.meta.shape = (1,)
        self.AnnotationLocations.meta.dtype = object

        self.AnnotationBodyIds.meta.shape = (1,)
        self.AnnotationBodyIds.meta.dtype = object

        self.Annotations.meta.shape = (1,)
        self.Annotations.meta.dtype = object
        
        self._annotations = None

    class AnnotationParsingException(Exception):
        def __init__(self, msg, original_exc=None):
            super(OpParseAnnotations.AnnotationParsingException, self).__init__()
            self.original_exc = original_exc
            self.msg = msg

    @classmethod
    def _parseAnnotationFile(cls, annotation_filepath, body_label_img_slot):
        """
        Returns dict of annotations of the form { coordinate_3d : Annotation }
        """
        try:
            with open(annotation_filepath) as annotationFile:
                annotation_json_dict = json.load( annotationFile )
        except Exception as ex:
            raise cls.AnnotationParsingException(
                 "Failed to parse your bookmark file.  It isn't valid JSON.", ex), None, sys.exc_info()[2]

        if 'data' not in annotation_json_dict:
            raise cls.AnnotationParsingException(
                 "Couldn't find the 'data' list in your bookmark file.  Giving up."), None, sys.exc_info()[2]

        # Before we parse the bookmarks data, locate the substack description
        #  to calculate the z-coordinate offset (see comment about substack coordinates, above)
        bookmark_dir = os.path.split(annotation_filepath)[0]
        substack_dir = os.path.split(bookmark_dir)[0]
        substack_description_path = os.path.join( substack_dir, 'substack.json' )
        try:
            with open(substack_description_path) as substack_description_file:
                substack_description_json_dict = json.load( substack_description_file )
        except Exception as ex:
            raise cls.AnnotationParsingException(
                 "Failed to parse SUBSTACK",
                 "Attempted to open substack description file:\n {}"
                 "\n but something went wrong.  See console output for details.  Giving up."
                 .format(substack_description_path) ), None, sys.exc_info()[2]

        # See comment above about why we have to subtract a Z-offset
        z_offset = substack_description_json_dict['idz1'] - substack_description_json_dict['border']

        # Each bookmark is a dict (see example above)
        annotations = {}
        bookmarks = annotation_json_dict['data']
        for bookmark in bookmarks:
            if 'text' in bookmark and str(bookmark['text']).lower().find( 'split' ) != -1:
                coord3d = bookmark['location']
                coord3d[1] = 520 - coord3d[1] # Raveler y-axis is inverted (Raveler substacks are 520 cubes)
                coord3d[2] -= z_offset # See comments above re: substack coordinates
                coord3d = tuple(coord3d)
                coord5d = (0,) + coord3d + (0,)
                pos = TinyVector(coord5d)
                sample_roi = (pos, pos+1)
                # For debug purposes, we sometimes load a smaller volume than the original.
                # Don't import bookmarks that fall outside our volume
                if (pos < body_label_img_slot.meta.shape).all():
                    # Sample the label volume to determine the body id (raveler label)
                    label_sample = body_label_img_slot(*sample_roi).wait()
                    annotations[coord3d] = OpParseAnnotations.Annotation( ravelerLabel=label_sample[0,0,0,0,0], 
                                                       comment=str(bookmark['text']) )
        
        return annotations

    def execute(self, slot, subindex, roi, result):
        # Parse file and cache results.
        if self._annotations is None:
            annotation_filepath = self.AnnotationFilepath.value
            self._annotations = OpParseAnnotations._parseAnnotationFile(annotation_filepath, self.BodyLabels)

        if slot == self.Annotations:
            result[0] = self._annotations
        elif slot == self.AnnotationLocations:
            result[0] = sorted( self._annotations.keys() )
        elif slot == self.AnnotationBodyIds:
            result[0] = sorted( set( map( lambda (label, comment): label, self._annotations.values() ) ) )
        else:
            assert False, "Unknown output slot: {}".format( slot.name )

    def propagateDirty(self, slot, subindex, roi):
        # Everything is dirty
        self._annotations = None
        self.AnnotationLocations.setDirty()
        self.AnnotationBodyIds.setDirty()
        self.Annotations.setDirty()





