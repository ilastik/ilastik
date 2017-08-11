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

import ilastik
import imp
import itertools
import logging
import numpy
import os
import sys
import tempfile

from lazyflow.graph import Graph
from lazyflow.operators.ioOperators import OpInputDataReader
from lazyflow.operators.ioOperators.opFormattedDataExport import \
    OpFormattedDataExport
from lazyflow.operators.opReorderAxes import OpReorderAxes
from lazyflow.utility.timer import timeLogged

logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)


class TestAxesOrderPreservation(object):
    dir = tempfile.mkdtemp()
    # os.path.expanduser('~/Desktop/tmp')
    PROJECT_FILE_BASE = '../../data/inputdata/*.ilp'

    @classmethod
    def setupClass(cls):
        print('starting setup...')
        print('looking for ilastik.py...')
        # Load the ilastik startup script as a module.
        # Do it here in setupClass to ensure that it isn't loaded more than
        # once.
        ilastik_entry_file_path = os.path.join(os.path.split(
            os.path.realpath(ilastik.__file__))[0], "../ilastik.py")
        if not os.path.exists(ilastik_entry_file_path):
            raise RuntimeError(
                "Couldn't find ilastik.py startup script: {}".format(
                    ilastik_entry_file_path))

        cls.ilastik_startup = imp.load_source(
            'ilastik_startup', ilastik_entry_file_path)

    def test_pixel_classification(self):
        options = []
        options.append((['2d', '2d3c'], ['yxc', 'xyc']))
        # + ['ycx', 'xcy', 'cyx', 'cxy']

        # options.append((['5t2d1c', '5t2d2c'], ['tyxc', 'txyc']))
        options.append((['5t3d2c'], ['tzyxc']))

        # options = cyx_options
        for combination in options:
            for testcase, order in itertools.product(*combination):
                print('testcase/order', testcase, order)
                yield self._test_pixel_classification, testcase, order

    @classmethod
    def create_input(cls, filepath, input_axes):
        """
            creates an file from the data at 'filepath' that has 'input_axes'
        """
        basename = os.path.basename(filepath)
        print('basename', basename)
        graph = Graph()
        reader = OpInputDataReader(graph=graph)
        reader.FilePath.setValue(os.path.abspath(filepath))
        print('reader axes', reader.Output.meta)

        # print('output reader', reader.Output[:].wait().shape)

        writer = OpFormattedDataExport(parent=reader)
        writer.OutputAxisOrder.setValue(input_axes)
        writer.Input.connect(reader.Output)
        writer.OutputFilenameFormat.setValue(os.path.join(
            cls.dir, basename.split('.')[0] + '_' + input_axes))
        # writer.OutputFormat.setValue(output_format)
        writer.TransactionSlot.setValue(True)
        input_path = writer.ExportPath.value
        writer.run_export()

        return input_path

    @timeLogged(logger)
    def _test_pixel_classification(self, testcase, input_axes):
        # NOTE: In this test, cmd-line args to nosetests will also end up
        #       getting "parsed" by ilastik. That shouldn't be an issue, since
        #       the pixel classification workflow ignores unrecognized options.
        #       See if __name__ == __main__ section, below.
        project_file = self.PROJECT_FILE_BASE.replace(
            '*', 'PixelClassification' + testcase)

        if not os.path.exists(project_file):
            raise IOError('project file "{}" not found'.format(
                project_file))

        args = []
        args.append("--headless")
        args.append("--project=" + project_file)

        # Batch export options
        # If we were actually launching from the command line, 'png sequence'
        # would be in quotes...
        # args.append('--output_format=png sequence')
        args.append("--export_source=Simple Segmentation")
        args.append(
            "--output_filename_format=" + self.dir + "/{nickname}_result")
        args.append(
            "--output_format=hdf5")
        args.append("--export_dtype=uint8")
        # args.append("--output_axis_order=")

        args.append("--pipeline_result_drange=(0,2)")
        args.append("--export_drange=(0,2)")

        # Input args
        args.append("--input_axes={}".format(input_axes))
        input_source_path = '../../data/inputdata/{}.h5'.format(testcase)
        input_path = self.create_input(input_source_path, input_axes)
        args.append(input_path)

        # Clear the existing commandline args so it looks like we're starting
        # fresh.
        sys.argv = ['ilastik.py']
        sys.argv += args

        # Start up the ilastik.py entry script as if we had launched it from
        # the command line
        # This will execute the batch mode script
        self.ilastik_startup.main()

        output_path = input_path.replace('.', '_result.')

        opReaderResult = OpInputDataReader(graph=Graph())
        opReaderResult.FilePath.setValue(output_path)
        result = opReaderResult.Output[:].wait()

        compare_name = '../../data/inputdata/{}_Simple Segmentation.h5/' \
                       'exported_data'.format(testcase)
        compare_name = os.path.abspath(compare_name)
        opReaderCompare = OpInputDataReader(graph=Graph())
        opReaderCompare.FilePath.setValue(compare_name)
        opReorderCompare = OpReorderAxes(parent=opReaderCompare)
        opReorderCompare.Input.connect(opReaderCompare.Output)
        opReorderCompare.AxisOrder.setValue(input_axes)

        compare = opReorderCompare.Output[:].wait()

        assert numpy.array_equal(result, compare)


if __name__ == "__main__":
    # make the program quit on Ctrl+C
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    import nose
    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nocapture")
    # Don't set the logging level to DEBUG.  Leave it alone.
    sys.argv.append("--nologcapture")
    nose.run(defaultTest=__file__)
