###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2026, the ilastik developers
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
import json
from dataclasses import dataclass
from typing import Annotated, Any, List, LiteralString, OrderedDict, TypeVar, Tuple

import annotated_types
import h5py
import numpy
import numpy.typing as npt
from pydantic import BaseModel, BeforeValidator, StringConstraints

from ilastik.applets.base.appletSerializer.legacyClassifiers import (
    deserialize_classifier,
    deserialize_classifier_factory,
)
from ilastik.applets.base.appletSerializer.serializerUtils import deserialize_string_from_h5
from lazyflow.classifiers.lazyflowClassifier import (
    LazyflowVectorwiseClassifierABC,
    LazyflowVectorwiseClassifierFactoryABC,
)


@dataclass
class _VigraAxisTags:
    key: str
    typeFlags: int
    resolution: int
    description: str


def deserialize_arraylike_from_h5(ds: h5py.Dataset) -> Any:
    return ds[()]


def deserialize_axistags(at_str: str) -> List[_VigraAxisTags]:
    return [_VigraAxisTags(**at) for at in json.loads(at_str)["axes"]]


def deserialize_str_list_from_h5(str_list: h5py.Dataset) -> List[str]:
    return [x.decode() for x in str_list]


LaneName = Annotated[str, StringConstraints(pattern=r"lane\d{4}")]
NDShape = Annotated[Tuple[int, ...], annotated_types.Len(2, 6)]
VigraAxisTags = Annotated[List[_VigraAxisTags], BeforeValidator(deserialize_axistags)]

Tnpdt = TypeVar("Tnpdt", numpy.bool_, numpy.int64, numpy.float64)
Ts = TypeVar("Ts", bound=LiteralString)

T = TypeVar("T")

H5Array = Annotated[npt.NDArray[Tnpdt], BeforeValidator(deserialize_arraylike_from_h5)]
H5Classifier = Annotated[
    LazyflowVectorwiseClassifierABC,
    BeforeValidator(deserialize_classifier),
]
H5ClassifierFactory = Annotated[LazyflowVectorwiseClassifierFactoryABC, BeforeValidator(deserialize_classifier_factory)]
H5List = Annotated[list[T], BeforeValidator(deserialize_arraylike_from_h5)]
H5Literal = Annotated[Ts, BeforeValidator(deserialize_string_from_h5)]
H5NDShape = Annotated[
    NDShape, BeforeValidator(lambda x: tuple(x.tolist())), BeforeValidator(deserialize_arraylike_from_h5)
]
H5String = Annotated[str, BeforeValidator(deserialize_string_from_h5)]
H5VigraAxisTags = Annotated[VigraAxisTags, BeforeValidator(deserialize_string_from_h5)]


class DatasetInfo(BaseModel):
    axistags: H5VigraAxisTags
    shape: H5NDShape

    @property
    def tagged_shape(self) -> OrderedDict[str, int]:
        return OrderedDict((tag.key, size) for tag, size in zip(self.axistags, self.shape))
