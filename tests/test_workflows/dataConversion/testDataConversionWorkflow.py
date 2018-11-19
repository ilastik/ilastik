from __future__ import print_function
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
#           http://ilastik.org/license.html
###############################################################################
import os
import sys
import imp
import numpy
import tempfile

from lazyflow.graph import Graph
from lazyflow.operators.ioOperators import OpStackLoader
from lazyflow.operators.opReorderAxes import OpReorderAxes

import ilastik
from lazyflow.utility.timer import timeLogged


import logging
logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)


class TestDataConversionWorkflow(object):
    dir = tempfile.mkdtemp()
    PROJECT_FILE = os.path.join(dir, 'test_project.ilp')
    # SAMPLE_DATA = os.path.split(__file__)[0] + '/synapse_small.npy'

    @classmethod
    def setup_class(cls):
        print('starting setup...')

        if hasattr(cls, 'SAMPLE_DATA'):
            cls.using_random_data = False
        else:
            cls.using_random_data = True
            cls.create_random_tst_data()

        print('looking for ilastik.py...')
        # Load the ilastik startup script as a module.
        # Do it here in setupClass to ensure that it isn't loaded more than once.
        ilastik_entry_file_path = os.path.join(os.path.split(os.path.realpath(ilastik.__file__))[0], "../ilastik.py")
        if not os.path.exists(ilastik_entry_file_path):
            raise RuntimeError("Couldn't find ilastik.py startup script: {}".format(ilastik_entry_file_path))

        cls.ilastik_startup = imp.load_source('ilastik_startup', ilastik_entry_file_path)

    @classmethod
    def teardown_class(cls):
        # Clean up: Delete any test files we generated
        removeFiles = [TestDataConversionWorkflow.PROJECT_FILE]
        if cls.using_random_data:
            removeFiles += [TestDataConversionWorkflow.SAMPLE_DATA]

        for f in removeFiles:
            try:
                os.remove(f)
            except:  # noqa
                pass

    @classmethod
    def create_random_tst_data(cls):
        cls.SAMPLE_DATA = os.path.join(cls.dir, 'random_data.npy')
        cls.data = numpy.random.random((1, 200, 200, 50, 1))
        cls.data *= 256
        numpy.save(cls.SAMPLE_DATA, cls.data.astype(numpy.uint8))

        cls.SAMPLE_MASK = os.path.join(cls.dir, 'mask.npy')
        cls.data = numpy.ones((1, 200, 200, 50, 1))
        numpy.save(cls.SAMPLE_MASK, cls.data.astype(numpy.uint8))

    @timeLogged(logger)
    def testLotsOfOptions(self):
        # NOTE: In this test, cmd-line args to tests will also end up getting "parsed" by ilastik.
        #       That shouldn't be an issue, since the pixel classification workflow ignores unrecognized options.
        #       See if __name__ == __main__ section, below.
        args = []
        args.append("--new_project=" + self.PROJECT_FILE)
        args.append("--workflow=DataConversionWorkflow")
        args.append("--headless")
        # args.append( "--sys_tmp_dir=/tmp" )

        # Batch export options
        # If we were actually launching from the command line, 'png sequence' would be in quotes...
        args.append('--output_format=png sequence')
        args.append("--output_filename_format={dataset_dir}/{nickname}_converted_{slice_index}.png")
        args.append("--export_dtype=uint8")
        args.append("--output_axis_order=ztyxc")

        args.append("--pipeline_result_drange=(0,2)")
        args.append("--export_drange=(0,255)")

        args.append("--cutout_subregion=[(0,50,50,0,0), (1, 150, 150, 50, 1)]")

        # Input args
        args.append("--input_axes=ztyxc")
        args.append(self.SAMPLE_DATA)

        sys.argv = ['ilastik.py']  # Clear the existing commandline args so it looks like we're starting fresh.
        sys.argv += args

        # Start up the ilastik.py entry script as if we had launched it from the command line
        # This will execute the batch mode script
        self.ilastik_startup.main()

        output_path = self.SAMPLE_DATA[:-4] + "_converted_{slice_index}.png"
        globstring = output_path.format(slice_index=999)
        globstring = globstring.replace('999', '*')

        opReader = OpStackLoader(graph=Graph())
        opReader.SequenceAxis.setValue('t')
        opReader.globstring.setValue(globstring)

        # (The OpStackLoader produces tzyxc order.)
        opReorderAxes = OpReorderAxes(graph=Graph())
        opReorderAxes.AxisOrder.setValue('ztyxc')
        opReorderAxes.Input.connect(opReader.stack)

        try:
            readData = opReorderAxes.Output[:].wait()

            # Check basic attributes
            assert readData.shape[:-1] == self.data[0:1, 50:150, 50:150,
                                                    0:50, 0:1].shape[:-1]  # Assume channel is last axis
            assert readData.shape[-1] == 1, "Wrong number of channels.  Expected 1, got {}".format(readData.shape[-1])
        finally:
            # Clean-up.
            opReorderAxes.cleanUp()
            opReader.cleanUp()
