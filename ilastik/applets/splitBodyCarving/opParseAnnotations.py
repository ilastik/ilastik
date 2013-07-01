import sys
import os
import collections
import json

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.roi import TinyVector

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

