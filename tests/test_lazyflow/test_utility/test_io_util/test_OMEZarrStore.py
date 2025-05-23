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
import json
import socket
import threading
import time
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Tuple, Type
from unittest import mock

import fsspec.implementations.http
import numpy
import pytest
import s3fs
import zarr
from aiohttp import ClientResponseError

from lazyflow.utility.io_util.OMEZarrStore import OMEZarrStore, NoOMEZarrMetaFound, OME_ZARR_V_0_4_KWARGS


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


@pytest.fixture
def ome_zarr_store_on_disc(tmp_path) -> str:
    """Sets up a zarr store of a random image at raw scale and a downscale.
    Returns the store's subdir under tmp_path"""
    subdir = "some.zarr"
    zarr_dir = tmp_path / subdir
    zarr_dir.mkdir(parents=True, exist_ok=True)

    dataset_shape = [3, 100, 100]  # cyx - to match the 2d3c project
    chunk_size = [3, 64, 64]
    zattrs = {
        "multiscales": [
            {
                "version": "0.4",
                "axes": [{"name": "c"}, {"name": "y"}, {"name": "x"}],
                "datasets": [
                    {
                        "path": "s0",
                        "coordinateTransformations": [
                            {"scale": [1.0, 1.0, 1.0], "type": "scale"},
                        ],
                    },
                    {
                        "path": "s1",
                        "coordinateTransformations": [
                            {"scale": [1.0, 2.0, 2.0], "type": "scale"},
                        ],
                    },
                ],
            }
        ]
    }
    (zarr_dir / ".zattrs").write_text(json.dumps(zattrs))

    image_original = numpy.random.randint(0, 256, dataset_shape, dtype=numpy.uint16)
    image_scaled = image_original[:, ::2, ::2]
    chunks = tuple(chunk_size)
    zarr.array(image_original, chunks=chunks, store=zarr.DirectoryStore(str(zarr_dir / "s0")), **OME_ZARR_V_0_4_KWARGS)
    zarr.array(image_scaled, chunks=chunks, store=zarr.DirectoryStore(str(zarr_dir / "s1")), **OME_ZARR_V_0_4_KWARGS)

    return subdir


def wait_for_server(host_and_port: Tuple[str, int], timeout=5):
    end_time = time.time() + timeout
    while time.time() < end_time:
        try:
            with socket.create_connection(host_and_port, timeout=1):
                return True
        except OSError:
            time.sleep(0.1)
    raise RuntimeError(f"Server on {':'.join(host_and_port)} didn't start within {timeout} seconds")


def run_server_in_separate_thread(
    handler_class: Type[SimpleHTTPRequestHandler], path: Path
) -> Tuple[HTTPServer, threading.Thread]:
    """Serves `path` on a random open port under localhost, handling requests with `handler_class`."""
    handler = partial(handler_class, directory=str(path))
    server = HTTPServer(("localhost", 0), handler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True  # Allows the server to be killed after the test ends
    thread.start()
    wait_for_server(("localhost", server.server_port))
    return server, thread


@pytest.fixture
def slow_ome_zarr_server(tmp_path, ome_zarr_store_on_disc) -> str:
    class SlowHTTPRequestHandler(SimpleHTTPRequestHandler):
        def do_GET(self):
            # This delays calls to aiohttp.client.ClientSession.get,
            # as done once per file in zarr.implementations.http.HTTPFileSystem._cat_file.
            time.sleep(1)
            super().do_GET()

    server, thread = run_server_in_separate_thread(SlowHTTPRequestHandler, tmp_path)

    yield f"http://localhost:{server.server_port}/{ome_zarr_store_on_disc}"

    server.shutdown()
    thread.join()


def test_handles_slow_connection(tmp_path, graph, ome_zarr_store_on_disc, slow_ome_zarr_server):
    all_roi = mock.Mock()
    all_roi.toSlice = lambda: (slice(None), slice(None), slice(None))
    store = OMEZarrStore(slow_ome_zarr_server)
    data = store.request(all_roi)
    expected_content = zarr.open(str(tmp_path / ome_zarr_store_on_disc))["s1"]
    assert data.shape == (3, 50, 50)
    numpy.testing.assert_array_equal(data, expected_content)


@pytest.fixture
def dropping_ome_zarr_server(tmp_path, ome_zarr_store_on_disc) -> str:
    class DroppingHTTPRequestHandler(SimpleHTTPRequestHandler):
        request_count = 1  # Class variable because a new handler instance is created for each request

        def do_GET(self):
            # aiohttp.client.ClientSession._request retries once on ServerDisconnectedError already,
            # so need to be worse than dropping every other request to provoke our own retrying.
            if DroppingHTTPRequestHandler.request_count % 4 == 0:
                super().do_GET()
            DroppingHTTPRequestHandler.request_count += 1

    server, thread = run_server_in_separate_thread(DroppingHTTPRequestHandler, tmp_path)

    yield f"http://localhost:{server.server_port}/{ome_zarr_store_on_disc}"

    server.shutdown()
    thread.join()


def test_handles_dropping_connection(tmp_path, graph, ome_zarr_store_on_disc, dropping_ome_zarr_server):
    all_roi = mock.Mock()
    all_roi.toSlice = lambda: (slice(None), slice(None), slice(None))
    store = OMEZarrStore(dropping_ome_zarr_server)
    data = store.request(all_roi)
    expected_content = zarr.open(str(tmp_path / ome_zarr_store_on_disc))["s1"]
    assert data.shape == (3, 50, 50)
    numpy.testing.assert_array_equal(data, expected_content)
