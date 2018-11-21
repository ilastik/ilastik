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
import tempfile
import shutil
import os
import numpy
import vigra
from lazyflow.graph import Graph
from ilastik.applets.dataSelection.opDataSelection import OpDataSelectionGroup, DatasetInfo

class TestOpDataSelectionGroup(object):

    @classmethod
    def setup_class(cls):
        cls.workingDir = tempfile.mkdtemp()
        cls.group1Data = [ ( os.path.join(cls.workingDir, 'A.npy'), numpy.random.random( (100,100, 1) ) ),
                           ( os.path.join(cls.workingDir, 'C.npy'), numpy.random.random( (100,100, 1) ) ) ]

        for name, data in cls.group1Data:
            numpy.save(name, data)

    @classmethod
    def teardown_class(cls):
        shutil.rmtree(cls.workingDir)

    def test(self):
        """
        Make sure that the dataset roles work the way we expect them to.
        """
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
        
        # Ensure that files opened by the inner operators are closed before we exit.
        op.DatasetGroup.resize(0)

    def testWeirdAxisInfos(self):
        """
        If we add a dataset that has the channel axis in the wrong place, 
        the operator should automatically transpose it to be last.
        """
        weirdAxisFilename = os.path.join(self.workingDir, 'WeirdAxes.npy')
        expected_data = numpy.random.random( (3,100,100) )
        numpy.save(weirdAxisFilename, expected_data)

        info = DatasetInfo()
        info.filePath = weirdAxisFilename
        info.axistags = vigra.defaultAxistags('cxy')
        
        graph = Graph()
        op = OpDataSelectionGroup(graph=graph, forceAxisOrder=False)
        op.WorkingDirectory.setValue( self.workingDir )
        op.DatasetRoles.setValue( ['RoleA'] )

        op.DatasetGroup.resize( 1 )
        op.DatasetGroup[0].setValue( info )

        assert op.ImageGroup[0].ready()
        
        data_from_op = op.ImageGroup[0][:].wait()
        
        assert data_from_op.dtype == expected_data.dtype 
        assert data_from_op.shape == expected_data.shape, (data_from_op.shape, expected_data.shape)
        assert (data_from_op == expected_data).all()

        # op.Image is a synonym for op.ImageGroup[0]
        assert op.Image.ready()
        assert (op.Image[:].wait() == expected_data).all()
        
        # Ensure that files opened by the inner operators are closed before we exit.
        op.DatasetGroup.resize(0)

    def testNoChannelAxis(self):
        """
        If we add a dataset that is missing a channel axis altogether, 
        the operator should automatically append a channel axis.
        """
        noChannelFilename = os.path.join(self.workingDir, 'NoChannelAxis.npy')
        noChannelData = numpy.random.random( (100,100) )
        numpy.save(noChannelFilename, noChannelData)

        info = DatasetInfo()
        info.filePath = noChannelFilename
        info.axistags = vigra.defaultAxistags('xy')
        
        graph = Graph()
        op = OpDataSelectionGroup( graph=graph )
        op.WorkingDirectory.setValue( self.workingDir )
        op.DatasetRoles.setValue( ['RoleA'] )

        op.DatasetGroup.resize( 1 )
        op.DatasetGroup[0].setValue( info )

        assert op.ImageGroup[0].ready()
        
        # Note that we expect a channel axis to be appended to the data.
        expected_data = noChannelData[:,:,numpy.newaxis]
        data_from_op = op.ImageGroup[0][:].wait()
        
        assert data_from_op.dtype == expected_data.dtype 
        assert data_from_op.shape == expected_data.shape
        assert (data_from_op == expected_data).all()

        # op.Image is a synonym for op.ImageGroup[0]
        assert op.Image.ready()
        assert (op.Image[:].wait() == expected_data).all()
        
        # Ensure that files opened by the inner operators are closed before we exit.
        op.DatasetGroup.resize(0)
