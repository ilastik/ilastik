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
TODOs TikTorchflowClassifier:
"""
from builtins import range
import pickle as pickle
import tempfile


import numpy
import vigra

from .lazyflowClassifier import LazyflowPixelwiseClassifierABC, LazyflowPixelwiseClassifierFactoryABC
from lazyflow.operators.opReorderAxes import OpReorderAxes
from lazyflow.graph import Graph
from lazyflow.roi import roiToSlice

import logging
logger = logging.getLogger(__name__)

try:
    from tiktorch.wrapper import TikTorch
except ImportError as e:
    print(e)


# FIXME: hard coded file path to a trained and pickled pytorch network!
# PYTORCH_MODEL_FILE_PATH = '/Users/chaubold/opt/miniconda/envs/ilastik-py3/src/tiktorch/test3.nn'
# PYTORCH_MODEL_FILE_PATH = '/Users/jmassa/Downloads/dnunet-cpu-chaubold.nn'


class TikTorchLazyflowClassifierFactory(LazyflowPixelwiseClassifierFactoryABC):
    # The version is used to determine compatibility of pickled classifier factories.
    # You must bump this if any instance members are added/removed/renamed.
    VERSION = 1

    def __init__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs

        print (self._args)

        # FIXME: hard coded file path to a trained and pickled pytorch network!
        self._filename = None # self._args[0]
        self._loaded_pytorch_net = None

    def create_and_train_pixelwise(self, feature_images, label_images, axistags=None, feature_names=None):
        self._filename = PYTORCH_MODEL_FILE_PATH
        logger.debug('Loading pytorch network from {}'.format(self._filename))

        # Save for future reference
        # known_labels = numpy.sort(vigra.analysis.unique(y))

        # TODO: check whether loaded network has the same number of classes as specified in ilastik!
        self._loaded_pytorch_net = TikTorch.unserialize(self._filename)
        logger.info(self.description)

        # logger.info("OOB during training: {}".format( oob ))
        return TikTorchLazyflowClassifier(self._loaded_pytorch_net, self._filename)

    def get_halo_shape(self, data_axes='zyxc'):
        # return (z_halo, y_halo, x_halo, 0)
        if len(data_axes) == 4:
            return (0, 32, 32, 0)
        # FIXME: assuming 'yxc' !
        elif len(data_axes) == 3:
            return (32, 32, 0)

    @property
    def description(self):
        if self._loaded_pytorch_net:
            return (
                f"pytorch network loaded from {self._filename} with "
                f"expected input shape {self._loaded_pytorch_net.expected_input_shape} and "
                f"output shape {self._loaded_pytorch_net.expected_output_shape}"
            )
        else:
            return f"pytorch network loading from {self._filename} failed"

    def estimated_ram_usage_per_requested_predictionchannel(self):
        # FIXME: compute from model size somehow??
        return numpy.inf

    def __eq__(self, other):
        return (isinstance(other, type(self)) and
                self._args == other._args and
                self._kwargs == other._kwargs
        )

    def __ne__(self, other):
        return not self.__eq__(other)


assert issubclass(TikTorchLazyflowClassifierFactory, LazyflowPixelwiseClassifierFactoryABC)


class TikTorchLazyflowClassifier(LazyflowPixelwiseClassifierABC):
    HDF5_GROUP_FILENAME = 'pytorch_network_path'
    # TODO: parametrize!
    HALO_SIZE = 32
    # TODO: parametrize!
    BATCH_SIZE = 3

    def __init__(self, tiktorch_net, filename=None):
        """
        Args:
            tiktorch_net (tiktorch): tiktorch object to be loaded into this
              classifier object
            filename (None, optional): Save file name for future reference
        """
        self._filename = filename
        if self._filename is None:
            self._filename = ""



        if tiktorch_net is None:
            print (self._filename)
            tiktorch_net = TikTorch.unserialize(self._filename)

        # print (self._filename)

        # assert tiktorch_net.return_hypercolumns == False
        # print('blah')

        self._tiktorch_net = tiktorch_net

        self._opReorderAxes = OpReorderAxes(graph=Graph())
        self._opReorderAxes.AxisOrder.setValue('zcyx')

    def predict_probabilities_pixelwise(self, feature_image, roi, axistags=None):
        """
        Implicitly assumes that feature_image is includes the surrounding HALO!
        roi must be chosen accordingly
        """
        logger.info(f'predicting using pytorch network for image of shape {feature_image.shape} and roi {roi}')
        logger.info(f"Stats of input: min={feature_image.min()}, max={feature_image.max()}, mean={feature_image.mean()}")
        logger.info(f'expected pytorch input shape is {self._tiktorch_net.expected_input_shape}')
        logger.info(f'expected pytorch output shape is {self._tiktorch_net.expected_output_shape}')

        # print(self._tiktorch_net.expected_input_shape)
        # print(self._tiktorch_net.expected_output_shape)

        num_channels = len(self.known_classes)
        expected_shape = [stop - start for start, stop in zip(roi[0], roi[1])] + [num_channels]

        self._opReorderAxes.Input.setValue(vigra.VigraArray(feature_image, axistags=axistags))
        self._opReorderAxes.AxisOrder.setValue('zcyx')
        reordered_feature_image = self._opReorderAxes.Output([]).wait()

        # normalizing patch
        # reordered_feature_image = (reordered_feature_image - reordered_feature_image.mean()) / (reordered_feature_image.std() + 0.000001)

        logger.info(
            f'input axistags are {axistags}, '
            f'Shape after reordering input is {reordered_feature_image.shape}, '
            f'axistags are {self._opReorderAxes.Output.meta.axistags}')

        slice_shape = list(reordered_feature_image.shape[1::])  # ignore z axis
        # assuming [z, y, x]
        result_roi = numpy.array(roi)
        if slice_shape != list(self._tiktorch_net.expected_input_shape[1::]):
            logger.info(
                f"Expected input shape is {self._tiktorch_net.expected_input_shape[1::]}, "
                f"but got {slice_shape}, reshaping...")

            # adding a zero border to images that have the specific shape

            exp_shape = list(self._tiktorch_net.expected_input_shape)
            zero_img = numpy.zeros(exp_shape)

            # diff shape: cyx
            diff_shape = numpy.array(self._tiktorch_net.expected_input_shape[1::]) - numpy.array(slice_shape)
            # offset shape z, y, x, c for easy indexing, with c = 0, z = 0
            offset = numpy.array([0, 0, 0, 0])
            logger.info(f"Diff_shape {diff_shape}")

            # at least one of y, x (diff_shape[1], diff_shape[2]) should be off
            # let's determine how to adjust the offset -> offset[2] and offset[3]
            # caveat: this code assumes that image requests were tiled in a regular
            # pattern starting from left upper corner.
            # We use a blocked array-cache to achieve that
            # y-offset:
            if diff_shape[1] > 0:
                # was the halo added to the upper side of the feature image?
                # HACK: this only works because we assume the data to be in zyx!!!
                if roi[0][1] == 0:
                    # no, doesn't seem like it
                    offset[1] = self.HALO_SIZE

            # x-offsets:
            if diff_shape[2] > 0:
                # was the halo added to the upper side of the feature image?
                # HACK: this only works because we assume the data to be in zyx!!!
                if roi[0][2] == 0:
                    # no, doesn't seem like it
                    offset[2] = self.HALO_SIZE

            # HACK: still assuming zyxc
            result_roi[0] += offset[0:3]
            result_roi[1] += offset[0:3]
            reorder_feature_image_extents = numpy.array(reordered_feature_image.shape)
            # add the offset:
            reorder_feature_image_extents[2:4] += offset[1:3]
            zero_img[:, :, offset[1]:reorder_feature_image_extents[2], offset[2]:reorder_feature_image_extents[3]] = \
                reordered_feature_image

            reordered_feature_image = zero_img

            logger.info(f"New Image shape {reordered_feature_image.shape}")

        result = numpy.zeros(
            [reordered_feature_image.shape[0], num_channels] + list(reordered_feature_image.shape[2:]))

        logger.info(f"forward")

        # we always predict in 2D, per z-slice, so we loop over z
        for z in range(0, reordered_feature_image.shape[0], self.BATCH_SIZE):
            # logger.warning("Dumping to {}".format('"/Users/chaubold/Desktop/dump.h5"'))
            # vigra.impex.writeHDF5(reordered_feature_image[z,...], "data", "/Users/chaubold/Desktop/dump.h5")

            # create batch of desired num slices. Multiple slices can be processed on multiple GPUs!
            batch = [reordered_feature_image[zi:zi + 1, ...].reshape(self._tiktorch_net.expected_input_shape)
                     for zi in range(z, min(z + self.BATCH_SIZE, reordered_feature_image.shape[0]))]
            logger.info(f"batch info: {[x.shape for x in batch]}")

            print("batch info:", [x.shape for x in batch])

            result_batch = self._tiktorch_net.forward(batch)
            logger.info(f"Resulting slices from {z} to {z + len(batch)} have shape {result_batch[0].shape}")

            print("Resulting slices from ",z ," to ", z + len(batch), " have shape ",result_batch[0].shape)

            for i, zi in enumerate(range(z, (z + len(batch)))):
                result[zi:(zi + 1), ...] = result_batch[i]

        logger.info(f"Obtained a predicted block of shape {result.shape}")

        print ("Obtained a predicted block of shape ", result.shape)

        self._opReorderAxes.Input.setValue(vigra.VigraArray(result, axistags=vigra.makeAxistags('zcyx')))
        # axistags is vigra.AxisTags, but opReorderAxes expects a string
        self._opReorderAxes.AxisOrder.setValue(''.join(axistags.keys()))
        result = self._opReorderAxes.Output([]).wait()
        logger.info(f"Reordered result to shape {result.shape}")

        # FIXME: not needed for real neural net results:
        logger.info(f"Stats of result: min={result.min()}, max={result.max()}, mean={result.mean()}")

        # cut out the required roi
        logger.info(f"Roi shape {result_roi}")

        # crop away halo and reorder axes to match "axistags"
        # crop in X and Y:
        cropped_result = result[roiToSlice(*result_roi)]

        logger.info(f"cropped the predicted block to shape {cropped_result.shape}")

        return cropped_result

    @property
    def known_classes(self):
        return list(range(self._tiktorch_net.expected_output_shape[0]))

    @property
    def feature_count(self):
        return self._tiktorch_net.expected_input_shape[0]

    def get_halo_shape(self, data_axes='zyxc'):
        if len(data_axes) == 4:
            return (0, self.HALO_SIZE, self.HALO_SIZE, 0)
        # FIXME: assuming 'yxc' !
        elif len(data_axes) == 3:
            return (self.HALO_SIZE, self.HALO_SIZE, 0)

    def serialize_hdf5(self, h5py_group):
        logger.debug('Serializing')
        h5py_group[self.HDF5_GROUP_FILENAME] = self._filename
        h5py_group['pickled_type'] = pickle.dumps(type(self), 0)

        # HACK: can this be done more elegantly?
        with tempfile.TemporaryFile() as f:
            self._tiktorch_net.serialize(f)
            f.seek(0)
            h5py_group['classifier'] = numpy.void(f.read())

    @classmethod
    def deserialize_hdf5(cls, h5py_group):
        # TODO: load from HDF5 instead of hard coded path!
        logger.debug('Deserializing')
        # HACK:
        # filename = PYTORCH_MODEL_FILE_PATH
        filename = h5py_group[cls.HDF5_GROUP_FILENAME]
        logger.debug("Deserializing from {}".format(filename))

        with tempfile.TemporaryFile() as f:
            f.write(h5py_group['classifier'].value)
            f.seek(0)
            loaded_pytorch_net = TikTorch.unserialize(f)

        return TikTorchLazyflowClassifier(loaded_pytorch_net, filename)


assert issubclass(TikTorchLazyflowClassifier, LazyflowPixelwiseClassifierABC)
