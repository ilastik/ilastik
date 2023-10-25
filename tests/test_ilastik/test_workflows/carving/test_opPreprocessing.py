###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2019, the ilastik developers
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
# 		   http://ilastik.org/license.html
###############################################################################

import pytest
import numpy as np
import vigra

from pytest import raises
from contextlib import nullcontext as does_not_raise
from lazyflow.graph import Graph
from lazyflow.utility import is_root_cause
from lazyflow.request import RequestError

from ilastik.workflows.carving.opPreprocessing import OpSimpleBlockwiseWatershed


@pytest.mark.parametrize(
    "shape,do_agglo,expectation,exp_root_cause",
    [
        ((9, 9, 9, 9, 1), 0, raises(RequestError), ValueError),
        ((9, 9, 9, 9, 1), 1, raises(RequestError), ValueError),
        ((1, 9, 9, 9, 1), 0, does_not_raise(), None),
        ((1, 9, 9, 9, 1), 1, does_not_raise(), None),
        ((1, 9, 9, 1, 1), 0, does_not_raise(), None),
        ((1, 9, 9, 1, 1), 1, does_not_raise(), None),
        ((1, 9, 1, 1, 1), 0, raises(RequestError), ValueError),
        ((1, 9, 1, 1, 1), 1, raises(RequestError), ValueError),
    ],
)
def test_OpSimpleBlockwiseWatershed_dimensions(shape, do_agglo, expectation, exp_root_cause):
    op = OpSimpleBlockwiseWatershed(graph=Graph())
    input_ = vigra.taggedView(np.zeros(shape, dtype="uint8"), "txyzc")
    op.Input.setValue(input_)
    op.DoAgglo.setValue(do_agglo)
    with expectation as exc_info:
        op.Output[:].wait()
        if exp_root_cause:
            assert is_root_cause(exp_root_cause, exc_info.value)
