# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Copyright 2011-2014, the ilastik developers

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
        if self.RawInput.ready():
            numChannels = self.RawInput.meta.getTaggedShape()['c']
            if numChannels != 1:
                raise DatasetConstraintError(
                    "Layer Viewer",
                    "Raw data must have exactly one channel.  " +
                    "You attempted to add a dataset with {} channels".format( numChannels ) )

        if self.OtherInput.ready() and self.RawInput.ready():
            rawTaggedShape = self.RawInput.meta.getTaggedShape()
            otherTaggedShape = self.OtherInput.meta.getTaggedShape()
            rawTaggedShape['c'] = None
            otherTaggedShape['c'] = None
            if dict(rawTaggedShape) != dict(otherTaggedShape):
                msg = "Raw data and other data must have equal dimensions (different channels are okay).\n"\
                      "Your datasets have shapes: {} and {}".format( self.RawInput.meta.shape, self.OtherInput.meta.shape )
                raise DatasetConstraintError( "Layer Viewer", msg )
        
        