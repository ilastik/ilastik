class _Feature:
    name = "some name"

    def __init__(self, scale):
        self.scale = scale

    @property
    def key(self):
        return self.name, self.scale

    def __hash__(self):
        return hash(self.key())

    def __eq__(self, other):
        return isinstance(other, _Feature) and self.key() == other.key()


class Gaussian(_Feature):
    name = "GaussianSmoothing"

class LaplacianOfGaussian(_Feature):
    name = "LaplacianOfGaussian"

class StructureTensorEigenvalues(_Feature):
    name = "StructureTensorEigenvalues"

class HessianOfGaussianEigenvalues(_Feature):
    name = "HessianOfGaussianEigenvalues"

class GaussianGradientMagnitude(_Feature):
    name = "GaussianGradientMagnitude"

class DifferenceOfGaussians(_Feature):
    name = "DifferenceOfGaussians"


_FEAUTURE_CLASSES = [
    DifferenceOfGaussians,
    Gaussian,
    GaussianGradientMagnitude,
    HessianOfGaussianEigenvalues,
    LaplacianOfGaussian,
    StructureTensorEigenvalues,
]

_SCALES = [3, 7, 10, 16, 35, 50, 100]

DEFAULT_FEATURES = [
    cls(scale)
    for cls in _FEAUTURE_CLASSES
    for scale in _SCALES
]
