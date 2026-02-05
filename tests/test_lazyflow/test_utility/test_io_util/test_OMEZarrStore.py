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
import asyncio
from unittest import mock

import fsspec.implementations.http
import pytest
import s3fs
from aiohttp import ClientResponseError

from lazyflow.utility.io_util.OMEZarrStore import NoOMEZarrMetaFound, OMEZarrStore


def test_handles_wrapped_connection_error(monkeypatch):
    # zarr.storage.FSStore raises a ClientConnectorError wrapped in a KeyError
    # when the web connection fails. We handle this by re-raising as ConnectionError.
    # Check that it hasn't changed in the zarr library.
    f = asyncio.Future()
    f.set_result("{}")
    monkeypatch.setattr(fsspec.implementations.http.HTTPFileSystem, "_cat_file", lambda _, __: f)
    with pytest.raises(NoOMEZarrMetaFound):
        OMEZarrStore(f"https://nonexistent-address.zarr.foobar123")


@pytest.fixture
def count_s3fs_instances(monkeypatch):
    # Simply patching __init__ with a mock is iffy because fsspec does custom imports
    s3fs.core.S3FileSystem.instance_counter = 0
    s3fs_init = s3fs.core.S3FileSystem.__init__

    def track_instances(*args, **kwargs):
        s3fs.core.S3FileSystem.instance_counter += 1
        return s3fs_init(*args, **kwargs)

    monkeypatch.setattr(s3fs.core.S3FileSystem, "__init__", track_instances)
    # Prevent actually sending web requests
    f = asyncio.Future()
    f.set_result("{}")
    monkeypatch.setattr(s3fs.core.S3FileSystem, "_cat_file", lambda _, __: f)

    return track_instances


@pytest.fixture
def mock_httpfs_403(monkeypatch):
    # Mimics what happens when an S3-compatible store is accessed with a default fsspec HTTPFileSystem
    # E.g. when passing "https://s3.embl.de/bucket/file" to zarr.storage.FSStore
    def raise_403(_, __):
        raise ClientResponseError(status=403, request_info=mock.Mock(), history=mock.Mock())

    monkeypatch.setattr(fsspec.implementations.http.HTTPFileSystem, "_cat_file", raise_403)


def test_maps_https_scheme_to_s3fs_on_403(count_s3fs_instances, mock_httpfs_403):
    with pytest.raises(NoOMEZarrMetaFound):
        OMEZarrStore(f"https://localhost/bucket/some.zarr")
    assert s3fs.core.S3FileSystem.instance_counter == 1
