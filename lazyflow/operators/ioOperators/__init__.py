# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Copyright 2011-2014, the ilastik developers

from ioOperators import *

# All "Read" operators must come before OpInputDataReader, which uses them.
from opNpyFileReader import *
from opStreamingHdf5Reader import *
from opRESTfulVolumeReader import *
from opBlockwiseFilesetReader import *
from opRESTfulBlockwiseFilesetReader import *

# Try to import the dvid-related operator.
# If it fails, that's okay.
try:
    from opDvidVolume import OpDvidVolume
    from opExportDvidVolume import OpExportDvidVolume
except ImportError as ex:
    # If the exception was not related to dvidclient, then re-raise it.
    if 'dvidclient' not in ex.args[0]:
        raise

from opInputDataReader import *

from opNpyWriter import OpNpyWriter
from opExport2DImage import OpExport2DImage
from opExportMultipageTiff import OpExportMultipageTiff
from opExportMultipageTiffSequence import OpExportMultipageTiffSequence
from opExportSlot import OpExportSlot
from opFormattedDataExport import OpFormattedDataExport

