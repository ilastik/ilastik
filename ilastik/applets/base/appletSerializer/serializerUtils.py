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
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple, Type, Union

import h5py
import sklearn
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis, QuadraticDiscriminantAnalysis
from sklearn.ensemble import AdaBoostClassifier, RandomForestClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC, NuSVC
from sklearn.tree import DecisionTreeClassifier

import lazyflow.classifiers
from lazyflow.classifiers.lazyflowClassifier import (
    LazyflowPixelwiseClassifierABC,
    LazyflowPixelwiseClassifierFactoryABC,
    LazyflowVectorwiseClassifierABC,
    LazyflowVectorwiseClassifierFactoryABC,
)
from lazyflow.classifiers.parallelVigraRfLazyflowClassifier import ParallelVigraRfLazyflowClassifierFactory
from lazyflow.classifiers.sklearnLazyflowClassifier import SklearnLazyflowClassifierFactory
from lazyflow.classifiers.vigraRfLazyflowClassifier import VigraRfLazyflowClassifierFactory
from lazyflow.classifiers.vigraRfPixelwiseClassifier import VigraRfPixelwiseClassifierFactory


def deleteIfPresent(parentGroup: h5py.Group, name: str) -> None:
    """Deletes parentGroup[name], if it exists."""
    # Check first. If we try to delete a non-existent key,
    # hdf5 will complain on the console.
    if name in parentGroup:
        del parentGroup[name]


def slicingToString(slicing: Sequence[slice]) -> bytes:
    """Convert the given slicing into a string of the form
    '[0:1,2:3,4:5]'

    slices need to have integer start and stop values, step-size of 1
    is assumed

    The result is a utf-8 encoded bytes, for easy storage via h5py
    """
    if any(sl.step not in [None, 1] for sl in slicing):
        raise ValueError("Only slices with step size of `1` or `None` are supported.")

    if any(sl.start is None for sl in slicing):
        raise ValueError("Start indices for slicing must be integer, got `None`.")

    if any(sl.stop is None for sl in slicing):
        raise ValueError("Stop indices for slicing must be integer, got `None`.")

    strSlicing = "["
    for s in slicing:
        strSlicing += str(s.start)
        strSlicing += ":"
        strSlicing += str(s.stop)
        strSlicing += ","

    strSlicing = strSlicing[:-1]  # Drop the last comma
    strSlicing += "]"
    return strSlicing.encode("utf-8")


def stringToSlicing(strSlicing: Union[bytes, str]) -> Tuple[slice, ...]:
    """Parse a string of the form '[0:1,2:3,4:5]' into a slicing (i.e.
    tuple of slices)

    """
    if isinstance(strSlicing, bytes):
        strSlicing = strSlicing.decode("utf-8")

    assert isinstance(strSlicing, str)

    slicing = []
    strSlicing = strSlicing[1:-1]  # Drop brackets
    sliceStrings = strSlicing.split(",")
    for s in sliceStrings:
        ends = s.split(":")
        if len(ends) != 2:
            raise ValueError(f"Did not expect slice element of form {s}")
        start = int(ends[0])
        stop = int(ends[1])
        slicing.append(slice(start, stop))

    return tuple(slicing)


def deserialize_string_from_h5(ds: h5py.Dataset):
    return ds[()].decode()


LazyflowClassifierABC = Union[LazyflowPixelwiseClassifierABC, LazyflowVectorwiseClassifierABC]

LazyflowClassifierTypeABC = Union[Type[LazyflowPixelwiseClassifierABC], Type[LazyflowVectorwiseClassifierABC]]


_lazyflow_classifier_factory_submodule_allow_list = [
    "vigraRfPixelwiseClassifier",
    "vigraRfLazyflowClassifier",
    "parallelVigraRfLazyflowClassifier",
    "sklearnLazyflowClassifier",
]

