###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2024, the ilastik developers
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
#          http://ilastik.org/license.html
###############################################################################
import pickle

import h5py
import numpy
import pytest
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis, QuadraticDiscriminantAnalysis
from sklearn.ensemble import AdaBoostClassifier, RandomForestClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC, NuSVC
from sklearn.tree import DecisionTreeClassifier

from ilastik.applets.base.appletSerializer.legacyClassifiers import (
    ClassifierFactoryTypeInfo,
    SklearnClassifierFactoryInfo,
    _deserialize_classifier_factory_impl,
    _deserialize_classifier_factory_type,
    _deserialize_ParallelVigraRfLazyflowClassifierFactory,
    _deserialize_sklearn_classifier,
    _deserialize_SklearnLazyflowClassifierFactory,
    _deserialize_VigraRfClassifierFactory,
    deserialize_classifier_factory,
    deserialize_classifier_type,
)
from lazyflow.classifiers.parallelVigraRfLazyflowClassifier import ParallelVigraRfLazyflowClassifierFactory
from lazyflow.classifiers.sklearnLazyflowClassifier import SklearnLazyflowClassifier, SklearnLazyflowClassifierFactory
from lazyflow.classifiers.vigraRfLazyflowClassifier import VigraRfLazyflowClassifier, VigraRfLazyflowClassifierFactory


def test_deserialize_classifier(empty_in_memory_project_file: h5py.File):
    classifier_bytes = b"clazyflow.classifiers.vigraRfLazyflowClassifier\nVigraRfLazyflowClassifier\np0\n."
    ds = empty_in_memory_project_file.create_dataset("classifier_type", data=classifier_bytes)

    classifier = deserialize_classifier_type(ds)

    assert issubclass(classifier, VigraRfLazyflowClassifier)


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
        _ = deserialize_classifier_type(ds)


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
    deserialized_info = _deserialize_sklearn_classifier(classifier_type, pickled_classifier)
    assert deserialized_info == expected_info


def test_sklearn_deserialization_from_project_file(empty_in_memory_project_file):
    """Ensure loading of sklearn classifiers as saved in ilastik"""

    classifier = SklearnLazyflowClassifier(
        KNeighborsClassifier(), known_classes=3, feature_count=3, feature_names=["a", "b", "c"]
    )
    classifier_bytes = pickle.dumps(classifier, 0)
    # note that sklearn classifiers are saved wrapped in numpy.void
    ds = empty_in_memory_project_file.create_dataset("classifier_type", data=numpy.void(classifier_bytes))

    classifier_type = deserialize_classifier_type(ds)
    assert issubclass(classifier_type, SklearnLazyflowClassifier)


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
        _ = _deserialize_sklearn_classifier(classifier_type, "someRandomString")


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
def test_deserialize_SklearnLazyflowClassifierFactory(classifier_type, c_args, c_kwargs, expected_info):
    pickled_classifier = pickle.dumps(
        SklearnLazyflowClassifierFactory(classifier_type, *c_args, **c_kwargs), 0
    ).decode()
    classifier_factory_info = _deserialize_SklearnLazyflowClassifierFactory(pickled_classifier)

    assert classifier_factory_info == expected_info


@pytest.mark.parametrize(
    "pickle_string",
    [
        "V_classifier_type\np0\ncsklearn.some.submodules.not.in.list\nAdaBoostClassifier\n",
        "V_classifier_type\np0\ncsklearn.neighbors._classification\nMyMeanClassifier42\n",
        "someRandomString",
    ],
)
def test_deserialize_SklearnLazyflowClassifierFactory_raises(
    pickle_string,
):
    with pytest.raises(ValueError):
        _ = _deserialize_SklearnLazyflowClassifierFactory(pickle_string)


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
def test_deserialize_ParallelVigraRfLazyflowClassifierFactory(classifier_factory):
    info = _deserialize_ParallelVigraRfLazyflowClassifierFactory(pickle.dumps(classifier_factory, 0).decode())

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
def test_deserialize_ParallelVigraRfLazyflowClassifierFactory_raises(pickle_string):
    with pytest.raises(ValueError):
        _ = _deserialize_ParallelVigraRfLazyflowClassifierFactory(pickle_string)


@pytest.mark.parametrize(
    "classifier_factory",
    [
        VigraRfLazyflowClassifierFactory(30),
        VigraRfLazyflowClassifierFactory(42),
    ],
)
def test_deserialize_legacy_VigraRflassifierFactory(classifier_factory):
    info = _deserialize_VigraRfClassifierFactory(pickle.dumps(classifier_factory, 0).decode())

    assert info.instance == classifier_factory


def test_deserialize_legacy_VigraRflassifierFactory_raises():
    with pytest.raises(ValueError):
        _ = _deserialize_VigraRfClassifierFactory(pickle.dumps(VigraRfLazyflowClassifierFactory(), 0).decode())


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
def test_deserialize_classifier_factory_impl(classifier_factory):
    info = _deserialize_classifier_factory_impl(type(classifier_factory), pickle.dumps(classifier_factory, 0).decode())

    assert info.instance == classifier_factory


class MyTestClassifierFactory:
    def __init__(self, *args, **kwargs):
        pass


def test_deserialize_classifier_factory_raises():

    classifier_factory = MyTestClassifierFactory(42)

    with pytest.raises(ValueError):
        _ = _deserialize_classifier_factory_impl(
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
def test_deserialize_classifier_factory_type(classifier_factory, expected_info):
    info = _deserialize_classifier_factory_type(pickle.dumps(classifier_factory, 0).decode())
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
def test_deserialize_classifier_factory_type_raises(pickle_string):
    with pytest.raises(ValueError):
        _ = _deserialize_classifier_factory_type(pickle_string)


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
def test_deserialize_classifier_factory(empty_in_memory_project_file, classifier_factory):

    ds = empty_in_memory_project_file.create_dataset(name="classifier", data=pickle.dumps(classifier_factory, 0))

    factory = deserialize_classifier_factory(ds)

    assert factory == classifier_factory
