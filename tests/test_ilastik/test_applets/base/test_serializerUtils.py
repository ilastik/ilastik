import pickle
from typing import Sequence, Tuple, Union

import h5py
import pytest
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis, QuadraticDiscriminantAnalysis
from sklearn.ensemble import AdaBoostClassifier, RandomForestClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC, NuSVC
from sklearn.tree import DecisionTreeClassifier

from ilastik.applets.base.appletSerializer.serializerUtils import (
    ClassifierFactoryTypeInfo,
    SklearnClassifierFactoryInfo,
    _deserialize_classifier_factory_details,
    _deserialize_legacy_classifier_factory_type_info,
    _deserialize_legacy_ParallelVigraRfLazyflowClassifierFactory,
    _deserialize_legacy_SklearnLazyflowClassifierFactory,
    _deserialize_legacy_VigraRfClassifierFactory,
    _deserialize_sklearn_classifier_details,
    deleteIfPresent,
    deserialize_legacy_classifier_factory,
    deserialize_legacy_classifier_type_info,
    deserialize_string_from_h5,
    slicingToString,
    stringToSlicing,
)
from lazyflow.classifiers.parallelVigraRfLazyflowClassifier import ParallelVigraRfLazyflowClassifierFactory
from lazyflow.classifiers.sklearnLazyflowClassifier import SklearnLazyflowClassifierFactory
from lazyflow.classifiers.vigraRfLazyflowClassifier import VigraRfLazyflowClassifier, VigraRfLazyflowClassifierFactory


def test_deleteIfPresent_present(empty_in_memory_project_file: h5py.File):
    test_group_name = "test_group_42"
    _ = empty_in_memory_project_file.create_group(test_group_name)
    assert test_group_name in empty_in_memory_project_file

    deleteIfPresent(empty_in_memory_project_file, test_group_name)

    assert test_group_name not in empty_in_memory_project_file


def test_deleteIfPresent_not_present(empty_in_memory_project_file: h5py.File):
    test_group_name = "test_group_42"
    assert test_group_name not in empty_in_memory_project_file

    deleteIfPresent(empty_in_memory_project_file, test_group_name)

    assert test_group_name not in empty_in_memory_project_file


@pytest.mark.parametrize(
    "slicing,expected_string",
    [
        ((slice(0, 1),), b"[0:1]"),
        ((slice(0, 1), slice(5, 42)), b"[0:1,5:42]"),
    ],
)
def test_slicingToString(slicing: Sequence[slice], expected_string: bytes):
    assert slicingToString(slicing) == expected_string


@pytest.mark.parametrize(
    "slicing",
    [
        (slice(0, 1, 5),),
        (slice(0, 1), slice(5, 42, 13)),
    ],
)
def test_slicingToString_invalid_step_raises(slicing):
    with pytest.raises(ValueError, match="Only slices with step size of `1` or `None` are supported."):
        _ = slicingToString(slicing)


@pytest.mark.parametrize(
    "slicing",
    [
        (slice(None, 1),),
        (slice(None, 1), slice(5, 42)),
        (slice(0, 1), slice(None, 42)),
    ],
)
def test_slicingToString_start_none_raises(slicing):
    with pytest.raises(ValueError, match="Start indices for slicing must be integer, got `None`."):
        _ = slicingToString(slicing)


@pytest.mark.parametrize(
    "slicing",
    [
        (slice(0, None),),
        (slice(0, None), slice(5, 42, None)),
    ],
)
def test_slicingToString_stop_none_raises(slicing):
    with pytest.raises(ValueError, match="Stop indices for slicing must be integer, got `None`"):
        _ = slicingToString(slicing)


@pytest.mark.parametrize(
    "slice_string,expected_slicing",
    [
        (b"[0:1]", (slice(0, 1),)),
        (b"[0:1,5:42]", (slice(0, 1), slice(5, 42))),
        ("[0:1,5:42]", (slice(0, 1), slice(5, 42))),
    ],
)
def test_stringToSlicing(slice_string: Union[bytes, str], expected_slicing: Tuple[slice, ...]):
    assert stringToSlicing(slice_string) == expected_slicing


