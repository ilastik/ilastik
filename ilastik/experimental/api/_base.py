import vigra
import numpy

from lazyflow.graph import Graph
from lazyflow.operators.classifierOperators import OpClassifierPredict, OpTrainClassifierBlocked
from lazyflow.classifiers import ParallelVigraRfLazyflowClassifierFactory
from ilastik.applets.featureSelection.opFeatureSelection import OpFeatureSelection
from .types import Classifier

WORKFLOW_KEY = "workflowName"
FEATURES_KEY = "FeatureSelections"
FEATURES_IDS_KEY = "FeatureIds"
FEATURES_SCALES_KEY = "Scales"
FEATURES_SELECTION_MATRIX_KEY = "SelectionMatrix"
PIXEL_CLASSIFICATION_KEY = "PixelClassification"
PIXEL_CLASSIFICATION_TYPE_KEY = "pickled_type"
PIXEL_CLASSIFICATION_FORESTS_KEY = "ClassifierForests"
LABEL_NAMES_KEY = "LabelNames"

PIXEL_CLASSIFICATION = b"Pixel Classification"

class ClassifierBuilder:
    def __init__(self):
        self._data = None
        self._labels = None
        self._features = None

    def _validate_data_and_labels(self, data, labels):
        if data is None:
            raise ValueError("No data provided")

        if labels is None:
            raise ValueError("No labels provided")

        if data.shape != labels.shape:
            raise ValueError(f"data({data.shape}) and labels({labels.shape}) shape mismatch")

    def _validate_features(self, features):
        if not features:
            raise ValueError("No features provided")

    def add_dataset(self, data, labels):
        # TODO: Properly handle axistags
        self._validate_data_and_labels(data, labels)
        data_axes = _guess_axistags(data.shape)
        label_axes = _guess_axistags(labels.shape)
        self._data = _make_vigra_with_cannel_axis(data, data_axes)
        self._labels = _make_vigra_with_cannel_axis(labels, label_axes)
        return self

    def use_features(self, features):
        self._validate_features(features)
        self._features = features
        return self

    def _construct_graph(self):
        graph = Graph()

        feature_names, scales, sel_matrix = _collect_features(self._features)

        feature_sel_op = OpFeatureSelection(graph=graph)
        feature_sel_op.InputImage.setValue(self._data)
        feature_sel_op.FeatureIds.setValue(feature_names)
        feature_sel_op.Scales.setValue([s / 10 for s in scales])
        feature_sel_op.SelectionMatrix.setValue(numpy.array(sel_matrix))

        train_op = OpTrainClassifierBlocked(graph=graph)
        train_op.ClassifierFactory.setValue(ParallelVigraRfLazyflowClassifierFactory(100))
        train_op.Images.resize(1)
        train_op.Labels.resize(1)
        train_op.nonzeroLabelBlocks.resize(1)
        train_op.Images[0].connect(feature_sel_op.CachedOutputImage)
        train_op.Labels[0].setValue(self._labels)
        train_op.nonzeroLabelBlocks[0].setValue(0) # This value is ignored by vectorwise classifier
        train_op.MaxLabel.setValue(2)

        class _ClassifierImpl(Classifier):
            def predict(self, data):
                axes = _guess_axistags(data.shape)
                data = _make_vigra_with_cannel_axis(data, axes)

                feature_sel_op = OpFeatureSelection(graph=graph)
                feature_sel_op.InputImage.setValue(data)
                feature_sel_op.FeatureIds.setValue(feature_names)
                feature_sel_op.Scales.setValue([s / 10 for s in scales])
                feature_sel_op.SelectionMatrix.setValue(numpy.array(sel_matrix))

                predict_op = OpClassifierPredict(graph=graph)
                predict_op.Classifier.connect(train_op.Classifier)
                predict_op.Image.connect(feature_sel_op.OutputImage)
                predict_op.LabelsCount.connect(train_op.MaxLabel)
                return predict_op.PMaps.value[:,:,0]

        return _ClassifierImpl()

    def train(self):
        self._validate_data_and_labels(self._data, self._labels)
        self._validate_features(self._features)
        return self._construct_graph()

    @classmethod
    def from_project_file(self, path):
        import h5py
        import pickle

        with h5py.File(path, "r") as project_file:
            print(project_file.keys())
            workflow = project_file[WORKFLOW_KEY][()]
            if workflow != PIXEL_CLASSIFICATION:
                raise NotImplementedError(f"Unsupported workflow {workflow}")

            feature_names = [name.decode("ascii") for name in project_file[FEATURES_KEY][FEATURES_IDS_KEY][()]]
            scales = project_file[FEATURES_KEY][FEATURES_SCALES_KEY][()]
            sel_matrix = project_file[FEATURES_KEY][FEATURES_SELECTION_MATRIX_KEY][()]

            classfier_group = project_file[PIXEL_CLASSIFICATION_KEY][PIXEL_CLASSIFICATION_FORESTS_KEY]
            classifier_type = pickle.loads(classfier_group[PIXEL_CLASSIFICATION_TYPE_KEY][()])
            classifier = classifier_type.deserialize_hdf5(classfier_group)

            label_count = len(project_file[PIXEL_CLASSIFICATION_KEY][LABEL_NAMES_KEY])

        graph = Graph()

        class _ClassifierImpl(Classifier):
            def predict(self, data):
                axes = _guess_axistags(data.shape)
                data = _make_vigra_with_cannel_axis(data, axes)

                feature_sel_op = OpFeatureSelection(graph=graph)
                feature_sel_op.InputImage.setValue(data)
                feature_sel_op.FeatureIds.setValue(feature_names)
                feature_sel_op.Scales.setValue([s / 10 for s in scales])
                feature_sel_op.SelectionMatrix.setValue(numpy.array(sel_matrix))

                predict_op = OpClassifierPredict(graph=graph)
                predict_op.Classifier.setValue(classifier)
                predict_op.Classifier.meta.classifier_factory = ParallelVigraRfLazyflowClassifierFactory(100)  # FIXME
                predict_op.Image.connect(feature_sel_op.OutputImage)
                predict_op.LabelsCount.setValue(label_count)
                return predict_op.PMaps.value[:,:,0]

        return _ClassifierImpl()


def _guess_axistags(shape):
    if len(shape) == 3:
        return "zyx"
    elif len(shape) == 2:
        return "yx"
    else:
        raise NotImplementedError(f"Got shape {shape}")


def _collect_features(features):
    feature_names = set()
    scales = set()
    lookup = {}

    for f in features:
        feature_names.add(f.name)
        scales.add(f.scale)
        lookup[f.name, f.scale] = True

    feature_names = sorted(feature_names)
    scales = sorted(scales)

    feature_matrix = []
    for f_name in feature_names:
        row = []
        for f_scale in scales:
            row.append(lookup.get((f_name, f_scale), False))

        feature_matrix.append(row)

    return feature_names, scales, feature_matrix


def _make_vigra_with_cannel_axis(data, axes):
    assert "c" not in axes
    result = data.reshape(*data.shape, 1)
    return vigra.taggedView(result, axes + "c")
