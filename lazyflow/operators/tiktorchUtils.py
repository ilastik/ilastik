###############################################################################
#   lazyflow: data flow based lazy parallel computation framework
#
#       Copyright (C) 2011-2014, the ilastik developers
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
#		   http://ilastik.org/license/
###############################################################################

import numpy as np

# TikTorch
from tiktorch.blockinator import slicey, np_pad

class IlastikBlockinator(object):

    def __init__(self, data_slot, halo, pad_fn=np_pad):
        # Publics
        self.data = data_slot # Image InputSlot
        self.base_block = halo
        self.pad_fn = pad_fn

    @property
    def block_shape(self):
        return self.base_block

    @property
    def spatial_shape(self):
        # return self.data.shape[:]
        return self.data.meta.shape[:]

    @property
    def num_blocks(self):
        return tuple(shape // size for shape, size in zip(self.spatial_shape, self.block_shape))

    def get_slice(self, *block):
        return tuple(slice(_size * _block, _size * (_block + 1))
                     for _block, _size in zip(block, self.block_shape))

    def space_cake(self, *slices):
        # This function slices the data, and adds a halo if requested.
        # Convert all slice to sliceys
        slices = [slicey.from_(sl) for sl in slices]
        # Pad out-of-array values
        # Get unpadded volume
        unpadded_volume = self.data[tuple(sl.slice for sl in slices)].wait()
        padding = [sl.padding for sl in slices]
        padded_volume = self.pad_fn(unpadded_volume, padding)
        return padded_volume

    def fetch(self, item):
        if isinstance(item, np.ndarray):
            full_slice = [slice(start, stop, None) for start, stop in zip(item[0], item[1])]

        halo = self.base_block

        if halo is not None:
            assert len(halo) == len(self.spatial_shape)
            spatial_padding = [(elem,) * 2 for elem in halo]
            sliceys = [slicey.from_(_sl, _padding, _shape)
                       for _sl, _padding, _shape in zip(full_slice, spatial_padding,
                                                        self.spatial_shape)]
            sliced = self.space_cake(*sliceys)
        else:
            sliced = self.space_cake(*full_slice)
        return sliced

    def __getitem__(self, item):
        return self.fetch(item)

if __name__ == '__main__':
    blockinator = IlastikBlockinator(data_slot=np.random.randn(20, 1250, 1250, 1),
                                     halo=[5, 32, 32, 0],
                                     roi=np.array([[9, 0, 768, 0], [10, 256, 1024, 1]]),
                                     pad_fn=np_pad)
    roi = np.array([[8, 0, 768, 0], [10, 256, 1024, 1]])
    out = blockinator[roi]
    

    x = 6
