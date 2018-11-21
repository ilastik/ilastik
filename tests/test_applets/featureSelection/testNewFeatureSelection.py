import logging
import numpy
import time
import vigra
import pytest

from lazyflow.graph import Graph, OperatorWrapper

from ilastik.applets.featureSelection.opFeatureSelection import OpFeatureSelection
from lazyflow.operators.oldVigraOperators import OpFeatureSelection as OpFeatureSelectionOld

DEBUG = False

if DEBUG:
    import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)



class TestCompareOpFeatureSelectionToOld:

    def setup_method(self, method):
        # data = vigra.taggedView(numpy.random.random((2, 20, 25, 30, 3)), 'tzyxc')

        graph = Graph()
        graph_old = Graph()

        # Define operators
        opFeatures = OperatorWrapper(OpFeatureSelection, graph=graph)
        opFeaturesOld = OperatorWrapper(OpFeatureSelectionOld, graph=graph_old)

        opFeatures.InputImage.resize(1)
        opFeaturesOld.InputImage.resize(1)

        # Configure scales
        scales = [0.3, 0.7, 1, 1.6, 5.0]
        opFeatures.Scales.setValue(scales)
        opFeaturesOld.Scales.setValue(scales)

        # Configure feature types
        featureIds = ['GaussianSmoothing',
                      'LaplacianOfGaussian',
                      'StructureTensorEigenvalues',
                      'HessianOfGaussianEigenvalues',
                      'GaussianGradientMagnitude',
                      'DifferenceOfGaussians']
        opFeatures.FeatureIds.setValue(featureIds)
        opFeaturesOld.FeatureIds.setValue(featureIds)

        self.opFeatures = opFeatures
        self.opFeaturesOld = opFeaturesOld

    def compare(self, result, resultOld):
        assert result.shape == resultOld.shape
        assert numpy.allclose(result, resultOld, rtol=1.e-2, atol=1.e-4)

    def test_tiny(self):
        # Configure matrix
        tiny_sel = numpy.zeros((6, 5), dtype=bool)
        tiny_sel[0, 0] = True  # Gaussian
        tiny_sel[1, 2] = True  # L of G
        tiny_sel[2, 2] = True  # ST EVs
        tiny_sel[3, 1] = True  # H of G EVs
        tiny_sel[4, 2] = True  # GGM
        tiny_sel[5, 2] = True  # Diff of G

        self.opFeatures.SelectionMatrix.setValue(tiny_sel)
        self.opFeaturesOld.SelectionMatrix.setValue(tiny_sel)

        data = vigra.taggedView(numpy.resize(numpy.arange(64 * 7 * 3, dtype=numpy.float32), (1, 1, 6, 7, 3)), 'tzyxc')

        # Set input data
        self.opFeatures.InputImage[0].setValue(data)
        self.opFeaturesOld.InputImage[0].setValue(data)

        output = self.opFeatures.OutputImage[0]
        outputOld = self.opFeaturesOld.OutputImage[0]

        assert id(output) != id(outputOld)
        assert output.meta.shape == outputOld.meta.shape, (output.meta.shape, outputOld.meta.shape)
        assert output.meta.axistags == outputOld.meta.axistags
        for key in output.meta.keys():
            if key in ['description', 'channel_names']:
                continue
            if DEBUG and output.meta[key] != outputOld.meta[key]:
                print(f'{key}: {output.meta[key]}, {outputOld.meta[key]}\n')
            if output.meta[key] != outputOld.meta[key]:
                print(f'{key}: {output.meta[key]}, {outputOld.meta[key]}\n')
            assert output.meta[key] == outputOld.meta[key], key

        for roi in [
            [0, 0, slice(None), slice(None), slice(0, 3)],
            [0, 0, slice(None), slice(None), slice(3, 6)],
            [0, 0, slice(1, 5), slice(1, 6), slice(6, 7)],
            [0, 0, slice(1, 5), slice(None), slice(7, 8)],
            [0, 0, slice(None), slice(1, 6), slice(8, 11)],
            [0, 0, slice(None), slice(None), slice(11, 14)],
            [0, 0, slice(None), slice(None), slice(14, 15)],
            [0, 0, slice(None), slice(None), slice(15, 18)],
            [0, 0, slice(None), slice(None), slice(15, 18)],
            [0, 0, slice(None), slice(None), slice(18, 21)],
            [0, 0, slice(None), slice(None), slice(21, 24)],
        ]:
            result = output[roi].wait()
            resultOld = outputOld[roi].wait()
            yield self.compare, result, resultOld

    def test_output(self):
        self.opFeatures.InputImage[0].disconnect()

        # Configure selection matrix
        sel = numpy.zeros((6, 5), dtype=bool)
        sel[0, 1] = True  # Gaussian
        sel[1, 2] = True  # L of G
        sel[2, 3] = True  # ST EVs
        sel[3, 2] = True  # H of G EVs
        sel[4, 3] = True  # GGM
        sel[5, 2] = True  # Diff of G

        if DEBUG:
            # set vigra filter to compare to here
            scales = [1.6]
            vigra_fn = vigra.filters.gaussianSmoothing

        self.opFeatures.SelectionMatrix.setValue(sel)
        self.opFeatures.ComputeIn2d.setValue([False] * 6)
        self.opFeaturesOld.SelectionMatrix.setValue(sel)

        data = vigra.taggedView(
            numpy.resize(numpy.random.rand(2 * 18 * 19 * 20 * 3), (2, 18, 19, 20, 3)).astype(numpy.float32),
            'tzyxc')

        # Set input data
        self.opFeatures.InputImage[0].setValue(data)
        self.opFeaturesOld.InputImage[0].setValue(data)

        output = self.opFeatures.OutputImage[0]
        outputOld = self.opFeaturesOld.OutputImage[0]

        assert id(output) != id(outputOld)
        assert output.meta.shape == outputOld.meta.shape, (output.meta.shape, outputOld.meta.shape)
        assert output.meta.axistags == outputOld.meta.axistags
        for key in output.meta.keys():
            if key in ['description', 'channel_names']:
                continue
            if DEBUG and output.meta[key] != outputOld.meta[key]:
                print(f'{key}: {output.meta[key]}, {outputOld.meta[key]}\n')
            assert output.meta[key] == outputOld.meta[key], key

        for roi in [
            [slice(0, 1), slice(0, 1), slice(None), slice(None), slice(0, 1)],
            [slice(None), 0, slice(None), slice(None), slice(0, 1)],
            [slice(0, 1), 1, slice(None), slice(None), slice(1, 2)],
            [slice(None), 0, slice(None), slice(None), slice(2, 3)],
            [slice(1, 2), 0, slice(None), slice(None), slice(0, 3)],
            [0, 0, slice(None), slice(None), slice(3, 6)],
            # [0, 0, slice(1, 5), slice(1, 6), slice(6, 7)],
            [0, 0, slice(None), slice(None), slice(7, 8)],
            # [0, 0, slice(None), slice(1, 6), slice(8, 11)],
            [0, 0, slice(None), slice(None), slice(11, 14)],
            # [0, 0, slice(None), slice(None), slice(14, 15)],
            [0, 0, slice(1, 5), slice(None), slice(15, 18)],
            # [0, 0, slice(None), slice(None), slice(15, 18)],
            [0, 0, slice(None), slice(None), slice(18, 21)],
            # [0, 0, slice(None), slice(None), slice(21, 24)],
            [slice(None), slice(4, 13), slice(None), slice(None), slice(0, 24)],
        ]:
            result = output[roi].wait()
            resultOld = outputOld[roi].wait()

            if DEBUG:
                # restrict to 2d image with at most 3 channel
                result = result[0, 0, ..., :3]
                resultOld = resultOld[0, 0, ..., :3]

                print('result', result.shape, result.max(), result.min(), result.mean())
                print('resultOld', resultOld.shape, resultOld.max(), resultOld.min(), resultOld.mean())

                result = result.squeeze()
                resultOld = resultOld.squeeze()
                try:
                    resultVigra = vigra_fn(data[roi][0, 0, ..., :3].squeeze(), *scales)
                except Exception:
                    pass
                compare = ['result', 'resultOld', 'resultVigra']
                print('            result       resultOld   resultVigra')
                for i in compare:
                    line = f'{i:12s}'
                    for j in compare:
                        try:
                            line += f'{numpy.absolute(eval(i) - eval(j)).mean():1.8f}   '
                        except Exception:
                            pass
                    print(line)

                display = result - result.min()
                display /= display.max()
                displayOld = resultOld - resultOld.min()
                displayOld /= displayOld.max()
                try:
                    displayVigra = resultVigra - resultVigra.min()
                    displayVigra /= displayVigra.max()
                except Exception:
                    pass
                print('here', display.shape)
                plt.figure(figsize=(10, 10))
                plt.subplot(2, 2, 1)
                plt.imshow(display)
                plt.title('new')
                plt.subplot(2, 2, 2)
                plt.imshow(displayOld)
                plt.title('old')
                plt.subplot(2, 2, 3)
                diff = abs(display - displayOld)
                diff /= diff.max()
                plt.imshow(diff)
                plt.title('diff')
                plt.subplot(2, 2, 4)
                plt.title('vigra')
                try:
                    plt.imshow(displayVigra)
                except Exception:
                    pass
                plt.show()

            yield self.compare, result, resultOld

    def test_features(self):
        # Configure selection matrix
        sel = numpy.zeros((6, 5), dtype=bool)
        sel[0, 1] = True  # Gaussian
        sel[1, 3] = True  # L of G
        sel[2, 4] = True  # ST EVs
        sel[3, 3] = True  # H of G EVs
        sel[4, 4] = True  # GGM
        sel[5, 2] = True  # Diff of G

        if DEBUG:
            # set vigra filter to compare to here
            scales = [1.6]
            vigra_fn = vigra.filters.gaussianSmoothing

        self.opFeatures.SelectionMatrix.setValue(sel)
        self.opFeatures.ComputeIn2d.setValue([True] * 6)
        self.opFeaturesOld.SelectionMatrix.setValue(sel)

        data = vigra.taggedView(
            numpy.resize(numpy.random.rand(1 * 1 * 19 * 20 * 3), (1, 1, 19, 20, 3)).astype(numpy.float32),
            'tzyxc')

        # Set input data
        self.opFeatures.InputImage[0].setValue(data)
        self.opFeaturesOld.InputImage[0].setValue(data)

        for output, outputOld in zip(self.opFeatures.FeatureLayers[0], self.opFeaturesOld.FeatureLayers[0]):
            assert output.meta.shape == outputOld.meta.shape, (output.meta.shape, outputOld.meta.shape)
            assert output.meta.axistags == outputOld.meta.axistags
            for key in output.meta.keys():
                if key in ['description', 'channel_names']:
                    continue
                if DEBUG and output.meta[key] != outputOld.meta[key]:
                    print(f'{key}: {output.meta[key]}, {outputOld.meta[key]}\n')
                assert output.meta[key] == outputOld.meta[key], key
            result = output[:].wait()
            resultOld = outputOld[:].wait()

            if DEBUG:
                # restrict to 2d image with at most 3 channel
                result = result[0, 0, ..., :3]
                resultOld = resultOld[0, 0, ..., :3]

                print('result', result.shape, result.max(), result.min(), result.mean())
                print('resultOld', resultOld.shape, resultOld.max(), resultOld.min(), resultOld.mean())

                result = result.squeeze()
                resultOld = resultOld.squeeze()
                try:
                    resultVigra = vigra_fn(data[0, 0, ..., :3].squeeze(), *scales)
                except Exception:
                    pass
                compare = ['result', 'resultOld', 'resultVigra']
                print('            result       resultOld   resultVigra')
                for i in compare:
                    line = f'{i:12s}'
                    for j in compare:
                        try:
                            line += f'{numpy.absolute(eval(i) - eval(j)).mean():1.8f}   '
                        except Exception:
                            pass
                    print(line)

                display = result - result.min()
                display /= display.max()
                displayOld = resultOld - resultOld.min()
                displayOld /= displayOld.max()
                try:
                    displayVigra = resultVigra - resultVigra.min()
                    displayVigra /= displayVigra.max()
                except Exception:
                    pass
                print('here', display.shape)
                plt.figure(figsize=(10, 10))
                plt.subplot(2, 2, 1)
                plt.imshow(display)
                plt.title('new')
                plt.subplot(2, 2, 2)
                plt.imshow(displayOld)
                plt.title('old')
                plt.subplot(2, 2, 3)
                diff = abs(display - displayOld)
                diff /= diff.max()
                plt.imshow(diff)
                plt.title('diff')
                plt.subplot(2, 2, 4)
                plt.title('vigra')
                try:
                    plt.imshow(displayVigra)
                except Exception:
                    pass
                plt.show()

            yield self.compare, result, resultOld

    def test_ComputeIn2d(self):
        # tests ComputIn2d flag on smoothing of a 3d block (smoothing across all three, or only 2 dimensions)
        opFeatures = OpFeatureSelection(graph=Graph())
        opFeatures.Scales.setValue([1.])
        opFeatures.FeatureIds.setValue(['GaussianSmoothing'])
        opFeatures.SelectionMatrix.setValue(numpy.ones((1, 1), dtype=bool))
        opFeatures.ComputeIn2d.setValue([False])
        shape = [5, 5, 5]
        data = numpy.ones(shape, dtype=numpy.float32)
        for z in range(shape[0]):
            # make sure data is anisotropic in z
            data[z, z, 0] = 0

        data = vigra.taggedView(data[None, ...], 'czyx')
        opFeatures.InputImage.setValue(data)

        res3d = opFeatures.OutputImage[:].wait()
        opFeatures.ComputeIn2d.setValue([True])
        res2d = opFeatures.OutputImage[:].wait()
        assert (res3d != res2d).all()

    @pytest.mark.parametrize('shape,order,in2d', [
        # ([1, 1, 20, 512, 512], 'tczyx', False),
        # ([1, 1, 20, 512, 512], 'tcxyz', False),
        ([1, 1, 1, 2048, 2048], 'tczyx', True),
        # ([1, 1, 1, 512, 512], 'tczxy', True), # old is faster
        # ([10, 3, 1, 1024, 1024], 'tczyx', True),
        # ([1, 1, 25, 67, 68], 'tczyx', False),
        # ([5, 25, 67, 68, 3], 'tzyxc', False),
        ([5, 5, 256, 256], 'tcyx', True),
        ([5, 256, 256, 1], 'tyxc', True),
        ([25, 26, 1], 'xyc', True),
    ])
    def test_timing(self, shape, order, in2d):
        self.opFeatures.InputImage[0].disconnect()
        # Configure selection matrix
        sel = numpy.ones((6, 5), dtype=bool)
        sel[:, 0] = False  # don't compare sigma of 0.3
        self.opFeatures.SelectionMatrix.setValue(sel)
        self.opFeaturesOld.SelectionMatrix.setValue(sel)

        data = vigra.taggedView(
            numpy.resize(numpy.random.rand(numpy.prod(shape)), shape).astype(numpy.float32), order)
        self._timing(data, in2d)

    def _timing(self, data, in2d):
        timingsNew = []
        timingsOld = []

        for _ in range(5):
            self.opFeatures.ComputeIn2d.setValue([in2d] * 6)
            self.opFeatures.InputImage[0].setValue(data)
            self.opFeaturesOld.InputImage[0].setValue(data)
            t0 = time.time()
            self.opFeatures.OutputImage[0][:].wait()
            t1 = time.time()
            self.opFeaturesOld.OutputImage[0][:].wait()
            t2 = time.time()
            timingsNew.append(t1 - t0)
            timingsOld.append(t2 - t1)


        timeNew = numpy.mean(timingsNew)
        timeOld = numpy.mean(timingsOld)

        # The new code should (within a tolerance) run faster!
        assert timeNew <= 1.1 * timeOld + .05, f'{timeNew:.2f} !<= {timeOld:.2f}'
        logger.debug(f'{timeNew:.2f} <= {timeOld:.2f}')
