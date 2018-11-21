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
import vigra
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


def detect_edges(img):
    img = img.squeeze().astype(numpy.uint64)
    # transpose dimensions, in order to have sensible 2D images to perform edge detection on
    img = img.transpose(numpy.argsort(img.shape))

    def detect(img):
        if len(img.shape) > 2:
            return numpy.stack([detect(i) for i in img])

        return vigra.analysis.regionImageToEdgeImage(img)

    return detect(img)


class TestAxesOrderPreservation(object):
    dir = tempfile.mkdtemp()
    # dir = os.path.expanduser('~/Desktop/tmp')  # uncommmet for easier debugging
    PROJECT_FILE_BASE = os.path.join(os.path.dirname(__file__), '..', '..', 'data')

    @classmethod
    def setup_class(cls):
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
        cls.ilastik_entry_file_path = os.path.join(os.path.split(
            os.path.realpath(ilastik.__file__))[0], "../ilastik.py")
        if not os.path.exists(cls.ilastik_entry_file_path):
            raise RuntimeError(
                "Couldn't find ilastik.py startup script: {}".format(
                    cls.ilastik_entry_file_path))

        cls.ilastik_startup = imp.load_source(
            'ilastik_startup', cls.ilastik_entry_file_path)

        cls.created_data = []

    @classmethod
    def teardown_class(cls):
        # Clean up: Delete all unzipped test projects
        for f in cls.unzipped_project_files + cls.created_data:
            file = os.path.join(cls.PROJECT_FILE_BASE, f)
            try:
                os.remove(file)
            except Exception as e:
                print('Failed to remove file {} due to the error: {}'.format(file, e))

            if cls.untested_projects:
                warnings.warn('untested projects detected: {}'.format(
                    ', '.join(cls.untested_projects)))

    @classmethod
    def create_simple_input(cls, name, data):
        """
        Creates a file named '{name}_{input_axes}' from 'data' with axis order 'input_axes'


        Args:
            name (str): first part of the name for created h5 file (without '.h5')
            data (numpy.ndarray, Vigra.VigraArray): data (for numpy axis order is 'tczyx')
            input_axes (str): desired axis order. Is added to the name.
        """
        write_at = os.path.join(cls.PROJECT_FILE_BASE, 'inputdata', name + '_' + 'simple.h5')
        if not os.path.exists(write_at):
            assert isinstance(data, vigra.VigraArray)

            vigra.writeHDF5(data, write_at, 'simple')
            cls.created_data.append(write_at)

        return write_at

    @classmethod
    def create_input(cls, filepath, input_axes, outmin=None, outmax=None, dtype=None):
        """ Creates a file from the data at 'filepath' that has 'input_axes' """
        basename = os.path.basename(filepath)
        reader = OpInputDataReader(graph=Graph())
        assert os.path.exists(filepath), '{} not found'.format(filepath)
        reader.FilePath.setValue(os.path.abspath(filepath))

        writer = OpFormattedDataExport(parent=reader)
        if outmin is not None:
            writer.ExportMin.setValue(outmin)
        if outmax is not None:
            writer.ExportMax.setValue(outmax)
        if dtype is not None:
            writer.ExportDtype.setValue(dtype)

        writer.OutputAxisOrder.setValue(input_axes)
        writer.Input.connect(reader.Output)
        writer.OutputFilenameFormat.setValue(os.path.join(
            cls.dir, basename.split('.')[0] + '_' + input_axes))
        writer.TransactionSlot.setValue(True)
        input_path = writer.ExportPath.value
        writer.run_export()

        return input_path

    def compare_results(self, opReaderResult, compare_path, input_axes, post_process=None,
                        max_mse=None, max_part_uneqaul=None, add_c=True):
        if os.path.exists(compare_path):
            result = opReaderResult.Output[:].wait()

            if add_c and 'c' not in input_axes:
                input_axes += 'c'

            opReaderCompare = OpInputDataReader(graph=Graph())
            opReaderCompare.FilePath.setValue(compare_path)
            opReorderCompare = OpReorderAxes(parent=opReaderCompare)
            opReorderCompare.Input.connect(opReaderCompare.Output)
            opReorderCompare.AxisOrder.setValue(input_axes)

            compare = opReorderCompare.Output[:].wait()

            assert result.shape == compare.shape, (result.shape, compare.shape)

            if post_process:
                result = post_process(result)
                compare = post_process(compare)

            # for easy debugging:
            # -----------------------------------------------------------------
            # import matplotlib.pyplot as plt

            # res = result.squeeze()
            # comp = compare.squeeze()
            # if len(res.shape) > 2:
            #     res = res.reshape(-1, max(res.shape))
            #     comp = comp.reshape(-1, max(comp.shape))

            # plt.figure()
            # plt.imshow(res)
            # plt.title(f'res {result.shape}')
            # plt.colorbar()
            # plt.figure()
            # plt.imshow(comp)
            # plt.title('comp')
            # plt.colorbar()
            # plt.figure()
            # plt.imshow(res - comp)
            # plt.title('diff')
            # plt.colorbar()
            # plt.show()
            # -----------------------------------------------------------------

            if max_mse:
                assert max_mse > numpy.mean(numpy.square(result - compare)), \
                    numpy.mean(numpy.square(result - compare))
            elif max_part_uneqaul:
                assert max_part_uneqaul > numpy.mean(~numpy.isclose(result, compare)), \
                    numpy.mean(~numpy.isclose(result, compare))
            else:
                assert numpy.allclose(result, compare), f'{result.shape}, {compare.shape}'
        else:
            writer = OpFormattedDataExport(graph=Graph())
            writer.Input.connect(opReaderResult.Output)

            writer.OutputFilenameFormat.setValue(compare_path)
            writer.TransactionSlot.setValue(True)
            writer.run_export()
            warnings.warn(f'created comparison data: {compare_path} with axis order {input_axes}')

    def test_pixel_classification(self):
        options = []
        options.append((['2d'], ['xy', 'yx']))
        options.append((['2d', '2d3c'], ['cxy', 'yxc', 'xyc', 'ycx']))
        options.append((['3d', '3d1c', '3d2c'], ['xyzc', 'czyx']))
        options.append((['5t2d1c', '5t2d2c'], ['tyxc', 'txyc', 'xytc']))
        options.append((['5t3d2c'], ['tzyxc', 'ztxyc', 'xyztc']))

        for combination in options:
            for dims, order in itertools.product(*combination):
                yield self._test_pixel_classification, dims, order

    @timeLogged(logger)
    def _test_pixel_classification(self, dims, input_axes):
        # NOTE: In this test, cmd-line args to test runner will also end up
        #       getting "parsed" by ilastik. That shouldn't be an issue, since
        #       the pixel classification workflow ignores unrecognized options.
        #       See if __name__ == __main__ section, below.
        project = 'PixelClassification' + dims + '.ilp'
        try:
            self.untested_projects.remove(project)
        except ValueError:
            pass

        project_file = os.path.join(self.PROJECT_FILE_BASE, project)

        if not os.path.exists(project_file):
            raise IOError('project file "{}" not found'.format(
                project_file))

        compare_path = os.path.join(self.dir, f'PixelClassification{dims}_compare')
        output_path = compare_path.replace('_compare', f'_{input_axes}_result')

        args = []
        args.append("--headless")
        args.append("--project=" + project_file)

        # Batch export options
        # If we were actually launching from the command line, 'png sequence'
        # would be in quotes...
        # args.append('--output_format=png sequence')
        args.append("--export_source=Simple Segmentation")
        args.append(
            "--output_filename_format=" + output_path)
        args.append(
            "--output_format=hdf5")
        args.append("--export_dtype=uint8")
        # args.append("--output_axis_order=")

        args.append("--pipeline_result_drange=(0,2)")
        args.append("--export_drange=(0,2)")

        # Input args
        args.append("--input_axes={}".format(input_axes))
        input_source_path = os.path.join(self.PROJECT_FILE_BASE, 'inputdata',
                                         '{}.h5'.format(dims))
        input_path = self.create_input(input_source_path, input_axes)
        args.append(input_path)

        # Clear the existing commandline args so it looks like we're starting fresh.
        sys.argv = ['ilastik.py']
        sys.argv += args

        # Start up the ilastik.py entry script as if we had launched it from the command line
        # This will execute the batch mode script
        self.ilastik_startup.main()

        output_path += '.h5'
        compare_path += '.h5'

        opReaderResult = OpInputDataReader(graph=Graph())
        opReaderResult.FilePath.setValue(output_path)

        if 'c' in input_axes:
            assert input_axes == ''.join(opReaderResult.Output.meta.getAxisKeys()), \
                ''.join(opReaderResult.Output.meta.getAxisKeys())
        else:
            assert input_axes == ''.join([a for a in opReaderResult.Output.meta.getAxisKeys() if a != 'c']), \
                ''.join(opReaderResult.Output.meta.getAxisKeys())

        self.compare_results(opReaderResult, compare_path, input_axes, max_mse=0.001)

    def test_autocontext(self):
        options = []
        # todo: single channel, same as for autocontext
        # options.append((['2d'], ['xy', 'yx']))
        options.append((['2d3c'], ['cxy', 'yxc', 'xyc', 'ycx']))
        options.append((['5t2d1c'], ['tyxc', 'txcy', 'cxyt']))

        for combination in options:
            for dims, order in itertools.product(*combination):
                yield self._test_autocontext, dims, order

    @timeLogged(logger)
    def _test_autocontext(self, dims, input_axes):
        # NOTE: In this test, cmd-line args to test runner will also end up
        #       getting "parsed" by ilastik. That shouldn't be an issue, since
        #       the pixel classification workflow ignores unrecognized options.
        #       See if __name__ == __main__ section, below.
        project = 'Autocontext' + dims + '.ilp'
        try:
            self.untested_projects.remove(project)
        except ValueError:
            pass

        project_file = os.path.join(self.PROJECT_FILE_BASE, project)

        if not os.path.exists(project_file):
            raise IOError('project file "{}" not found'.format(
                project_file))

        compare_path = os.path.join(self.dir, f'Autocontext{dims}_compare')
        output_path = compare_path.replace('_compare', f'_{input_axes}_result')

        args = []
        args.append("--headless")
        args.append("--project=" + project_file)

        # Batch export options
        # If we were actually launching from the command line, 'png sequence'
        # would be in quotes...
        # args.append('--output_format=png sequence')
        args.append("--export_source=probabilities all stages")
        args.append(
            "--output_filename_format=" + output_path)
        args.append(
            "--output_format=hdf5")

        # Input args
        args.append("--input_axes={}".format(input_axes))
        input_source_path = os.path.join(self.PROJECT_FILE_BASE, 'inputdata', f'{dims}.h5')
        input_path = self.create_input(input_source_path, input_axes, 0, 255, 'uint8')
        args.append(input_path)

        # Clear the existing commandline args so it looks like we're starting fresh.
        sys.argv = ['ilastik.py']
        sys.argv += args

        # Start up the ilastik.py entry script as if we had launched it from the command line
        # This will execute the batch mode script
        self.ilastik_startup.main()

        output_path += '.h5'
        compare_path += '.h5'

        opReaderResult = OpInputDataReader(graph=Graph())
        opReaderResult.FilePath.setValue(output_path)

        if 'c' in input_axes:
            assert input_axes == ''.join(opReaderResult.Output.meta.getAxisKeys()), \
                ''.join(opReaderResult.Output.meta.getAxisKeys())
        else:
            assert input_axes == ''.join([a for a in opReaderResult.Output.meta.getAxisKeys() if a != 'c']), \
                ''.join(opReaderResult.Output.meta.getAxisKeys())

        self.compare_results(opReaderResult, compare_path, input_axes)

    def test_object_classification(self):
        options = []
        options.append((['2d', '2d3c'], ['wPred', 'wSeg'], ['yxc', 'xcy', 'cyx']))
        options.append((['5t2d1c', '5t2d2c'], ['wPred', 'wSeg'], ['tyxc', 'txyc', 'xytc']))
        options.append((['5t3d2c'], ['wPred', 'wSeg'], ['tzyxc', 'xztyc', 'tczyx', 'cztxy']))

        for combination in options:
            for dims, variant, order in itertools.product(*combination):
                yield self._test_object_classification, dims, variant, order

    @timeLogged(logger)
    def _test_object_classification(self, dims, variant, input_axes):
        project = f'ObjectClassification{dims}_{variant}.ilp'
        try:
            self.untested_projects.remove(project)
        except ValueError:
            pass

        project_file = os.path.join(self.PROJECT_FILE_BASE, project)

        if not os.path.exists(project_file):
            raise IOError(f'project file "{project_file}" not found')

        compare_path = os.path.join(self.dir, f'Object_Predictions_{dims}_{variant}_compare')
        output_path = compare_path.replace('_compare', f'_{input_axes}_result')

        args = [
            '--headless',
            '--project', project_file,
            # Batch export options
            '--export_source', 'Object Predictions',
            '--output_filename_format', output_path,
            '--output_format', 'hdf5',
            '--export_dtype', 'uint8',
            '--pipeline_result_drange', '(0,255)',
            '--export_drange', '(0,255)',
            # Input args
            '--input_axes', input_axes,
            '--raw_data',
            self.create_input(os.path.join(self.PROJECT_FILE_BASE, 'inputdata', f'{dims}.h5'), input_axes)
        ]

        if variant == 'wPred':
            args.append('--prediction_maps')
            args.append(self.create_input(
                os.path.join(self.PROJECT_FILE_BASE, 'inputdata', f'{dims}_Probabilities.h5'),
                input_axes))
        elif variant == 'wSeg':
            args.append('--segmentation_image')
            args.append(self.create_input(
                os.path.join(self.PROJECT_FILE_BASE, 'inputdata', f'{dims}_Binary_Segmentation.h5'),
                input_axes))
        else:
            raise NotImplementedError(f'unknown variant: {variant}')

        # Start up the ilastik.py entry script as if we had launched it from the command line
        # This will execute the batch mode script
        sys.argv = ['ilastik.py'] + args
        self.ilastik_startup.main()
        output_path += '.h5'
        compare_path += '.h5'

        opReaderResult = OpInputDataReader(graph=Graph())
        opReaderResult.FilePath.setValue(output_path)

        self.compare_results(opReaderResult, compare_path, input_axes)

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

        compare_path = os.path.join(self.dir, f'Multicut_Segmentation{dims}_compare')
        output_path = compare_path.replace('_compare', f'_{input_axes}_result')

        args = []
        args.append("--headless")
        args.append("--project=" + project_file)

        # Batch export options
        # If we were actually launching from the command line, 'png sequence'
        # would be in quotes...
        # args.append('--output_format=png sequence')
        args.append('--export_source=Multicut Segmentation')
        args.append(
            "--output_filename_format=" + output_path)
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

        output_path += '.h5'
        compare_path += '.h5'

        opReaderResult = OpInputDataReader(graph=Graph())
        opReaderResult.FilePath.setValue(output_path)

        self.compare_results(opReaderResult, compare_path, input_axes, post_process=detect_edges,
                             max_part_uneqaul=0.02)

    def test_counting(self):
        options = []
        # todo: add 2d[1c] counting project (missing channel leads to 'no image data' error)
        # options.append((['2d'], ['xy', 'yx']))
        # options.append((['2d1c', '2d3c'], ['yxc', 'cxy']))  # 'xyc', 'cxy', 'ycx
        options.append((['2d3c'], ['yxc', 'xyc', 'cxy', 'ycx']))

        for combination in options:
            for dims, order in itertools.product(*combination):
                yield self._test_counting, dims, order

    @timeLogged(logger)
    def _test_counting(self, dims, input_axes):
        project = f'CellDensityCounting{dims}.ilp'
        try:
            self.untested_projects.remove(project)
        except ValueError:
            pass

        project_file = os.path.join(self.PROJECT_FILE_BASE, project)

        if not os.path.exists(project_file):
            raise IOError('project file "{}" not found'.format(
                project_file))

        compare_path = os.path.join(self.dir, f'Counts{dims}_compare')
        output_path = compare_path.replace('_compare', f'_{input_axes}_result')

        args = []
        args.append("--headless")
        args.append("--project=" + project_file)

        # Batch export options
        # If we were actually launching from the command line, 'png sequence'
        # would be in quotes...
        # args.append('--output_format=png sequence')
        args.append("--export_source=Probabilities")
        args.append(
            "--output_filename_format=" + output_path)
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

        output_path += '.h5'
        compare_path += '.h5'

        opReaderResult = OpInputDataReader(graph=Graph())
        opReaderResult.FilePath.setValue(output_path)

        self.compare_results(opReaderResult, compare_path, input_axes, max_mse=0.001)

    # todo: exchange nonsense data and labels in tracking projects (wBin)
    def test_tracking_with_learning(self):
        options = []
        # test configurations
        options.append((['5t2d'], ['_wPred'], ['tyx', 'txy', 'xyt']))
        options.append((['5t2d1c'], ['_wBin', '_wPred'], ['tyxc', 'txyc', 'xytc']))
        options.append((['5t2d2c'], ['_wBin'], ['tyxc', 'txyc', 'xytc']))
        options.append((['5t2d3c'], ['_wPred'], ['tyxc', 'txyc', 'xytc']))
        options.append((['5t3d'], ['_wPred'], ['tzyxc', 'xztyc']))
        options.append((['5t3d2c'], ['_wBin'], ['tzyxc', 'xztyc']))

        for combination in options:
            for dims, variant, order in itertools.product(*combination):
                yield self._test_tracking_with_learning, dims, variant, order

    @timeLogged(logger)
    def _test_tracking_with_learning(self, dims, variant, input_axes):
        project = 'TrackingwLearning' + dims + variant + '.ilp'
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
        args.append("--export_source=Tracking-Result")
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
        if 'wPred' in variant:
            raw = numpy.zeros((5, 3, 10, 20, 30), dtype=numpy.uint8)
            for t in range(5):
                raw[t, :, 0:5 + t, 9 + t:15 + t, 5:10] = 200
                raw[t, :, 0:5 + t, t:4 + t, 20:25] = 240

            raw = vigra.VigraArray(raw, axistags=vigra.defaultAxistags('tczyx'))
            pred = numpy.zeros((5, 1, 10, 20, 30), dtype=numpy.float32)
            for t in range(5):
                pred[t, :, 0:5 + t, 9 + t:15 + t, 5:10] = .8
                pred[t, :, 0:5 + t, t:4 + t, 20:25] = .9

            pred = vigra.VigraArray(pred, axistags=vigra.defaultAxistags('tczyx'))

            if '2d' in dims:
                # remove z
                raw = raw[:, :, 0]
                pred = pred[:, :, 0]

            if 'c' in dims:
                # select only #c channels
                c = int(dims[dims.find('c') - 1])
                raw = raw[:, :c]
            else:
                # remove c
                raw = raw[:, 0]

            input_source_path1 = self.create_simple_input(dims, raw)  # create data linked in test project
            input_source_path1 = self.create_input(input_source_path1, input_axes)  # create reordered test data

            project_data_path2 = self.create_simple_input(dims + '_Probabilities',
                                                          pred)  # create data linked in test project
            input_source_path2 = self.create_input(project_data_path2, input_axes)  # create reordered test data

            args.append("--raw_data=" + input_source_path1)
            args.append("--prediction_maps=" + input_source_path2)
        elif 'wBin' in variant:
            input_source_path1 = os.path.join(self.PROJECT_FILE_BASE, 'inputdata',
                                              '{}.h5'.format(dims))
            input_source_path1 = self.create_input(input_source_path1, input_axes)
            args.append("--raw_data=" + input_source_path1)
            input_source_path2 = os.path.join(self.PROJECT_FILE_BASE, 'inputdata',
                                              '{}_Binary_Segmentation.h5'
                                              .format(dims))
            input_path2 = self.create_input(input_source_path2, input_axes)
            args.append("--binary_image=" + input_path2)
        else:
            raise NotImplementedError('variant {} unknown'.format(variant))

        # Clear the existing commandline args so it looks like we're starting fresh.
        sys.argv = ['ilastik.py']
        sys.argv += args

        # Start up the ilastik.py entry script as if we had launched it from the command line
        # This will execute the batch mode script
        self.ilastik_startup.main()

        output_path = input_source_path1.replace('.', '_result{}.'.format(variant))

        opReaderResult = OpInputDataReader(graph=Graph())
        opReaderResult.FilePath.setValue(output_path)

        compare_name = os.path.abspath(os.path.join(self.dir, f'{dims}{variant}_Tracking-Result.h5'))

        if variant == '_wPred':
            self.compare_results(opReaderResult, compare_name, input_axes)
        else:
            self.compare_results(opReaderResult, compare_name, input_axes, post_process=detect_edges,
                                 max_part_uneqaul=0.01)
