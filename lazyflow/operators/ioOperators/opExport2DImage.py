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

import os

import numpy
import vigra

from lazyflow.graph import Operator, InputSlot

class OpExport2DImage(Operator):
    """
    Export a 2D image using vigra.impex.writeImage()
    """
    Input = InputSlot() # Allowed to have more than 2 dimensions as long as the others are singletons.
    Filepath = InputSlot()
    
    def setupOutputs(self):
        # Ask vigra which extensions are supported.
        # If vigra was compiled with libpng, libjpeg, etc.,
        #  then 'png', 'jpeg', etc. will be in this list.
        # Otherwise, they aren't supported.        
        extension = os.path.splitext(self.Filepath.value)[1][1:]
        if extension not in vigra.impex.listExtensions().split():
            msg = "Unknown export format: '{}' "\
                  "is not a recognized 2D image extension.".format( extension )
            raise Exception(msg)
        

    # No Output slots...
    def execute(self, slot, subindex, roi, result): pass
    def propagateDirty(self, slot, subindex, roi): pass
    
    def run_export(self):
        """
        Requests all of the input and saves the output file.
        SYNCHRONOUSLY.
        """
        # Check for errors...
        tagged_shape = self.Input.meta.getTaggedShape()
        nonzero_dims = filter( lambda (k,v): k != 'c' and v > 1, tagged_shape.items() )
        assert len(nonzero_dims) <= 2, "Image must have no more than 2 non-singleton dimensions."

        data = self.Input[:].wait()
        data = vigra.taggedView( data, self.Input.meta.axistags )
        data = data.squeeze()
        if len(data.shape) == 1 or len(data.shape) == 2 and data.axistags.channelIndex < 2:
            data = data[numpy.newaxis, :]
        assert len(data.shape) == 2 or (len(data.shape) == 3 and data.axistags.channelIndex < 3), "Image has shape {}, channelIndex is {}".format(data.shape, data.axistags.channelIndex)
        
        vigra.impex.writeImage(data, self.Filepath.value)

if __name__ == "__main__":
    a = numpy.random.random((1, 100, 1, 100, 1)) * 255
    a = a.astype( numpy.uint8 )
    a = vigra.taggedView(a, vigra.defaultAxistags('txyzc'))
    
    from lazyflow.graph import Graph
    op = OpExport2DImage(graph=Graph())
    op.Input.setValue(a)
    op.Filepath.setValue('/tmp/test.png')
    
    op.run_export()

