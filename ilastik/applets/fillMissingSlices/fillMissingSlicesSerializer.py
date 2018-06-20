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
#		   http://ilastik.org/license.html
###############################################################################
from ilastik.applets.base.appletSerializer import AppletSerializer, SerialSlot

from lazyflow.operators.opInterpMissingData import OpDetectMissing


class FillMissingSlicesSerializer(AppletSerializer):

    def __init__(self, topGroupName, topLevelOperator):
        slots = [SerialSlot(topLevelOperator.PatchSize),
                 SerialSlot(topLevelOperator.HaloSize)]
        super(FillMissingSlicesSerializer, self).__init__(topGroupName,
                                                          slots=slots)
        self._operator = topLevelOperator

    def _serializeToHdf5(self, topGroup, hdf5File, projectFilePath):
        dslot = self._operator.Detector[0]
        extractedSVM = dslot[:].wait()
        self._setDataset(topGroup, 'SVM', extractedSVM)
        for s in self._operator.innerOperators:
            s.resetDirty()

    def _deserializeFromHdf5(self, topGroup, version, h5file, projectFilePath, headless=False):
        svm = self._operator.OverloadDetector.setValue(
            self._getDataset(topGroup, 'SVM'))
        for s in self._operator.innerOperators:
            s.resetDirty()

    def isDirty(self):
        return any([s.isDirty() for s in self._operator.innerOperators])

    ### internal ###
    def _setDataset(self, group, dataName, dataValue):
        if dataName not in list(group.keys()):
            # Create and assign
            group.create_dataset(dataName, data=dataValue)
        else:
            # Assign (this will fail if the dtype doesn't match)
            group[dataName][()] = dataValue

    def _getDataset(self, group, dataName):
        try:
            result = group[dataName].value
        except KeyError:
            result = ''
        return result