@pytest.mark.parametrize(
    "slice_string",
    [
        b"[0:None]",
        b"[None:1,5:42]",
        "[0:1:5,5:42]",
    ],
)
def test_stringToSlicing_raises(slice_string: Union[bytes, str]):
    with pytest.raises(ValueError):
        _ = stringToSlicing(slice_string)


def test_deserialize_string_from_h5(empty_in_memory_project_file: h5py.File):
    test_string = "this is a test string"
    ds = empty_in_memory_project_file.create_dataset("test", data=test_string.encode("utf-8"))

    assert deserialize_string_from_h5(ds) == test_string


def test_deserialize_classifier(empty_in_memory_project_file: h5py.File):
    classifier_bytes = b"clazyflow.classifiers.vigraRfLazyflowClassifier\nVigraRfLazyflowClassifier\np0\n."
    expected_submodule = "vigraRfLazyflowClassifier"
    expected_type = "VigraRfLazyflowClassifier"
    ds = empty_in_memory_project_file.create_dataset("classifier_type", data=classifier_bytes)

    cl_info = deserialize_legacy_classifier_type_info(ds)

    assert cl_info.submodule_name == expected_submodule
    assert cl_info.type_name == expected_type

    assert issubclass(cl_info.classifier_type, VigraRfLazyflowClassifier)


@pytest.mark.parametrize(
    "classifier_bytes",
    [
        b"clazyflow.class.vigraRfLazyflowClassifier\nVigraRfLazyflowClassifierFactory\np0\n.",
        b"csome.other_submodule.classifiers.vigraRfLazyflowClassifier\nVigraRfLazyflowClassifierFactory\np0\n.",
        b"clazyflow.classifiers.sneakyVigraRfLazyflowClassifier\nVigraRfLazyflowClassifierFactory\np0\n.",
        b"clazyflow.classifiers.vigraRfLazyflowClassifier\nSneakyVigraRfLazyflowClassifierFactory\np0\n.",
        b"random.",
    ],
)
def test_deserialize_classifier_raises(empty_in_memory_project_file: h5py.File, classifier_bytes: bytes):
    ds = empty_in_memory_project_file.create_dataset("classifier_type", data=classifier_bytes)
    with pytest.raises(ValueError):
        _ = deserialize_legacy_classifier_type_info(ds)


@pytest.mark.parametrize(
    "classifier_type, c_args, c_kwargs, expected_info",
    [
        (
            AdaBoostClassifier,
            [],
            {"n_estimators": 257},
            SklearnClassifierFactoryInfo(classifier_type=AdaBoostClassifier, args=[], kwargs={"n_estimators": 257}),
        ),
        (
            DecisionTreeClassifier,
            [],
            {"max_depth": 257},
            SklearnClassifierFactoryInfo(classifier_type=DecisionTreeClassifier, args=[], kwargs={"max_depth": 257}),
        ),
        (GaussianNB, [], {}, SklearnClassifierFactoryInfo(classifier_type=GaussianNB, args=[], kwargs={})),
        (
            KNeighborsClassifier,
            [],
            {},
            SklearnClassifierFactoryInfo(classifier_type=KNeighborsClassifier, args=[], kwargs={}),
        ),
        (
            LinearDiscriminantAnalysis,
            [],
            {},
            SklearnClassifierFactoryInfo(classifier_type=LinearDiscriminantAnalysis, args=[], kwargs={}),
        ),
        (
            QuadraticDiscriminantAnalysis,
            [],
            {},
            SklearnClassifierFactoryInfo(classifier_type=QuadraticDiscriminantAnalysis, args=[], kwargs={}),
        ),
        (
            RandomForestClassifier,
            [143],
            {},
            SklearnClassifierFactoryInfo(classifier_type=RandomForestClassifier, args=[143], kwargs={}),
        ),
        (
            SVC,
            [],
            {"probability": False},
            SklearnClassifierFactoryInfo(classifier_type=SVC, args=[], kwargs={"probability": False}),
        ),
        (
            NuSVC,
            [],
            {"probability": False},
            SklearnClassifierFactoryInfo(classifier_type=NuSVC, args=[], kwargs={"probability": False}),
        ),
    ],
)
def test_sklearn_lazyflow_classifier_pickled_deserialization(
    classifier_type, c_args, c_kwargs, expected_info: SklearnClassifierFactoryInfo
):
    pickled_classifier = pickle.dumps(
        SklearnLazyflowClassifierFactory(classifier_type, *c_args, **c_kwargs), 0
    ).decode()
    deserialized_info = _deserialize_sklearn_classifier_details(classifier_type, pickled_classifier)
    assert deserialized_info == expected_info


