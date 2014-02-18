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

import tempfile
import shutil
import os
import numpy
from lazyflow.graph import Graph
from ilastik.applets.dataSelection.opDataSelection import OpDataSelectionGroup, DatasetInfo

class TestOpDataSelectionGroup(object):

    @classmethod
    def setupClass(cls):
        cls.workingDir = tempfile.mkdtemp()
        cls.group1Data = [ ( os.path.join(cls.workingDir, 'A.npy'), numpy.random.random( (100,100, 1) ) ),
                           ( os.path.join(cls.workingDir, 'C.npy'), numpy.random.random( (100,100, 1) ) ) ]

        for name, data in cls.group1Data:
            numpy.save(name, data)
        
    @classmethod
    def teardownClass(cls):
        shutil.rmtree(cls.workingDir)

    def test(self):
        infoA = DatasetInfo()
        infoA.filePath = self.group1Data[0][0]
        
        infoC = DatasetInfo()
        infoC.filePath = self.group1Data[1][0]
        
        graph = Graph()
        op = OpDataSelectionGroup( graph=graph )
        op.WorkingDirectory.setValue( self.workingDir )
        op.DatasetRoles.setValue( ['RoleA', 'RoleB', 'RoleC'] )

        op.DatasetGroup.resize( 3 )
        op.DatasetGroup[0].setValue( infoA )
        # Leave RoleB blank -- datasets other than the first are optional
        op.DatasetGroup[2].setValue( infoC )

        assert op.ImageGroup[0].ready()
        assert op.ImageGroup[2].ready()
        
        expectedDataA = self.group1Data[0][1]
        dataFromOpA = op.ImageGroup[0][:].wait()
        
        assert dataFromOpA.dtype == expectedDataA.dtype 
        assert dataFromOpA.shape == expectedDataA.shape         
        assert (dataFromOpA == expectedDataA).all()

        expectedDataC = self.group1Data[0][1]
        dataFromOpC = op.ImageGroup[0][:].wait()
        
        assert dataFromOpC.dtype == expectedDataC.dtype 
        assert dataFromOpC.shape == expectedDataC.shape         
        assert (dataFromOpC == expectedDataC).all()

        assert op.Image.ready()
        assert (op.Image[:].wait() == expectedDataA).all()


if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
