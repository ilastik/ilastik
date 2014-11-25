
from collections import defaultdict

import numpy as np
from ilastik.applets.base.appletSerializer import AppletSerializer
from ilastik.applets.base.appletSerializer import SerialHdf5BlockSlot
from ilastik.applets.base.appletSerializer import SerialDictSlot
from ilastik.applets.base.appletSerializer import SerialSlot

import cPickle as pickle

import logging
logger = logging.getLogger(__name__)


class SerialPickledSlot(SerialSlot):
    def __init__(self, slot, name=None):
        super(SerialPickledSlot, self).__init__(slot, name=name)

    def _saveValue(self, group, name, value):
        pickled = pickle.dumps(value)
        group.create_dataset(name, data=pickled)

    def _getValue(self, dset, slot):
        pickled = dset[()]
        value = pickle.loads(pickled)
        slot.setValue( value )


class MriVolFilterSerializer(AppletSerializer):
    """
    ...
    """

    version = "0.7"

    def __init__(self, op, projectFileGroupName):
        slots = [SerialDictSlot(op.Configuration),
                 SerialPickledSlot(op.ReassignedObjects),
                 SerialSlot(op.Method),
                 SerialSlot(op.Threshold),
                 SerialSlot(op.ActiveChannels),
                 SerialHdf5BlockSlot(op.OutputHdf5,
                                     op.InputHdf5,
                                     op.CleanBlocks,
                                     name='caches',
                                     subname='cache{:03d}',),
                 SerialHdf5BlockSlot(op.IdsOutputHdf5,
                                     op.IdsInputHdf5,
                                     op.IdsCleanBlocks,
                                     name='idcache',
                                     subname='cache{:03d}',),
                 SerialHdf5BlockSlot(op.ArgmaxOutputHdf5,
                                     op.ArgmaxInputHdf5,
                                     op.ArgmaxCleanBlocks,
                                     name='argmaxcache',
                                     subname='cache{:03d}',),
                 ]
        super(MriVolFilterSerializer, self).__init__(
            projectFileGroupName, slots, op)
        self._labelString = "labelNames"

    def _serializeToHdf5(self, group, hdf5File, projectFilePath):
        slot = self.operator.LabelNames
        if len(slot) < 1:
            # no data yet
            return
        if slot[0].partner is not None:
            # slot is connected, upstream will serialize the names
            data = None
        else:
            data = [(s.value if s.ready() else None) for s in slot]

        pickled = pickle.dumps(data)
        if self._labelString in group:
            # don't know how to require_dataset() for pickled dataset
            del group[self._labelString]
        group.create_dataset(self._labelString, data=pickled)

    def _deserializeFromHdf5(self, group, groupVersion, hdf5File,
                             projectFilePath, headless=False):
        pickled = group[self._labelString][()]
        data = pickle.loads(pickled)
        if data is None:
            return
        slot = self.operator.LabelNames
        for i, d in enumerate(data):
            if d is not None:
                slot[i].setValue(d)
