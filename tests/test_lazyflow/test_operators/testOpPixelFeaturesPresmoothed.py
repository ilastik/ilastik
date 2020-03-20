import numpy
import vigra

from lazyflow.graph import Graph
from lazyflow.operators import OpPixelFeaturesPresmoothed

DEBUG = False

if DEBUG:
    import matplotlib.pyplot as plt


class TestOpPixelFeaturesPresmoothed(object):
    @classmethod
    def setup_class(cls):
        # cls.data = numpy.random.randint(0, 255, (2, 3, 8, 19, 20), dtype='uint8').view(vigra.VigraArray)
        cls.data = numpy.random.rand(2, 3, 10, 19, 20).view(vigra.VigraArray)
        cls.data.axistags = vigra.defaultAxistags("tczyx")

    def test_compute_in_2d(self):
        op = OpPixelFeaturesPresmoothed(graph=Graph())

        op.Scales.setValue([0.7, 1, 1.6])

        op.FeatureIds.setValue(
            [
                "GaussianSmoothing",
                "LaplacianOfGaussian",
                "StructureTensorEigenvalues",
                "HessianOfGaussianEigenvalues",
                "GaussianGradientMagnitude",
                "DifferenceOfGaussians",
            ]
        )

        op.SelectionMatrix.setValue(
            numpy.array(
                [
                    [True, False, True],
                    [False, True, False],
                    [False, False, True],
                    [True, False, False],
                    [False, True, False],
                    [False, False, True],
                ]
            )
        )

        # compute result over whole volume in 2d
        op.ComputeIn2d.setValue([True] * 3)
        op.Input.setValue(self.data)
        computed_whole = op.Output[:].wait()

        # compute result for every z slice independently
        z_slices = []
        for z in range(self.data.shape[2]):
            op.Input.setValue(self.data[:, :, z : z + 1])
            z_slices.append(op.Output[:].wait())

        computed_per_slice = numpy.concatenate(z_slices, axis=2)
        assert computed_per_slice.shape == computed_whole.shape

        if DEBUG:
            check_channel = 6
            plt.figure(figsize=(5, 20))
            for z in range(self.data.shape[2]):
                plt.subplot(self.data.shape[2], 2, 2 * z + 1)
                plt.imshow(computed_whole[0, check_channel, z])
                plt.title("whole")
                plt.subplot(self.data.shape[2], 2, 2 * z + 2)
                plt.imshow(computed_per_slice[0, check_channel, z])
                plt.title("per slice")

            plt.show()

        assert computed_whole.shape == computed_per_slice.shape
        assert numpy.allclose(computed_whole, computed_per_slice), abs(computed_whole - computed_per_slice).max()


if __name__ == "__main__":
    import sys
    import nose

    sys.argv.append("--nocapture")  # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture")  # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
