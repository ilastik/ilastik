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


def chooseChunkShape(outerShape, desiredChunkSize):
    '''
    Choose a chunk shape that
      * is less than or equal the desired chunk size
      * respects the aspect ratio of the outer shape
    Note that you will most likely have to handle channel and time dimension
    differently (i.e. set them to 1 or max).
    Each dimension will be at least 1 and at most the outer shape.
    
    @param outerShape the shape of the volume as tuple of ints
    @param desiredChunkSize the chunk size in pixels (not bytes!)
    @return the 'optimal' chunk shape as tuple of ints
    '''

    x = np.array(outerShape, dtype=np.int)
    assert np.all(x > 0)
    size = np.prod(x)
    n = len(x)
    assert n > 0
    if desiredChunkSize >= size:
        return tuple(x)
    if desiredChunkSize <= 0:
        return (1,)*n

    # determine the factor (f*y_1 * ... f*y_n = x_1 * ... * x_n)
    # y_1 * ... * y_n = desiredChunkSize
    # x_1 * ... * x_n = size
    # f^n = size/desiredChunkSize
    f = np.power(size/float(desiredChunkSize), 1/float(n))
    
    y = np.floor(x/f)
    y = np.maximum(y, 1).astype(np.int)
    return tuple(y)
