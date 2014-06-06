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
from lazyflow.graph import InputSlot
from ilastik.applets.dataExport.opDataExport import OpDataExport
from ilastik.applets.base.applet import DatasetConstraintError

class OpCountingDataExport( OpDataExport ):
    # Add these additional input slots, to be used by the GUI.
    PmapColors = InputSlot()
    LabelNames = InputSlot()
    UpperBound = InputSlot()
    ConstraintDataset = InputSlot() # Any dataset from the training workflow, which we'll use for 
                                    #   comparison purposes when checking dataset constraints.
    
    def __init__(self,*args,**kwargs):
        super(OpCountingDataExport, self).__init__(*args, **kwargs)
        self.ConstraintDataset.notifyReady(self._checkDataConstraint)
        self.RawData.notifyReady(self._checkDataConstraint)
        
    def _checkDataConstraint(self, *args):
        """
        The batch workflow uses the same classifier as the training workflow,
         and therefore the batch datasets must be compatible with the training datasets in certain respects.
        This function tests those constraints by comparing the batch input against a (arbitrary) training dataset,
        and raises a DatasetConstraintError if something is incorrect.
        """
        if not self.ConstraintDataset.ready() or not self.RawData.ready():
            return
        
        dataTrain = self.ConstraintDataset.meta
        dataBatch = self.RawData.meta

        # Must have same dimensionality (but not necessarily the same shape)
        if len(dataTrain.shape) != len(dataBatch.shape):
            raise DatasetConstraintError("Batch Prediction Input","Batch input must have the same dimension as training input.")
        
        # Must have same number of channels
        if dataTrain.getTaggedShape()['c'] != dataBatch.getTaggedShape()['c']:
            raise DatasetConstraintError("Batch Prediction Input","Batch input must have the same number of channels as training input.")
        
        # Must have same set of axes (but not necessarily in the same order)
        if set(dataTrain.getAxisKeys()) != set(dataBatch.getAxisKeys()):
            raise DatasetConstraintError("Batch Prediction Input","Batch input axis must fit axis of training input.")
