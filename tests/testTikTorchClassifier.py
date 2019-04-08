###############################################################################
#   lazyflow: data flow based lazy parallel computation framework
#
#       Copyright (C) 2011-2017, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the Lesser GNU General Public License
# as published by the Free Software Foundation; either version 2.1
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# See the files LICENSE.lgpl2 and LICENSE.lgpl3 for full text of the
# GNU Lesser General Public License version 2.1 and 3 respectively.
# This information is also available on the ilastik web site at:
#          http://ilastik.org/license/
###############################################################################
"""
Tests prediction-only classifiers, like the NN one
"""
import os
import shutil
import tempfile

import h5py
import nose
import numpy
import vigra

# Don't run the tests on systems that are unprepared
try:
    import torch
    import inferno
    import tiktorch
except ImportError as e:
    raise nose.SkipTest("Necessary NN modules not available.")

from lazyflow.graph import Graph
from lazyflow.classifiers import TikTorchLazyflowClassifier

from tiktorch.utils import TinyConvNet3D, TinyConvNet2D
from tiktorch.wrapper import TikTorch


class TestDummyTikTorchNet(object):
    @classmethod
    def setup_class(cls):
        cls.graph = Graph()
        cls.model = TinyConvNet2D(num_input_channels=1, num_output_channels=2)
        cls.tiktorch_net = TikTorch(model=cls.model)
        # HACK: Window size catered to settings in tiktorchLazyflowClassifier :/
        cls.tiktorch_net.configure(window_size=[192, 192], num_input_channels=1, num_output_channels=2)

        # HACK: this is also catered to the hardcoded settings in tiktorchLazyflowClassifier
        cls.data = numpy.arange(3 * 192 * 192).astype(numpy.uint8).reshape((3, 1, 192, 192))

        cls.tmp_dir = tempfile.mkdtemp()
        cls.h5_file = h5py.File(os.path.join(cls.tmp_dir, "h5_file.h5"), mode="a")
        cls.classifier_group = cls.h5_file.create_group("classifier")

    @classmethod
    def teardown_class(cls):
        if os.path.exists(cls.tmp_dir):
            shutil.rmtree(cls.tmp_dir)

    def test_classifier_construction(self):
        file_name = None

        classifier = TikTorchLazyflowClassifier(self.tiktorch_net, filename=file_name)

        assert len(classifier.known_classes) == self.tiktorch_net.get("num_output_channels")
        # TODO: test more stuff ;)

    def test_classifier_serialization_derserialization(self):
        file_name = None
        classifier = TikTorchLazyflowClassifier(self.tiktorch_net, filename=file_name)
        classifier.serialize_hdf5(self.classifier_group)

        assert self.classifier_group["pytorch_network_path"].value == ""
        # TODO: test more stuff!

        classifier_deserialized = TikTorchLazyflowClassifier.deserialize_hdf5(self.classifier_group)

        # TODO: add __eq__ to tiktorch?!
        assert str(classifier_deserialized._tiktorch_net.model) == str(self.tiktorch_net.model)

    def test_forward_through_model(self):
        classifier = TikTorchLazyflowClassifier(self.tiktorch_net)

        roi = ((0, 0, 32, 32), (3, 1, 160, 160))

        axistags = vigra.defaultAxistags("zcyx")
        output = classifier.predict_probabilities_pixelwise(self.data, roi, axistags)

        assert output.shape == (3, 2, 128, 128)
        # TODO: test more stuff!