@pytest.mark.parametrize(
    "classifier_type",
    [
        AdaBoostClassifier,
        DecisionTreeClassifier,
        RandomForestClassifier,
        SVC,
        NuSVC,
    ],
)
def test_sklearn_lazyflow_classifier_pickled_deserialization_raises(
    classifier_type,
):
    with pytest.raises(ValueError, match="Could not deserialize"):
        _ = _deserialize_sklearn_classifier_details(classifier_type, "someRandomString")


@pytest.mark.parametrize(
    "classifier_type, c_args, c_kwargs, expected_info",
    [
        (
            AdaBoostClassifier,
            [],
            {"n_estimators": 257},
            SklearnClassifierFactoryInfo(classifier_type=AdaBoostClassifier, args=[], kwargs={"n_estimators": 257}),
        ),
        (
            DecisionTreeClassifier,
            [],
            {"max_depth": 257},
            SklearnClassifierFactoryInfo(classifier_type=DecisionTreeClassifier, args=[], kwargs={"max_depth": 257}),
        ),
        (GaussianNB, [], {}, SklearnClassifierFactoryInfo(classifier_type=GaussianNB, args=[], kwargs={})),
        (
            KNeighborsClassifier,
            [],
            {},
            SklearnClassifierFactoryInfo(classifier_type=KNeighborsClassifier, args=[], kwargs={}),
        ),
        (
            LinearDiscriminantAnalysis,
            [],
            {},
            SklearnClassifierFactoryInfo(classifier_type=LinearDiscriminantAnalysis, args=[], kwargs={}),
        ),
        (
            QuadraticDiscriminantAnalysis,
            [],
            {},
            SklearnClassifierFactoryInfo(classifier_type=QuadraticDiscriminantAnalysis, args=[], kwargs={}),
        ),
        (
            RandomForestClassifier,
            [143],
            {},
            SklearnClassifierFactoryInfo(classifier_type=RandomForestClassifier, args=[143], kwargs={}),
        ),
        (
            SVC,
            [],
            {"probability": False},
            SklearnClassifierFactoryInfo(classifier_type=SVC, args=[], kwargs={"probability": False}),
        ),
        (
            NuSVC,
            [],
            {"probability": False},
            SklearnClassifierFactoryInfo(classifier_type=NuSVC, args=[], kwargs={"probability": False}),
        ),
    ],
)
def test_deserialize_legacy_SklearnLazyflowClassifierFactory(classifier_type, c_args, c_kwargs, expected_info):
    assert True
    pickled_classifier = pickle.dumps(
        SklearnLazyflowClassifierFactory(classifier_type, *c_args, **c_kwargs), 0
    ).decode()
    classifier_factory_info = _deserialize_legacy_SklearnLazyflowClassifierFactory(pickled_classifier)

    assert classifier_factory_info == expected_info


@pytest.mark.parametrize(
    "pickle_string",
    [
        "V_classifier_type\np0\ncsklearn.some.submodules.not.in.list\nAdaBoostClassifier\n",
        "V_classifier_type\np0\ncsklearn.neighbors._classification\nMyMeanClassifier42\n",
        "someRandomString",
    ],
)
def test_deserialize_legacy_SklearnLazyflowClassifierFactory_raises(
    pickle_string,
):
    with pytest.raises(ValueError):
        _ = _deserialize_legacy_SklearnLazyflowClassifierFactory(pickle_string)


