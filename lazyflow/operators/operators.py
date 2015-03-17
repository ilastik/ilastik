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
#third-party dependencies
import psutil
if psutil.__version__ < '0.6':
    raise RuntimeError("lazyflow requires psutil 0.6.  Please upgrade your version of psutil (e.g. easy_install -U psutil)")

#lazyflow
import lazyflow
from lazyflow.rtype import SubRegion
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.roi import sliceToRoi, roiToSlice, TinyVector, getBlockBounds
from lazyflow import request
from lazyflow.utility import Tracer

#various cache operators
from lazyflow.operators.opArrayCache import OpArrayCache
from lazyflow.operators.opArrayPiper import OpArrayPiper
from lazyflow.operators.opBlockedArrayCache import OpBlockedArrayCache
from lazyflow.operators.opSlicedBlockedArrayCache import OpSlicedBlockedArrayCache
from lazyflow.operators.opUnblockedArrayCache import OpUnblockedArrayCache

# Don't import these obsolete label operators by default.
#from lazyflow.operators.opSparseLabelArray import OpSparseLabelArray
#from lazyflow.operators.opBlockedSparseLabelArray import OpBlockedSparseLabelArray