_lazyflow_classifier_factory_type_allow_list = [
    "VigraRfPixelwiseClassifierFactory",
    "VigraRfLazyflowClassifierFactory",
    "ParallelVigraRfLazyflowClassifierFactory",
    "SklearnLazyflowClassifierFactory",
]

_lazyflow_classifier_type_allow_list = [
    "VigraRfPixelwiseClassifier",
    "VigraRfLazyflowClassifier",
    "ParallelVigraRfLazyflowClassifier",
    "SklearnLazyflowClassifier",
]


@dataclass
class ClassifierInfo:
    submodule_name: str
    type_name: str

    @property
    def classifier_type(self) -> LazyflowClassifierTypeABC:
        submodule = getattr(lazyflow.classifiers, self.submodule_name)
        classifier_type = getattr(submodule, self.type_name)
        return classifier_type


def deserialize_legacy_classifier_type_info(ds: h5py.Dataset) -> ClassifierInfo:
    """Legacy helper for classifier type_info deserialization

    in order to avoid unpickling, the protocol0-style pickle string is
    parsed to extract the classifier typename of the form
    `lazyflow.classifier.myclassifier.MyClassifierType`, e.g.
    `lazyflow.classifier.vigraRfLazyflowClassifier.VigraRfLazyflowClassifier`.

    Args:
      ds: h5py dataset with that holds the pickled string - usually in
          `PixelClassification/ClassifierForests/pickled_type`

    Returns:
      Dictionary with two keys: `submodule_name`, and `typename`

    Raises:
      ValueError if pickled string does not conform to required pattern
    """
    class_string: str = deserialize_string_from_h5(ds)
    classifier_pickle_string_matcher = re.compile(
        r"""
        c                                  # GLOBAL
        lazyflow\.classifiers\.(?P<submodule_name>\w+)
        \n
        (?P<type_name>\w+)
        \n
        p\d+
        \n
        \.                                 # all pickles end in "." STOP
        $
    """,
        re.X,
    )

    # legacy support - ilastik used to pickle the classifier type
    if class_string.isascii() and (m := classifier_pickle_string_matcher.match(class_string)):
        groupdict = m.groupdict()

        if groupdict["submodule_name"] not in _lazyflow_classifier_factory_submodule_allow_list:
            raise ValueError(f"Could not load classifier: submodule {groupdict['submodule_name']} not allowed.")

        if groupdict["type_name"] not in _lazyflow_classifier_type_allow_list:
            raise ValueError(f"Could not load classifier: type {groupdict['type_name']} not allowed.")

        return ClassifierInfo(**groupdict)

    raise ValueError(f"Could not load classifier type {class_string=}")


LazyflowClassifierFactoryABC = Union[LazyflowPixelwiseClassifierFactoryABC, LazyflowVectorwiseClassifierFactoryABC]

LazyflowClassifierFactoryTypeABC = Union[
    Type[LazyflowPixelwiseClassifierFactoryABC], Type[LazyflowVectorwiseClassifierFactoryABC]
]


@dataclass
class ClassifierFactoryTypeInfo:
    factory_submodule: str
    factory_typename: str
    factory_version: int

    @property
    def classifier_factory_type(self) -> LazyflowClassifierFactoryTypeABC:
        submod = getattr(lazyflow.classifiers, self.factory_submodule)
        classifier_factory_type = getattr(submod, self.factory_typename)
        return classifier_factory_type


class ClassifierFactoryInfo(ABC):

    @property
    @abstractmethod
    def instance(self) -> LazyflowClassifierFactoryABC: ...


def deserialize_legacy_classifier_factory(ds: h5py.Dataset) -> LazyflowClassifierFactoryABC:
    pickle_string: str = deserialize_string_from_h5(ds)
    classifier_factory_info = _deserialize_legacy_classifier_factory_type_info(pickle_string)

    classifier_factory_type = classifier_factory_info.classifier_factory_type
    classifier_factory_details = _deserialize_classifier_factory_details(classifier_factory_type, pickle_string)
    factory_instance = classifier_factory_details.instance
    factory_instance.VERSION = classifier_factory_info.factory_version
    return factory_instance