@pytest.mark.parametrize(
    "classifier_factory",
    [
        ParallelVigraRfLazyflowClassifierFactory(42, None, None, None, False),
        ParallelVigraRfLazyflowClassifierFactory(43, 2, None, None, False),
        ParallelVigraRfLazyflowClassifierFactory(44, None, "test_variable_importance_path", None, True),
        ParallelVigraRfLazyflowClassifierFactory(45, None, None, 0.33, False),
        ParallelVigraRfLazyflowClassifierFactory(46, 89, "VVmyfunnyteststringVV", 1.0, True),
    ],
)
def test_deserialize_legacy_ParallelVigraRfLazyflowClassifierFactory(classifier_factory):
    info = _deserialize_legacy_ParallelVigraRfLazyflowClassifierFactory(pickle.dumps(classifier_factory, 0).decode())

    assert info.instance == classifier_factory


@pytest.mark.parametrize(
    "pickle_string",
    [
        "something_funny",
        # wrong value types will raise:
        "V_num_trees\np7\nF46\n",
        "V_num_trees\np7\nI46\nsV_label_proportion\np8\nI300\n",
        "V_num_trees\np7\nI46\nsV_label_proportion\np8\nF1.0\nsV_variable_importance_path\np9\nF3.0\n",
        "V_num_trees\np7\nI46\nsV_label_proportion\np8\nF1.0\nsV_variable_importance_path\np9\nVtest\np10\nsV_variable_importance_enabled\np11\nI1\ns",
        "V_num_trees\np7\nI46\nsV_label_proportion\np8\nF1.0\nsV_variable_importance_path\np9\nVtest\np10\nsV_variable_importance_enabled\np11\nI01\nsV_num_forests\np14\nF89\n",
        # missing values will raise:
        "V_num_trees\np7\nF46\n",
        "V_num_trees\np7\nI46\nsV_label_proportion\np8\n",
        "V_num_trees\np7\nI46\nsV_label_proportion\np8\nF1.0\nsV_variable_importance_path\np9\n\n",
        "V_num_trees\np7\nI46\nsV_label_proportion\np8\nF1.0\nsV_variable_importance_path\np9\nVtest\np10\nsV_variable_importance_enabled\np11\ns",
    ],
)
def test_deserialize_legacy_ParallelVigraRfLazyflowClassifierFactory_raises(pickle_string):
    with pytest.raises(ValueError):
        _ = _deserialize_legacy_ParallelVigraRfLazyflowClassifierFactory(pickle_string)


@pytest.mark.parametrize(
    "classifier_factory",
    [
        VigraRfLazyflowClassifierFactory(30),
        VigraRfLazyflowClassifierFactory(42),
    ],
)
def test_deserialize_legacy_VigraRflassifierFactory(classifier_factory):
    info = _deserialize_legacy_VigraRfClassifierFactory(pickle.dumps(classifier_factory, 0).decode())

    assert info.instance == classifier_factory


def test_deserialize_legacy_VigraRflassifierFactory_raises():
    with pytest.raises(ValueError):
        _ = _deserialize_legacy_VigraRfClassifierFactory(pickle.dumps(VigraRfLazyflowClassifierFactory(), 0).decode())


@pytest.mark.parametrize(
    "classifier_factory",
    [
        ParallelVigraRfLazyflowClassifierFactory(46, 89, "VVmyfunnyteststringVV", 1.0, True),
        SklearnLazyflowClassifierFactory(RandomForestClassifier, 143),
        SklearnLazyflowClassifierFactory(classifier_type=AdaBoostClassifier, n_estimators=257),
        SklearnLazyflowClassifierFactory(classifier_type=DecisionTreeClassifier, max_depth=257),
        SklearnLazyflowClassifierFactory(classifier_type=GaussianNB),
        SklearnLazyflowClassifierFactory(classifier_type=KNeighborsClassifier),
        SklearnLazyflowClassifierFactory(classifier_type=LinearDiscriminantAnalysis),
        SklearnLazyflowClassifierFactory(classifier_type=NuSVC, probability=False),
        SklearnLazyflowClassifierFactory(classifier_type=QuadraticDiscriminantAnalysis),
        SklearnLazyflowClassifierFactory(classifier_type=SVC, probability=False),
        VigraRfLazyflowClassifierFactory(42),
    ],
)
def test_deserialize_classifier_factory_details(classifier_factory):
    info = _deserialize_classifier_factory_details(
        type(classifier_factory), pickle.dumps(classifier_factory, 0).decode()
    )

    assert info.instance == classifier_factory


