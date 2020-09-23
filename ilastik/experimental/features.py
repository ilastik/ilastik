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

    def __repr__(self):
        return f"{self.name}(scale={self.scale/10:.1f})"


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


_FEAUTURE_CLASSES = {
    DifferenceOfGaussians.name: DifferenceOfGaussians,
    Gaussian.name: Gaussian,
    GaussianGradientMagnitude.name: GaussianGradientMagnitude,
    HessianOfGaussianEigenvalues.name: HessianOfGaussianEigenvalues,
    LaplacianOfGaussian.name: LaplacianOfGaussian,
    StructureTensorEigenvalues.name: StructureTensorEigenvalues,
}

_DEFAULT_SCALES = [3, 7, 10, 16, 35, 50, 100]


def create_feature_by_name(name, scale):
    type_ = _FEAUTURE_CLASSES[name]
    return type_(scale)


DEFAULT_FEATURES = [cls(scale) for cls in _FEAUTURE_CLASSES.values() for scale in _DEFAULT_SCALES]
