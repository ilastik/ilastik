
import numpy as np
from ilastik.applets.base.appletSerializer import AppletSerializer
from ilastik.applets.base.appletSerializer import SerialHdf5BlockSlot
from ilastik.applets.base.appletSerializer import SerialDictSlot
from ilastik.applets.base.appletSerializer import SerialSlot

import cPickle as pickle

import logging
logger = logging.getLogger(__name__)


class MriVolFilterSerializer(AppletSerializer):
    """
    ...
    """

    version = "0.4"

    def __init__(self, op, projectFileGroupName):
        slots = [SerialDictSlot(op.Configuration),
                 SerialSlot(op.Method),
                 SerialSlot(op.Threshold),
                 SerialSlot(op.ActiveChannels),
                 SerialHdf5BlockSlot(op.OutputHdf5,
                                     op.InputHdf5,
                                     op.CleanBlocks,
                                     name='caches',
                                     subname='cache{:03d}',),
                 ]
        super(MriVolFilterSerializer, self).__init__(
            projectFileGroupName, slots, op)

    def _serializeToHdf5(self, group, hdf5File, projectFilePath):
        slot = self.operator.LabelNames
        if slot[0].partner is not None:
            # slot is connected, upstream will serialize the names
            data = None
        else:
            data = [s.value for s in slot]

        pickled = pickle.dumps(data)
        name = "labelNames"
        if name in group:
            # don't know how to require_dataset() for pickled dataset
            del group[name]
        group.create_dataset(name, data=pickled)

    def _deserializeFromHdf5(self, group, groupVersion, hdf5File,
                             projectFilePath, headless=False):
        pickled = group['labelNames'][()]
        data = pickle.loads(pickled)
        if data is None:
            return
        slot = self.operator.LabelNames
        for i, d in enumerate(data):
            slot[i].setValue(d)

    def _saveValue(self, group, name, value):
        pickled = pickle.dumps(value)
        group.create_dataset(name, data=pickled)

    def _getValue(self, dset, slot):
        pickled = dset[()]
        value = pickle.loads(pickled)
        slot.setValue(value)