class MyTestClassifierFactory:
    def __init__(self, *args, **kwargs):
        pass


def test_deserialize_classifier_factory_details_raises():

    classifier_factory = MyTestClassifierFactory(42)

    with pytest.raises(ValueError):
        _ = _deserialize_classifier_factory_details(
            type(classifier_factory), pickle.dumps(classifier_factory, 0).decode()  # type: ignore[reportArgumentType]
        )


@pytest.mark.parametrize(
    "classifier_factory, expected_info",
    [
        (
            ParallelVigraRfLazyflowClassifierFactory(46, 89, "VVmyfunnyteststringVV", 1.0, True),
            ClassifierFactoryTypeInfo(
                factory_submodule="parallelVigraRfLazyflowClassifier",
                factory_typename="ParallelVigraRfLazyflowClassifierFactory",
                factory_version=ParallelVigraRfLazyflowClassifierFactory.VERSION,
            ),
        ),
        (
            SklearnLazyflowClassifierFactory(RandomForestClassifier, 143),
            ClassifierFactoryTypeInfo(
                factory_submodule="sklearnLazyflowClassifier",
                factory_typename="SklearnLazyflowClassifierFactory",
                factory_version=SklearnLazyflowClassifierFactory.VERSION,
            ),
        ),
        (
            SklearnLazyflowClassifierFactory(classifier_type=AdaBoostClassifier, n_estimators=257),
            ClassifierFactoryTypeInfo(
                factory_submodule="sklearnLazyflowClassifier",
                factory_typename="SklearnLazyflowClassifierFactory",
                factory_version=SklearnLazyflowClassifierFactory.VERSION,
            ),
        ),
        (
            SklearnLazyflowClassifierFactory(classifier_type=DecisionTreeClassifier, max_depth=257),
            ClassifierFactoryTypeInfo(
                factory_submodule="sklearnLazyflowClassifier",
                factory_typename="SklearnLazyflowClassifierFactory",
                factory_version=SklearnLazyflowClassifierFactory.VERSION,
            ),
        ),
        (
            SklearnLazyflowClassifierFactory(classifier_type=GaussianNB),
            ClassifierFactoryTypeInfo(
                factory_submodule="sklearnLazyflowClassifier",
                factory_typename="SklearnLazyflowClassifierFactory",
                factory_version=SklearnLazyflowClassifierFactory.VERSION,
            ),
        ),
        (
            SklearnLazyflowClassifierFactory(classifier_type=KNeighborsClassifier),
            ClassifierFactoryTypeInfo(
                factory_submodule="sklearnLazyflowClassifier",
                factory_typename="SklearnLazyflowClassifierFactory",
                factory_version=SklearnLazyflowClassifierFactory.VERSION,
            ),
        ),
        (
            SklearnLazyflowClassifierFactory(classifier_type=LinearDiscriminantAnalysis),
            ClassifierFactoryTypeInfo(
                factory_submodule="sklearnLazyflowClassifier",
                factory_typename="SklearnLazyflowClassifierFactory",
                factory_version=SklearnLazyflowClassifierFactory.VERSION,
            ),
        ),
        (
            SklearnLazyflowClassifierFactory(classifier_type=NuSVC, probability=False),
            ClassifierFactoryTypeInfo(
                factory_submodule="sklearnLazyflowClassifier",
                factory_typename="SklearnLazyflowClassifierFactory",
                factory_version=SklearnLazyflowClassifierFactory.VERSION,
            ),
        ),
        (
            SklearnLazyflowClassifierFactory(classifier_type=QuadraticDiscriminantAnalysis),
            ClassifierFactoryTypeInfo(
                factory_submodule="sklearnLazyflowClassifier",
                factory_typename="SklearnLazyflowClassifierFactory",
                factory_version=SklearnLazyflowClassifierFactory.VERSION,
            ),
        ),
        (
            SklearnLazyflowClassifierFactory(classifier_type=SVC, probability=False),
            ClassifierFactoryTypeInfo(
                factory_submodule="sklearnLazyflowClassifier",
                factory_typename="SklearnLazyflowClassifierFactory",
                factory_version=SklearnLazyflowClassifierFactory.VERSION,
            ),
        ),
        (
            VigraRfLazyflowClassifierFactory(42),
            ClassifierFactoryTypeInfo(
                factory_submodule="vigraRfLazyflowClassifier",
                factory_typename="VigraRfLazyflowClassifierFactory",
                factory_version=VigraRfLazyflowClassifierFactory.VERSION,
            ),
        ),
    ],
)
def test_deserialize_legacy_classifier_factory_type_info(classifier_factory, expected_info):
    info = _deserialize_legacy_classifier_factory_type_info(pickle.dumps(classifier_factory, 0).decode())
    assert info == expected_info