def _deserialize_legacy_classifier_factory_type_info(pickle_string: str) -> ClassifierFactoryTypeInfo:
    """Legacy helper for classifier type_info deserialization

    in order to avoid unpickling, the protocol0-style pickle string is
    parsed to extract the classifier typename of the form
    `lazyflow.classifier.myclassifier.MyClassifierTypeFactory`, e.g.
    `lazyflow.classifier.vigraRfLazyflowClassifier.VigraRfLazyflowClassifierFactory`.

    Args:
      pickle_string: string from pickling a LazyflowClassifierFactory instance

    Returns:
      ClassifierFactoryTypeInfo with classifier information

    Raises:
      ValueError if pickled string does not conform to required pattern
    """

    classifier_factory_pickle_string_matcher = re.compile(
        r"""
        clazyflow\.classifiers\.(?P<factory_submodule>\w+)
        \n
        (?P<type_name>\w+)
        \n
        """,
        re.X,
    )

    classifier_factory_version_pickle_string_matcher = re.compile(
        r"""
        VVERSION\n
        p\d+\n
        I(?P<factory_version>\d+)\n
        """,
        re.X,
    )

    if pickle_string.isascii() and (m := classifier_factory_pickle_string_matcher.search(pickle_string)):
        groupdict = m.groupdict()
        submodule = groupdict["factory_submodule"]
        typename = groupdict["type_name"]

        if submodule not in _lazyflow_classifier_factory_submodule_allow_list:
            raise ValueError(f"Could not load classifier: submodule {submodule} not allowed. {pickle_string=}")

        if typename not in _lazyflow_classifier_factory_type_allow_list:
            raise ValueError(f"Could not load classifier factory: type {typename} not allowed.")
    else:
        raise ValueError(f"Could not load classifier factory type submodule and type not found {pickle_string=}")

    if m := classifier_factory_version_pickle_string_matcher.search(pickle_string):
        version = int(m.groupdict()["factory_version"])
    else:
        raise ValueError(f"Could not load classifier type, no version found {pickle_string=}")

    return ClassifierFactoryTypeInfo(factory_submodule=submodule, factory_typename=typename, factory_version=version)


def _deserialize_classifier_factory_details(
    classifier_factory: LazyflowClassifierFactoryTypeABC, pickle_str: str
) -> ClassifierFactoryInfo:

    if issubclass(classifier_factory, (VigraRfPixelwiseClassifierFactory, VigraRfLazyflowClassifierFactory)):
        return _deserialize_legacy_VigraRfClassifierFactory(pickle_str)

    if issubclass(classifier_factory, ParallelVigraRfLazyflowClassifierFactory):
        return _deserialize_legacy_ParallelVigraRfLazyflowClassifierFactory(pickle_str)

    if issubclass(classifier_factory, SklearnLazyflowClassifierFactory):
        return _deserialize_legacy_SklearnLazyflowClassifierFactory(pickle_str)

    raise ValueError(f"Don't know how to deserialize classifier of type {classifier_factory!r}")


@dataclass
class VigraRfLazyflowClassifierFactoryInfo(ClassifierFactoryInfo):
    args: List[int]

    @property
    def instance(self) -> VigraRfLazyflowClassifierFactory:
        return VigraRfLazyflowClassifierFactory(*self.args)


def _deserialize_legacy_VigraRfClassifierFactory(pickle_string: str) -> VigraRfLazyflowClassifierFactoryInfo:
    """
    These classifier factories have only been used with a single arg
    """
    classifier_factory_args_pickle_string_matcher = re.compile(
        r"""
        V_args\n
        p\d+\n
        (\(I)?
        (?P<arg>(?<=\(I)\d+)\n     # we _only_ expect one integer element in _args for this type
        """,
        re.X,
    )

    if m := classifier_factory_args_pickle_string_matcher.search(pickle_string):
        arg = int(m.groupdict()["arg"])
    else:
        raise ValueError(
            f"Could not load VigraRfLazyflowClassifierFactory, no argument found not found in {pickle_string=}"
        )

    return VigraRfLazyflowClassifierFactoryInfo(args=[arg])


