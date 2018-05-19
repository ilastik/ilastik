import numpy
import vigra

from lazyflow.graph import Graph, OperatorWrapper

from ilastik.applets.featureSelection.opFeatureSelection import OpFeatureSelection
from lazyflow.operators.oldVigraOperators import OpFeatureSelection as OpFeatureSelectionOld

DEBUG = False

if DEBUG:
    import matplotlib.pyplot as plt


class TestCompareOpFeatureSelectionToOld(object):
    def setUp(self):
        # data = vigra.taggedView(numpy.random.random((2, 20, 25, 30, 3)), 'tzyxc')

        graph = Graph()
        graph_old = Graph()

        # Define operators
        opFeatures = OperatorWrapper(OpFeatureSelection, graph=graph)
        opFeaturesOld = OperatorWrapper(OpFeatureSelectionOld, graph=graph_old)

        opFeatures.InputImage.resize(1)
        opFeaturesOld.InputImage.resize(1)

        # Configure scales
        scales = [0.3, 0.7, 1, 1.6, 3.5, 5.0, 10.0]
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

    def test_tiny(self):
        data = vigra.taggedView(numpy.resize(numpy.arange(64 * 7 * 3, dtype=numpy.float32), (1, 1, 6, 7, 3)), 'tzyxc')

        # Set input data
        self.opFeatures.InputImage[0].setValue(data)
        self.opFeaturesOld.InputImage[0].setValue(data)

        # Configure matrix
        tiny_sel = numpy.zeros((6, 7), dtype=bool)
        tiny_sel[0, 1] = True  # Gaussian
        tiny_sel[1, 0] = True  # L of G
        tiny_sel[2, 2] = True  # ST EVs
        tiny_sel[3, 0] = True  # H of G EVs
        tiny_sel[4, 2] = True  # GGM
        tiny_sel[5, 1] = True  # Diff of G

        self.opFeatures.SelectionMatrix.setValue(tiny_sel)
        self.opFeaturesOld.SelectionMatrix.setValue(tiny_sel)

        output = self.opFeatures.OutputImage[0]
        outputOld = self.opFeaturesOld.OutputImage[0]

        assert id(output) != id(outputOld)
        assert output.meta.shape == outputOld.meta.shape, (output.meta.shape, outputOld.meta.shape)
        assert output.meta.axistags == outputOld.meta.axistags
        for key in output.meta.keys():
            if output.meta[key] != outputOld.meta[key]:
                print(f'{key}: {output.meta[key]}, {outputOld.meta[key]}\n')
        assert output.meta == outputOld.meta

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

            assert result.shape == resultOld.shape
            assert numpy.allclose(result, resultOld, atol=1.e-4)

    def test(self):
        data = vigra.taggedView(
            numpy.resize(numpy.random.rand(2 * 18 * 19 * 20 * 3), (2, 18, 19, 20, 3)).astype(numpy.float32),
            'tzyxc')

        # Set input data
        self.opFeatures.InputImage[0].setValue(data)
        self.opFeaturesOld.InputImage[0].setValue(data)

        # Configure selection matrix
        sel = numpy.zeros((6, 7), dtype=bool)
        sel[0, 3] = True  # Gaussian
        sel[1, 4] = True  # L of G
        sel[2, 2] = True  # ST EVs
        sel[3, 3] = True  # H of G EVs
        sel[4, 5] = True  # GGM
        sel[5, 1] = True  # Diff of G

        if DEBUG:
            scales = [1.6]
            vigra_fn = vigra.filters.gaussianSmoothing

        self.opFeatures.SelectionMatrix.setValue(sel)
        self.opFeaturesOld.SelectionMatrix.setValue(sel)

        output = self.opFeatures.OutputImage[0]
        outputOld = self.opFeaturesOld.OutputImage[0]

        assert id(output) != id(outputOld)
        assert output.meta.shape == outputOld.meta.shape, (output.meta.shape, outputOld.meta.shape)
        assert output.meta.axistags == outputOld.meta.axistags
        for key in output.meta.keys():
            if output.meta[key] != outputOld.meta[key]:
                print(f'{key}: {output.meta[key]}, {outputOld.meta[key]}\n')
        assert output.meta == outputOld.meta

        for roi in [
            [slice(0, 1), slice(0, 1), slice(None), slice(None), slice(0, 1)],
            [slice(None), 0, slice(None), slice(None), slice(0, 1)],
            [slice(0, 1), 1, slice(None), slice(None), slice(1, 2)],
            [slice(None), 0, slice(None), slice(None), slice(2, 3)],
            [slice(1, 2), 0, slice(None), slice(None), slice(0, 3)],
            [0, 0, slice(None), slice(None), slice(3, 6)],
            # [0, 0, slice(1, 5), slice(1, 6), slice(6, 7)],
            [0, 0, slice(1, 5), slice(None), slice(7, 8)],
            # [0, 0, slice(None), slice(1, 6), slice(8, 11)],
            [0, 0, slice(None), slice(None), slice(11, 14)],
            # [0, 0, slice(None), slice(None), slice(14, 15)],
            [0, 0, slice(None), slice(None), slice(15, 18)],
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

                result -= result.min()
                result /= result.max()
                resultOld -= resultOld.min()
                resultOld /= resultOld.max()
                try:
                    resultVigra -= resultVigra.min()
                    resultVigra /= resultVigra.max()
                except Exception:
                    pass
                print('here', result.shape)
                plt.figure(figsize=(10, 10))
                plt.subplot(2, 2, 1)
                plt.imshow(result)
                plt.title('new')
                plt.subplot(2, 2, 2)
                plt.imshow(resultOld)
                plt.title('old')
                plt.subplot(2, 2, 3)
                diff = abs(result - resultOld)
                diff /= diff.max()
                plt.imshow(diff)
                plt.title('diff')
                plt.subplot(2, 2, 4)
                plt.title('vigra')
                try:
                    plt.imshow(resultVigra)
                except Exception:
                    pass
                plt.show()

            assert result.shape == resultOld.shape
            assert numpy.allclose(result, resultOld, rtol=1.e-3, atol=1.e-3), roi


if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append('--nocapture')     # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append('--nologcapture')  # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
