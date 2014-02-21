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

import numpy
import vigra
from lazyflow.graph import Graph
from lazyflow.operators.opColorizeLabels import OpColorizeLabels

class TestOpColorizeLabels(object):
    
    def setUp(self):
        # Create a label array that's symmetric about the x-y axes
        data = numpy.indices((10,10), dtype=int).sum(0)
    
        assert (data == data.transpose()).all()
    
        data = data.view(vigra.VigraArray)
        data.axistags = vigra.defaultAxistags('xy')
        data = data.withAxes(*'txyzc')
    
        assert data.shape == (1,10,10,1,1)
    
        graph = Graph()
        op = OpColorizeLabels(graph=graph)
        op.Input.setValue(data)
        self.op = op

    def testBasic(self):
        op = self.op
    
        # Test requesting specific channels: Don't get RGBA, just get GBA.
        colorizedData = op.Output[:,5:,5:,:,1:4].wait()
        
        # Output is colorized (3 channels)
        assert colorizedData.shape == (1,5,5,1,3)

        # If we transpose x-y, then the data should still be the same,
        # which implies that identical labels got identical colors
        # (i.e. we chose deterministic colors)
        assert (colorizedData == colorizedData.transpose(0,2,1,3,4)).all()

        # Different labels should get different colors
        assert ( colorizedData[0,1,1,0,0] != colorizedData[0,2,2,0,0]
              or colorizedData[0,1,1,0,1] != colorizedData[0,2,2,0,1]
              or colorizedData[0,1,1,0,2] != colorizedData[0,2,2,0,2] )

        assert (colorizedData[0,1:,1:,0,2] == 255).all(), "Alpha should be 255 for all labels except label 0"

    def testOverrideColors(self):
        op = self.op
        
        overrides = {}
        overrides[1] = (1,2,3,4)
        overrides[2] = (5,6,7,8)

        # Label 0 override is black and transparent by default
        colorizedData = op.Output[...].wait()
        assert (colorizedData[0,0,0,0,:] == 0).all()

        # Apply custom overrides
        op.OverrideColors.setValue( overrides )        
        colorizedData = op.Output[...].wait()

        # Check for non-random colors on the labels we want to override        
        assert (colorizedData[0,1,0,0,:] == overrides[1]).all()
        assert (colorizedData[0,0,1,0,:] == overrides[1]).all()
        assert (colorizedData[0,1,1,0,:] == overrides[2]).all()
        assert (colorizedData[0,2,0,0,:] == overrides[2]).all()
        assert (colorizedData[0,0,2,0,:] == overrides[2]).all()

        # Other labels should be random
        assert not (colorizedData[0,0,3,0,:] == overrides[2]).all()
        
        
if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)
    if not ret: sys.exit(1)