@dataclass
class ParallelVigraRfLazyflowClassifierFactoryInfo(ClassifierFactoryInfo):
    num_trees: int
    label_proportion: Union[float, None]
    variable_importance_path: Union[str, None]
    variable_importance_enabled: bool
    num_forests: int

    # ParallelVigraRfLazyflowClassifierFactory accepts additional kwargs, but we cannot deserialize arbitrary input.
    # The parameters listed are all that we ever used in ilastik history.
    @property
    def instance(self) -> ParallelVigraRfLazyflowClassifierFactory:
        return ParallelVigraRfLazyflowClassifierFactory(
            num_trees_total=self.num_trees,
            num_forests=self.num_forests,
            variable_importance_path=self.variable_importance_path,
            label_proportion=self.label_proportion,
            variable_importance_enabled=self.variable_importance_enabled,
        )


def _deserialize_legacy_ParallelVigraRfLazyflowClassifierFactory(
    pickle_string,
) -> ParallelVigraRfLazyflowClassifierFactoryInfo:
    classifier_factory_num_trees_pickle_string_matcher = re.compile(
        r"""
        V_num_trees\n
        p\d+\n
        I(?P<num_trees>\d+)\n
        """,
        re.X,
    )

    if m := classifier_factory_num_trees_pickle_string_matcher.search(pickle_string):
        num_trees = int(m.groupdict()["num_trees"])
    else:
        raise ValueError(
            f"Could not load ParallelVigraRfLazyflowClassifierFactory, _num_trees not found in {pickle_string=}"
        )

    # this can be None, otherwise float between 0.0 and 1.0
    classifier_factory_label_proportion_pickle_string_matcher = re.compile(
        r"""
        V_label_proportion\n
        p\d+\n
        F?(?P<label_proportion>((?<=F)[01]\.\d+(?=\n))|N(?=s))        # positive lookbehind for float
        """,
        re.X,
    )

    if m := classifier_factory_label_proportion_pickle_string_matcher.search(pickle_string):
        label_prop_string = m.groupdict()["label_proportion"]
        label_proportion = None if label_prop_string == "N" else float(label_prop_string)
    else:
        raise ValueError(
            f"Could not load ParallelVigraRfLazyflowClassifierFactory, _label_proportion not found in {pickle_string=}"
        )

    # this can be None, otherwise string (V)
    classifier_factory_variable_importance_path_pickle_string_matcher = re.compile(
        r"""
        V_variable_importance_path\n
        p\d+\n
        V?(?P<variable_importance_path>((?<=V).+(?=\n))|N(?=s))       # positive lookbehind for string
        """,
        re.X,
    )

    if m := classifier_factory_variable_importance_path_pickle_string_matcher.search(pickle_string):
        variable_importance_pth_string = m.groupdict()["variable_importance_path"]
        variable_importance_path = None if variable_importance_pth_string == "N" else variable_importance_pth_string
    else:
        raise ValueError(
            f"Could not load ParallelVigraRfLazyflowClassifierFactory, _variable_importance_path not found in {pickle_string=}"
        )

    # will be a bool, either I00, or I01
    classifier_factory_variable_importance_enabled_pickle_string_matcher = re.compile(
        r"""
        V_variable_importance_enabled\n
        p\d+\n
        I(?P<variable_importance_enabled>[01]{2})\n
        """,
        re.X,
    )

    if m := classifier_factory_variable_importance_enabled_pickle_string_matcher.search(pickle_string):
        variable_importance_enabled = bool(int(m.groupdict()["variable_importance_enabled"]))
    else:
        raise ValueError(
            f"Could not load ParallelVigraRfLazyflowClassifierFactory, _variable_importance_enabled not found in {pickle_string=}"
        )

    classifier_factory_num_forests_pickle_string_matcher = re.compile(
        r"""
        V_num_forests\n
        p\d+\n
        I(?P<num_forests>\d+)\n
        """,
        re.X,
    )

    if m := classifier_factory_num_forests_pickle_string_matcher.search(pickle_string):
        num_forests = int(m.groupdict()["num_forests"])
    else:
        raise ValueError(
            f"Could not load ParallelVigraRfLazyflowClassifierFactory, _num_forests not found in {pickle_string=}"
        )

    return ParallelVigraRfLazyflowClassifierFactoryInfo(
        num_trees=num_trees,
        label_proportion=label_proportion,
        variable_importance_path=variable_importance_path,
        variable_importance_enabled=variable_importance_enabled,
        num_forests=num_forests,
    )


