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
import warnings
import zipfile

from lazyflow.graph import Graph
from lazyflow.operators.ioOperators import OpInputDataReader
from lazyflow.operators.ioOperators.opFormattedDataExport import \
    OpFormattedDataExport
from lazyflow.operators.opReorderAxes import OpReorderAxes
from lazyflow.utility.timer import timeLogged

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TestAxesOrderPreservation(object):
    dir = tempfile.mkdtemp()
    # dir = os.path.expanduser('~/Desktop/tmp')  # uncommmet for easier debugging
    PROJECT_FILE_BASE = os.path.join(os.path.dirname(__file__), '..', '..', 'data')

    @classmethod
    def setupClass(cls):
        print('starting setup...')
        print('unzipping project files...')
        projects = zipfile.ZipFile(os.path.join(cls.PROJECT_FILE_BASE,
                                                'test_projects.zip'),
                                   mode='r')

        projects.extractall(path=cls.PROJECT_FILE_BASE)
        cls.unzipped_project_files = projects.namelist()
        cls.untested_projects = list(cls.unzipped_project_files)
        print('unzipped projects: ' + ', '.join(cls.unzipped_project_files))
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

    @classmethod
    def teardownClass(cls):
        # Clean up: Delete all unzipped test projects
        for f in cls.unzipped_project_files:
            file = os.path.join(cls.PROJECT_FILE_BASE, f)
            try:
                os.remove(file)
            except Exception as e:
                print('Failed to remove file {} due to the error: {}'
                      .format(file, e))

        if cls.untested_projects:
            warnings.warn('untested projects detected: {}'.format(
                ', '.join(cls.untested_projects)))

    @classmethod
    def create_input(cls, filepath, input_axes):
        """
            creates an file from the data at 'filepath' that has 'input_axes'
        """
        basename = os.path.basename(filepath)
        graph = Graph()
        reader = OpInputDataReader(graph=graph)
        assert os.path.exists(filepath), '{} not found'.format(filepath)
        reader.FilePath.setValue(os.path.abspath(filepath))

        writer = OpFormattedDataExport(parent=reader)
        writer.OutputAxisOrder.setValue(input_axes)
        writer.Input.connect(reader.Output)
        writer.OutputFilenameFormat.setValue(os.path.join(
            cls.dir, basename.split('.')[0] + '_' + input_axes))
        writer.TransactionSlot.setValue(True)
        input_path = writer.ExportPath.value
        writer.run_export()

        return input_path

    def compare_results(self, opReaderResult, compare_name, input_axes):
        if os.path.exists(compare_name):
            result = opReaderResult.Output[:].wait()

            opReaderCompare = OpInputDataReader(graph=Graph())
            opReaderCompare.FilePath.setValue(compare_name)
            opReorderCompare = OpReorderAxes(parent=opReaderCompare)
            opReorderCompare.Input.connect(opReaderCompare.Output)
            opReorderCompare.AxisOrder.setValue(input_axes)

            compare = opReorderCompare.Output[:].wait()

            assert numpy.allclose(result, compare), f'{result.shape}, {compare.shape}'
        else:
            writer = OpFormattedDataExport(graph=Graph())
            writer.Input.connect(opReaderResult.Output)

            writer.OutputFilenameFormat.setValue(compare_name)
            writer.TransactionSlot.setValue(True)
            writer.run_export()
            warnings.warn(f'created comparison data: {compare_name} with axis order {input_axes}')

    def test_pixel_classification(self):
        options = []
        options.append((['2d'], ['xy', 'yx']))
        options.append((['2d', '2d3c'], ['cxy', 'yxc', 'xyc', 'ycx']))
        options.append((['3d', '3d1c', '3d2c'], ['xyzc', 'czyx']))
        options.append((['5t2d1c', '5t2d2c'], ['tyxc', 'txyc', 'xytc']))
        options.append((['5t3d2c'], ['tzyxc', 'ztxyc', 'xyztc']))

        for combination in options:
            for testcase, order in itertools.product(*combination):
                yield self._test_pixel_classification, testcase, order

    @timeLogged(logger)
    def _test_pixel_classification(self, testcase, input_axes):
        # NOTE: In this test, cmd-line args to nosetests will also end up
        #       getting "parsed" by ilastik. That shouldn't be an issue, since
        #       the pixel classification workflow ignores unrecognized options.
        #       See if __name__ == __main__ section, below.
        project = 'PixelClassification' + testcase + '.ilp'
        try:
            self.untested_projects.remove(project)
        except ValueError:
            pass

        project_file = os.path.join(self.PROJECT_FILE_BASE, project)

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
        input_source_path = os.path.join(self.PROJECT_FILE_BASE, 'inputdata',
                                         '{}.h5'.format(testcase))
        input_path = self.create_input(input_source_path, input_axes)
        args.append(input_path)

        # Clear the existing commandline args so it looks like we're starting fresh.
        sys.argv = ['ilastik.py']
        sys.argv += args

        # Start up the ilastik.py entry script as if we had launched it from the command line
        # This will execute the batch mode script
        self.ilastik_startup.main()

        output_path = input_path.replace('.', '_result.')

        opReaderResult = OpInputDataReader(graph=Graph())
        opReaderResult.FilePath.setValue(output_path)

        if 'c' in input_axes:
            assert input_axes == ''.join(opReaderResult.Output.meta.getAxisKeys()), \
                ''.join(opReaderResult.Output.meta.getAxisKeys())
        else:
            assert input_axes == ''.join([a for a in opReaderResult.Output.meta.getAxisKeys() if a != 'c']), \
                ''.join(opReaderResult.Output.meta.getAxisKeys())

        compare_name = os.path.abspath(os.path.join(self.dir, f'PixelClassification_{testcase}.h5'))

        self.compare_results(opReaderResult, compare_name, input_axes)

    def test_object_classification(self):
        options = []
        options.append((['2d', '2d3c'], ['_wPred', '_wSeg'], ['yxc', 'xcy', 'cyx']))
        options.append((['5t2d1c', '5t2d2c'], ['_wPred', '_wSeg'], ['tyxc', 'txyc', 'xytc']))
        options.append((['5t3d2c'], ['_wPred', '_wSeg'], ['tzyxc', 'xztyc', 'tczyx', 'cztxy']))

        for combination in options:
            for dims, variant, order in itertools.product(*combination):
                yield self._test_object_classification, dims, variant, order

    @timeLogged(logger)
    def _test_object_classification(self, dims, variant, input_axes):
        project = 'ObjectClassification' + dims + variant + '.ilp'
        try:
            self.untested_projects.remove(project)
        except ValueError:
            pass

        project_file = os.path.join(self.PROJECT_FILE_BASE, project)

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
        args.append("--export_source=Object Predictions")
        args.append(
            "--output_filename_format=" + self.dir + "/{nickname}_result" +
            variant)
        args.append(
            "--output_format=hdf5")
        args.append("--export_dtype=uint8")
        # args.append("--output_axis_order=" + input_axes)

        args.append("--pipeline_result_drange=(0,255)")
        args.append("--export_drange=(0,255)")

        # Input args
        args.append("--input_axes={}".format(input_axes))
        input_source_path1 = os.path.join(self.PROJECT_FILE_BASE, 'inputdata',
                                          '{}.h5'.format(dims))
        input_path1 = self.create_input(input_source_path1, input_axes)
        args.append("--raw_data=" + input_path1)
        if 'wPred' in variant:
            input_source_path2 = os.path.join(self.PROJECT_FILE_BASE,
                                              'inputdata',
                                              '{}_Probabilities.h5'
                                              .format(dims))
            input_path2 = self.create_input(input_source_path2, input_axes)
            args.append("--prediction_maps=" + input_path2)
        elif 'wSeg' in variant:
            input_source_path2 = os.path.join(self.PROJECT_FILE_BASE,
                                              'inputdata',
                                              '{}_Binary Segmentation.h5'
                                              .format(dims))
            input_path2 = self.create_input(input_source_path2, input_axes)
            args.append("--segmentation_image=" + input_path2)
        else:
            raise NotImplementedError('variant {} unknown'.format(variant))

        # Clear the existing commandline args so it looks like we're starting fresh.
        sys.argv = ['ilastik.py']
        sys.argv += args

        # Start up the ilastik.py entry script as if we had launched it from the command line
        # This will execute the batch mode script
        self.ilastik_startup.main()

        output_path = input_path1.replace('.', '_result{}.'.format(variant))

        opReaderResult = OpInputDataReader(graph=Graph())
        opReaderResult.FilePath.setValue(output_path)
        result = opReaderResult.Output[:].wait()

        compare_name = os.path.join(self.PROJECT_FILE_BASE, 'inputdata',
                                    '{}_Object Predictions.h5/exported_data'
                                    .format(dims + variant))
        compare_name = os.path.abspath(compare_name)
        opReaderCompare = OpInputDataReader(graph=Graph())
        opReaderCompare.FilePath.setValue(compare_name)
        opReorderCompare = OpReorderAxes(parent=opReaderCompare)
        opReorderCompare.Input.connect(opReaderCompare.Output)

        opReorderCompare.AxisOrder.setValue(input_axes)
        compare = opReorderCompare.Output[:].wait()

        assert numpy.allclose(result, compare)

    def test_boundarybased_segmentation_with_multicut(self):
        options = []
        options.append((['3d'], ['xyz', 'zcyx', 'xycz', 'yxcz']))
        options.append((['3d1c'], ['zyxc', 'xyzc', 'cxzy']))
        options.append((['3d2c'], ['zyxc', 'xcyz', 'czxy']))

        for combination in options:
            for dims, order in itertools.product(*combination):
                yield self._test_boundarybased_segmentation_with_multicut, \
                    dims, order

    @timeLogged(logger)
    def _test_boundarybased_segmentation_with_multicut(self, dims, input_axes):
        project = f'Boundary-basedSegmentationwMulticut{dims}.ilp'
        try:
            self.untested_projects.remove(project)
        except ValueError:
            pass

        project_file = os.path.join(self.PROJECT_FILE_BASE, project)

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
        args.append("--export_source=Multicut Segmentation")
        args.append(
            "--output_filename_format=" + self.dir + "/{nickname}_result")
        args.append(
            "--output_format=hdf5")
        args.append("--export_dtype=uint8")
        # args.append("--output_axis_order=" + input_axes)

        args.append("--pipeline_result_drange=(0,255)")
        args.append("--export_drange=(0,255)")

        # Input args
        args.append("--input_axes={}".format(input_axes))
        input_source_path1 = os.path.join(self.PROJECT_FILE_BASE, 'inputdata',
                                          '{}.h5'.format(dims))
        input_path1 = self.create_input(input_source_path1, input_axes)
        args.append("--raw_data=" + input_path1)
        input_source_path2 = os.path.join(self.PROJECT_FILE_BASE, 'inputdata',
                                          '{}_Probabilities.h5'.format(dims))
        prob_axes = input_axes
        if 'c' not in input_axes:
            prob_axes += 'c'
        input_path2 = self.create_input(input_source_path2, prob_axes)
        args.append("--probabilities=" + input_path2)

        # Clear the existing commandline args so it looks like we're starting
        # fresh.
        sys.argv = ['ilastik.py']
        sys.argv += args

        # Start up the ilastik.py entry script as if we had launched it from
        # the command line
        # This will execute the batch mode script
        self.ilastik_startup.main()

        output_path = input_path1.replace('.', '_result.')

        opReaderResult = OpInputDataReader(graph=Graph())
        opReaderResult.FilePath.setValue(output_path)

        compare_name = os.path.join(self.PROJECT_FILE_BASE, 'inputdata',
                                    f'{dims}_Multicut Segmentation.h5/exported_data')

        self.compare_results(opReaderResult, compare_name, input_axes)

    def test_counting(self):
        options = []
        # todo: add 2d[1c] counting project: options.append((['2d'], ['xy', 'yx']))
        # options.append((['2d', '2d3c'], ['yxc', 'cxy']))  # 'xyc', 'cxy', 'ycx
        options.append((['2d3c'], ['yxc', 'cxy']))  # 'xyc', 'cxy', 'ycx

        for combination in options:
            for dims, order in itertools.product(*combination):
                yield self._test_counting, dims, order

    @timeLogged(logger)
    def _test_counting(self, dims, input_axes):
        project = 'CellDensityCounting' + dims + '.ilp'
        try:
            self.untested_projects.remove(project)
        except ValueError:
            pass

        project_file = os.path.join(self.PROJECT_FILE_BASE, project)

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
        args.append("--export_source=Probabilities")
        args.append(
            "--output_filename_format=" + self.dir + "/{nickname}_result")
        args.append(
            "--output_format=hdf5")
        args.append("--export_dtype=float32")
        args.append("--pipeline_result_drange=(0,1)")
        args.append("--export_drange=(0,1)")

        # Input args
        args.append("--input_axes={}".format(input_axes))
        input_source_path1 = os.path.join(self.PROJECT_FILE_BASE, 'inputdata',
                                          '{}.h5'.format(dims))
        input_path1 = self.create_input(input_source_path1, input_axes)
        args.append("--raw_data=" + input_path1)

        # Clear the existing commandline args so it looks like we're starting fresh.
        sys.argv = ['ilastik.py']
        sys.argv += args

        # Start up the ilastik.py entry script as if we had launched it from the command line
        # This will execute the batch mode script
        self.ilastik_startup.main()

        output_path = input_path1.replace('.', '_result.')

        opReaderResult = OpInputDataReader(graph=Graph())
        opReaderResult.FilePath.setValue(output_path)

        compare_name = os.path.join(self.dir, 'inputdata', f'{dims}_count_Probabilities.h5/exported_data')

        self.compare_results(opReaderResult, compare_name, input_axes)


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
