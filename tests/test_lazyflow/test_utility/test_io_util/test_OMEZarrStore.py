###############################################################################
#   lazyflow: data flow based lazy parallel computation framework
#
#       Copyright (C) 2011-2024, the ilastik developers
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
# 		   http://ilastik.org/license/
###############################################################################
import pytest

from lazyflow.utility.io_util.OMEZarrStore import OMEZarrStore


def test_OMEZarrStore_handles_wrapped_connection_error():
    # zarr.storage.FSStore raises a ClientConnectorError wrapped in a KeyError
    # when the web connection fails. We handle this by re-raising as ConnectionError.
    # Check that it hasn't changed in the zarr library.
    nonsense_host = "nonexistent-address.zarr.foobar123"
    with pytest.raises(ConnectionError, match=nonsense_host):
        OMEZarrStore(f"https://{nonsense_host}")