SklearnClassifierType = Union[
    Type[AdaBoostClassifier],
    Type[DecisionTreeClassifier],
    Type[GaussianNB],
    Type[KNeighborsClassifier],
    Type[LinearDiscriminantAnalysis],
    Type[NuSVC],
    Type[QuadraticDiscriminantAnalysis],
    Type[RandomForestClassifier],
    Type[SVC],
]


@dataclass
class SklearnClassifierTypeInfo:
    submodules: List[str]
    typename: str

    @property
    def classifier_type(self) -> SklearnClassifierType:
        submodule = getattr(sklearn, self.submodules[0])
        for sm_name in self.submodules[1:]:
            submodule = getattr(submodule, sm_name)

        classifier_type = getattr(submodule, self.typename)
        return classifier_type


@dataclass
class SklearnClassifierFactoryInfo(ClassifierFactoryInfo):
    classifier_type: SklearnClassifierType
    args: List[int]
    kwargs: Dict[str, Union[bool, int, float]]

    @property
    def instance(self) -> LazyflowClassifierFactoryABC:
        return SklearnLazyflowClassifierFactory(self.classifier_type, *self.args, **self.kwargs)


def _deserialize_legacy_SklearnLazyflowClassifierFactory(pickle_string) -> SklearnClassifierFactoryInfo:
    """
    _args : RandomForestClassifier, 100 | GaussianNB | AdaBoostClassifier | DecisionTreeClassifier | KNeighborsClassifier | LDA | QDA | SVC | NuSVC
    _kwargs NONE | NONE | n_estimators=100 | max_depth=5 | NONE | N NONE | NONE | probability=True | probability=True
    _classifier_type

    """
    classifier_factory_sklearn_type_pickle_string_matcher = re.compile(
        """
        V_classifier_type\\n
        p\\d+\\n
        c
        sklearn\\.(?P<submodules>[\\w+\\.]+)\\n
        (?P<typename>[\\w]+)\\n
        """,
        re.X,
    )

    sklearn_submodule_allow_list = [
        "discriminant_analysis",
        "ensemble._forest",
        "ensemble._weight_boosting",
        "naive_bayes",
        "neighbors._classification",
        "svm._classes",
        "tree._classes",
    ]

    sklearn_classifier_allow_list = [
        "AdaBoostClassifier",
        "DecisionTreeClassifier",
        "GaussianNB",
        "KNeighborsClassifier",
        "LinearDiscriminantAnalysis",
        "NuSVC",
        "QuadraticDiscriminantAnalysis",
        "RandomForestClassifier",
        "SVC",
    ]

    if m := classifier_factory_sklearn_type_pickle_string_matcher.search(pickle_string):
        groupdict = m.groupdict()
        submodules = groupdict["submodules"]
        typename = groupdict["typename"]

        if submodules not in sklearn_submodule_allow_list or typename not in sklearn_classifier_allow_list:
            raise ValueError(f"Classifier of type sklearn.{submodules}.{typename} not permitted.")

    else:
        raise ValueError(f"Could not load classifier type {pickle_string=}")

    classifier_info = SklearnClassifierTypeInfo(submodules=submodules.split("."), typename=typename)
    classifier_type = classifier_info.classifier_type

    return _deserialize_sklearn_classifier_details(classifier_type, pickle_string)