@pytest.mark.parametrize(
    "pickle_string",
    [
        "ccopy_reg\n_reconstructor\np0\n(clazyflow.classifiers.vigraRfLazyflowClassifier\nMyPhantasyFactory\np1\nc__builtin__\nobject\np2\nNtp3\nRp4\n(dp5\nVVERSION\np6\nI1\nsV_args",
        "ccopy_reg\n_reconstructor\np0\n(clazyflow.classifiers.someothermodule\nVigraRfLazyflowClassifierFactory\np1\nc__builtin__\nobject\np2\nNtp3\nRp4\n(dp5\nVVERSION\np6\nI1\nsV_args",
        "ccopy_reg\n_reconstructor\np0\n(\nVigraRfLazyflowClassifierFactory\np1\nc__builtin__\nobject\np2\nNtp3\nRp4\n(dp5\nVVERSION\np6\nI1\nsV_args",
        "ccopy_reg\n_reconstructor\np0\n(clazyflow.classifiers.vigraRfLazyflowClassifier\nVigraRfLazyflowClassifierFactory\np1\nc__builtin__\nobject\np2\nNtp3\nRp4\n(dp5\nsV_args",
    ],
)
def test_deserialize_legacy_classifier_factory_type_info_raises(pickle_string):
    with pytest.raises(ValueError):
        _ = _deserialize_legacy_classifier_factory_type_info(pickle_string)


@pytest.mark.parametrize(
    "classifier_factory",
    [
        ParallelVigraRfLazyflowClassifierFactory(46, 89, "VVmyfunnyteststringVV", 1.0, True),
        SklearnLazyflowClassifierFactory(RandomForestClassifier, 143),
        SklearnLazyflowClassifierFactory(classifier_type=AdaBoostClassifier, n_estimators=257),
        SklearnLazyflowClassifierFactory(classifier_type=DecisionTreeClassifier, max_depth=257),
        SklearnLazyflowClassifierFactory(classifier_type=GaussianNB),
        SklearnLazyflowClassifierFactory(classifier_type=KNeighborsClassifier),
        SklearnLazyflowClassifierFactory(classifier_type=LinearDiscriminantAnalysis),
        SklearnLazyflowClassifierFactory(classifier_type=NuSVC, probability=False),
        SklearnLazyflowClassifierFactory(classifier_type=QuadraticDiscriminantAnalysis),
        SklearnLazyflowClassifierFactory(classifier_type=SVC, probability=False),
        VigraRfLazyflowClassifierFactory(42),
    ],
)
def test_deserialize_legacy_classifier_factory(empty_in_memory_project_file, classifier_factory):

    ds = empty_in_memory_project_file.create_dataset(name="classifier", data=pickle.dumps(classifier_factory, 0))

    factory = deserialize_legacy_classifier_factory(ds)

    assert factory == classifier_factory
