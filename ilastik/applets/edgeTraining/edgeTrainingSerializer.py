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
import numpy as np
import vigra
from ilastik.applets.base.appletSerializer import AppletSerializer, SerialSlot, SerialDictSlot, SerialClassifierSlot
from ilastikrag import Rag
from ilastikrag.util import dataframe_from_hdf5, dataframe_to_hdf5

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

class SerialEdgeLabelsDictSlot(SerialSlot):
    def _serialize(self, parent_group, name, multislot):
        multislot_group = parent_group.create_group( name )
        for lane_index, slot in enumerate(multislot):
            edge_labels_dict = slot.value
            if edge_labels_dict:
                sp_ids = np.array(edge_labels_dict.keys())
                labels = np.array(edge_labels_dict.values())
            else:
                sp_ids = np.ndarray( (0,2), dtype=np.uint32 )
                labels = np.ndarray( (0,), dtype=np.uint8 )

            dict_group = multislot_group.create_group( "EdgeLabels{:04}".format(lane_index) )
            dict_group.create_dataset( 'sp_ids', data=sp_ids )
            dict_group.create_dataset( 'labels', data=labels )

    def _deserialize(self, multislot_group, slot):
        for lane_index, (_dict_groupname, dict_group) in enumerate(sorted(multislot_group.items())):
            sp_ids = dict_group['sp_ids'][:,:]
            labels = dict_group['labels'][:]
            edge_labels_dict = dict( zip(map(tuple, sp_ids), labels) )
            slot[lane_index].setValue( edge_labels_dict )

class SerialCachedDataFrameSlot(SerialSlot):
    def __init__(self, slot, cache, inslot=None, name=None,
                 default=None, depends=None, selfdepends=True):
        super(SerialCachedDataFrameSlot, self).__init__(
            slot, inslot, name, None, default, depends, selfdepends
        )
        self.cache = cache
        if self.name is None:
            self.name = slot.name
        
        # We want to bind to the INPUT, not Output:
        # - if the input becomes dirty, we want to make sure the cache is deleted
        # - if the input becomes dirty and then the cache is reloaded, we'll save the classifier.
        self._bind(cache.Input)

    def _serialize(self, group, name, slot):
        if slot.level == 0:
            # Is the cache up-to-date?
            # if not, we'll just return (don't recompute the classifier just to save it)
            slot_index = slot.operator.index(slot)
            inner_op = self.cache.getLane( slot_index )
            if inner_op._dirty:
                return
    
            dataframe = inner_op.Output.value
    
            # Can be None if the user didn't actually compute features yet.
            if dataframe is None:
                return
    
            df_group = group.create_group( name )
            dataframe_to_hdf5( df_group, dataframe )
        else:
            subgroup = group.create_group(name)
            for i, subslot in enumerate(slot):
                subname = self.subname.format(i)
                self._serialize(subgroup, subname, slot[i])

    def _deserialize(self, subgroup, slot):
        if slot.level == 0:
            dataframe = dataframe_from_hdf5( subgroup )
            slot_index = slot.operator.index(slot)
            inner_op = self.cache.getLane( slot_index )
            inner_op.forceValue( dataframe )
        else:
            # Pair stored indexes with their keys,
            # e.g. [(0,'0'), (2, '2'), (3, '3')]
            # Note that in some cases an index might be intentionally skipped.
            indexes_to_keys = { int(k) : k for k in subgroup.keys() }
            
            # Ensure the slot is at least big enough to deserialize into.
            max_index = max( [0] + indexes_to_keys.keys() )
            if len(slot) < max_index+1:
                slot.resize(max_index+1)

            # Now retrieve the data
            for i, subslot in enumerate(slot):
                if i in indexes_to_keys:
                    key = indexes_to_keys[i]
                    assert key == self.subname.format(i)
                    self._deserialize(subgroup[key], subslot)

class EdgeTrainingSerializer(AppletSerializer):
    def __init__(self, operator, projectFileGroupName):
        slots = [ SerialDictSlot(operator.FeatureNames),
                  SerialEdgeLabelsDictSlot(operator.EdgeLabelsDict),
                  SerialRagSlot(operator.Rag, operator.opRagCache, operator.Superpixels),
                  SerialCachedDataFrameSlot( operator.opEdgeFeaturesCache.Output,
                                             operator.opEdgeFeaturesCache,
                                             name="EdgeFeatures" ),
                  SerialClassifierSlot(operator.opClassifierCache.Output,
                                       operator.opClassifierCache)
                 ]
        super(EdgeTrainingSerializer, self).__init__(projectFileGroupName, slots=slots)
