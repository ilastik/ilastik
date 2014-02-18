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
import tempfile
import shutil

import numpy
import vigra

from lazyflow.graph import Graph
from lazyflow.operators.ioOperators import OpInputDataReader, OpNpyWriter

class TestOpNpyWriter(object):
    
    @classmethod
    def setupClass(cls):
        cls._tmpdir = tempfile.mkdtemp()

    @classmethod
    def teardownClass(cls):
        shutil.rmtree(cls._tmpdir) 
    
    def testBasic(self):
        data = numpy.random.random( (100,100) ).astype( numpy.float32 )
        data = vigra.taggedView( data, vigra.defaultAxistags('xy') )
        
        graph = Graph()
        opWriter = OpNpyWriter(graph=graph)
        opWriter.Input.setValue(data)
        opWriter.Filepath.setValue( self._tmpdir + '/npy_writer_test_output.npy' )

        # Write it...
        opWriter.write()
        
        opRead = OpInputDataReader( graph=graph )
        opRead.FilePath.setValue( opWriter.Filepath.value )
        expected_data = data.view(numpy.ndarray)
        read_data = opRead.Output[:].wait()
        assert (read_data == expected_data).all(), "Read data didn't match exported data!"

if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)

