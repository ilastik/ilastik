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
#		   http://ilastik.org/license.html
###############################################################################
import numpy as np
import vigra 
import h5py

import pytest

from lazyflow.graph import Graph
from lazyflow.operators.opArrayPiper import OpArrayPiper
from lazyflow.utility import Pipeline

from ilastik.applets.wsdt.opWsdt import OpCachedWsdt

from elf.segmentation.watershed import distance_transform_watershed

DATA_PATH = './data/inputdata/3d2c_Probabilities.h5'
DATASET_NAME = 'exported_data'
AXIS_TAGS = "zyxc"

# Watershed distance transform function parameters.
# Same as the defaults.
WS_PARAMS = {
	'threshold' : 0.5,
	'sigma' : 3.0,
	'min_size' : 100,
	'alpha' : 0.9,
	'pixel_pitch' : None,
	'apply_nonmax_suppression' : False
}

@pytest.fixture
def input_data():
	with h5py.File(DATA_PATH, 'r') as input_file:
		result = np.array(input_file[DATASET_NAME])
		return result

@pytest.fixture
def get_result_function(input_data):
	"""
	Returns the result of the watershed algorithm directly from 
	the core function.
	"""

	ws, max_id = distance_transform_watershed(
						input_data[...,0],
						WS_PARAMS['threshold'],
						WS_PARAMS['sigma'],
						WS_PARAMS['sigma'],
						WS_PARAMS['min_size'],
						WS_PARAMS['alpha'],
						WS_PARAMS['pixel_pitch'],
						WS_PARAMS['apply_nonmax_suppression'])	

	return ws, max_id

@pytest.fixture
def get_result_operator(input_data):
	"""
	Returns the result of the wrapping operator pipeline, which gets 
	accessed via the GUI.
	"""

	input_data = vigra.VigraArray(input_data, axistags=vigra.defaultAxistags(AXIS_TAGS))

	graph = Graph()
	with Pipeline(graph=graph) as get_wsdt:
		get_wsdt.add(OpArrayPiper, Input=input_data)
		get_wsdt.add(OpCachedWsdt, FreezeCache=False)
		wsdt_result = get_wsdt[-1].outputs['Superpixels'][:].wait()

	return wsdt_result

def test_consistency(input_data, get_result_function, get_result_operator):
	"""
	Directly compare pipeline result to core function result. The test will
	pass if the results are exactly equal.
	"""

	ws, max_id = get_result_function
	wsdt_result = np.array(get_result_operator)

	assert np.sum(np.not_equal(ws, wsdt_result[...,0])) == 0, 'Inconsistent results between function and operator wrapper of function!' 
