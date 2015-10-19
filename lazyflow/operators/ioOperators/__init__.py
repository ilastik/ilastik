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
from ioOperators import OpStackLoader, OpStackWriter, OpStackToH5Writer, OpH5WriterBigDataset

# All "Read" operators must come before OpInputDataReader, which uses them.
from opStreamingMmfReader import OpStreamingMmfReader
from opStreamingUfmfReader import OpStreamingUfmfReader
from opRawBinaryFileReader import OpRawBinaryFileReader
from opNpyFileReader import OpNpyFileReader
from opStreamingHdf5Reader import OpStreamingHdf5Reader
from opRESTfulVolumeReader import OpRESTfulVolumeReader
from opBlockwiseFilesetReader import OpBlockwiseFilesetReader
from opRESTfulBlockwiseFilesetReader import OpRESTfulBlockwiseFilesetReader
from opTiledVolumeReader import OpTiledVolumeReader
from opCachedTiledVolumeReader import OpCachedTiledVolumeReader

# Try to import the dvid-related operator.
# If it fails, that's okay.
try:
    from opDvidVolume import OpDvidVolume
    from opDvidRoi import OpDvidRoi
    from opExportDvidVolume import OpExportDvidVolume
except ImportError as ex:
    # If the exception was not related to libdvid, then re-raise it.
    if 'libdvid' not in ex.args[0]:
        raise

from opInputDataReader import *

from opNpyWriter import OpNpyWriter
from opExport2DImage import OpExport2DImage
from opExportMultipageTiff import OpExportMultipageTiff
from opExportMultipageTiffSequence import OpExportMultipageTiffSequence
from opExportToArray import OpExportToArray
from opExportSlot import OpExportSlot
from opFormattedDataExport import OpFormattedDataExport

from hdf5SerializerKnime import *
from opExportToKnime import OpExportToKnime