def _deserialize_sklearn_classifier_details(
    classifier_type: SklearnClassifierType, pickle_str: str
) -> SklearnClassifierFactoryInfo:
    if issubclass(classifier_type, RandomForestClassifier):
        return _deserialize_sklearn_RandomForest_details(pickle_str)

    if issubclass(classifier_type, AdaBoostClassifier):
        return _deserialize_sklearn_AdaBoostClassifier_details(pickle_str)

    if issubclass(classifier_type, DecisionTreeClassifier):
        return _deserialize_sklearn_DecisionTreeClassifier_details(pickle_str)

    if issubclass(classifier_type, (SVC, NuSVC)):
        return _deserialize_sklearn_SVC_details(pickle_str, classifier_type)

    if issubclass(
        classifier_type,
        (
            GaussianNB,
            KNeighborsClassifier,
            LinearDiscriminantAnalysis,
            QuadraticDiscriminantAnalysis,
        ),
    ):
        return SklearnClassifierFactoryInfo(classifier_type=classifier_type, args=[], kwargs={})


def _deserialize_sklearn_RandomForest_details(pickle_str: str) -> SklearnClassifierFactoryInfo:
    classifier_factory_args_pickle_string_matcher = re.compile(
        r"""
        V_args\n
        p\d+\n
        \(
        I(?P<arg>\d+)\n     # we _only_ expect one integer element in _args for this type
        """,
        re.X,
    )

    if m := classifier_factory_args_pickle_string_matcher.search(pickle_str):
        return SklearnClassifierFactoryInfo(
            classifier_type=RandomForestClassifier, args=[int(m.groupdict()["arg"])], kwargs={}
        )
    else:
        raise ValueError("Could not deserialize sklearn RandomForest classifier.")


def _deserialize_sklearn_AdaBoostClassifier_details(pickle_str: str) -> SklearnClassifierFactoryInfo:
    classifier_factory_n_estimators_pickle_string_matcher = re.compile(
        r"""
        Vn_estimators\n
        p\d+\n
        I(?P<n_estimators>\d+)\n
        """,
        re.X,
    )
    if m := classifier_factory_n_estimators_pickle_string_matcher.search(pickle_str):
        return SklearnClassifierFactoryInfo(
            classifier_type=AdaBoostClassifier, args=[], kwargs={"n_estimators": int(m.groupdict()["n_estimators"])}
        )
    else:
        raise ValueError("Could not deserialize sklearn AdaBoostClassifier.")


def _deserialize_sklearn_DecisionTreeClassifier_details(pickle_str: str) -> SklearnClassifierFactoryInfo:
    classifier_factory_max_depth_pickle_string_matcher = re.compile(
        r"""
        Vmax_depth\n
        p\d+\n
        I(?P<max_depth>\d+)\n
        """,
        re.X,
    )
    if m := classifier_factory_max_depth_pickle_string_matcher.search(pickle_str):
        return SklearnClassifierFactoryInfo(
            classifier_type=DecisionTreeClassifier, args=[], kwargs={"max_depth": int(m.groupdict()["max_depth"])}
        )
    else:
        raise ValueError("Could not deserialize sklearn DecisionTreeClassifier")


def _deserialize_sklearn_SVC_details(
    pickle_str: str, classifier_type: Union[Type[SVC], Type[NuSVC]]
) -> SklearnClassifierFactoryInfo:
    classifier_factory_probability_pickle_string_matcher = re.compile(
        r"""
        Vprobability\n
        p\d+\n
        I(?P<probability>[01]{2})\n
        """,
        re.X,
    )
    if m := classifier_factory_probability_pickle_string_matcher.search(pickle_str):
        return SklearnClassifierFactoryInfo(
            classifier_type=classifier_type, args=[], kwargs={"probability": int(m.groupdict()["probability"]) != 0}
        )
    else:
        raise ValueError("Could not deserialize sklearn SVC/NuSVC classifier.")
