###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
#           http://ilastik.org/license.html
###############################################################################
import vigra
from ilastik.applets.base.appletSerializer import AppletSerializer, SerialSlot, SerialDictSlot
from ilastikrag import Rag

class SerialRagSlot(SerialSlot):
    def __init__(self, slot, cache, labels_slot):
        super(SerialRagSlot, self).__init__(slot, name='Rags')
        self.cache = cache
        self.labels_slot = labels_slot
        
        # We want to bind to the INPUT, not Output:
        # - if the input becomes dirty, we want to make sure the cache is deleted
        # - if the input becomes dirty and then the cache is reloaded, we'll save the rag.
        self._bind(cache.Input)

    def _serialize(self, parent_group, name, multislot):
        rags_group = parent_group.create_group( name )
        
        for lane_index, slot in enumerate(multislot):
            # Is the cache up-to-date?
            # if not, we'll just return (don't recompute the classifier just to save it)
            if self.cache[lane_index]._dirty:
                continue

            rag = self.cache[lane_index].Output.value
    
            # Rag can be None if there isn't any training data yet.
            if rag is None:
                continue

            rag_group = rags_group.create_group( "Rag_{:04}".format(lane_index) )
            rag.serialize_hdf5( rag_group, store_labels=False )

    def deserialize(self, rags_group):
        """
        Have to override this to ensure that dirty is always set False.
        """
        super(SerialRagSlot, self).deserialize(rags_group)
        self.dirty = False

    def _deserialize(self, rags_group, slot):
        for lane_index, (_rag_groupname, rag_group) in enumerate(sorted(rags_group.items())):
            label_img = self.labels_slot[lane_index][:].wait()
            label_img = vigra.taggedView( label_img, self.labels_slot.meta.axistags )
            label_img = label_img.dropChannelAxis()
            
            rag = Rag.deserialize_hdf5( rag_group, label_img )
            self.cache[lane_index].forceValue( rag )

class EdgeTrainingSerializer(AppletSerializer):
    def __init__(self, operator, projectFileGroupName):
        slots = [ SerialDictSlot(operator.FeatureNames),
                  SerialRagSlot(operator.Rag, operator.opRagCache, operator.Superpixels) ]
        super(EdgeTrainingSerializer, self).__init__(projectFileGroupName, slots=slots)
