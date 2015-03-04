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
from lazyflow.graph import Operator, InputSlot, OutputSlot

from ilastik.applets.base.applet import DatasetConstraintError

class OpLayerViewer(Operator):
    """
    This is the default top-level operator for the layer-viewer class.
    Note that applets based on the LayerViewer applet (and the LayerViewerGui) do NOT need to use this operator.
    Any operator will work with the LayerViewerGui base class.
    """
    name = "OpLayerViewer"
    category = "top-level"

    RawInput = InputSlot()
    OtherInput = InputSlot(optional=True)

    def __init__(self, *args, **kwargs):
        super( OpLayerViewer, self ).__init__(*args, **kwargs)
        
        self.RawInput.notifyReady( self.checkConstraints )
        self.OtherInput.notifyReady( self.checkConstraints )
        
    def checkConstraints(self, *args):
        """
        Example of how to check input data constraints.
        """
        if self.OtherInput.ready() and self.RawInput.ready():
            rawTaggedShape = self.RawInput.meta.getTaggedShape()
            otherTaggedShape = self.OtherInput.meta.getTaggedShape()
            raw_time_size = rawTaggedShape.get('t', 1)
            other_time_size = otherTaggedShape.get('t', 1)
            if raw_time_size != other_time_size and raw_time_size != 1 and other_time_size != 1:
                msg = "Your 'raw' and 'other' datasets appear to have differing sizes in the time dimension.\n"\
                      "Your datasets have shapes: {} and {}".format( self.RawInput.meta.shape, self.OtherInput.meta.shape )
                raise DatasetConstraintError( "Layer Viewer", msg )
                
            rawTaggedShape['c'] = None
            otherTaggedShape['c'] = None
            rawTaggedShape['t'] = None
            otherTaggedShape['t'] = None
            if dict(rawTaggedShape) != dict(otherTaggedShape):
                msg = "Raw data and other data must have equal spatial dimensions (different channels are okay).\n"\
                      "Your datasets have shapes: {} and {}".format( self.RawInput.meta.shape, self.OtherInput.meta.shape )
                raise DatasetConstraintError( "Layer Viewer", msg )
        
        