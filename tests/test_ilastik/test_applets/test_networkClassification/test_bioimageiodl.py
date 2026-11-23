###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2026, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
#          http://ilastik.org/license.html
###############################################################################
from pathlib import Path
from typing import Iterator
from zipfile import ZipFile

import pytest

try:
    import tiktorch
except ImportError:
    pytest.skip("Need tiktorch dependency to run `bioimageiodl` tests.", allow_module_level=True)

from ilastik.applets.neuralNetwork import bioimageiodl


@pytest.fixture(
    params=[("some_file.txt", False), ("not_a_real_zip.zip", False), ("real_zip.zip", True)],
    ids=["some_file.txt", "not_a_real_zip.zip", "real_zip.zip"],
)
def existing_files(tmp_path: Path, request) -> Iterator[tuple[Path, bool]]:
    fname, expected = request.param
    fn = tmp_path / fname

    if fname == "real_zip.zip":
        with ZipFile(fn, mode="w") as zip_file:
            zip_file.writestr("test.file", data="Hello World")

    yield fn, expected


@pytest.mark.parametrize(
    "pattern",
    [
        "https:/https://files.ilastik.org/ilastik-1.4.1-OSX.zip",
        "/Users/ilastik/test.zip",
        "myzip.zip",
        "affable-shark",
    ],
)
def test_is_zipfile_returns_false_nonexisting(pattern: str):
    assert bioimageiodl._is_existing_local_zip_file(Path(pattern)) == False


def test_is_zipfile_with_existing_files(existing_files: tuple[Path, bool]):
    filename, expection = existing_files
    assert bioimageiodl._is_existing_local_zip_file(filename) == expection


def test_progress_callback_skips_when_n_exceeds_total():
    """Progress callback must not emit values > 100% when n > total.

    This happens when the server uses content-encoding (e.g. zstd) and
    httpx transparently decompresses, making decompressed bytes larger
    than Content-Length. Regression test for #3166.
    """
    from unittest.mock import MagicMock

    signal = MagicMock()

    # Replicate the _callback pattern from BioImageDownloader.run()
    def _cb(n: int, total: int, **kwargs):
        if total > 0 and n <= total:
            signal.emit(int(n / total * 100))

    # Normal case: n < total
    _cb(500, 1000)
    signal.emit.assert_called_with(50)

    signal.reset_mock()

    # Exact case: n == total
    _cb(1000, 1000)
    signal.emit.assert_called_with(100)

    signal.reset_mock()

    # Over case: n > total (content-encoding mismatch) - should NOT emit
    _cb(1970, 1000)
    signal.emit.assert_not_called()

    signal.reset_mock()

    # Zero total: should NOT emit
    _cb(0, 0)
    signal.emit.assert_not_called()

    signal.reset_mock()

    # Zero n: should emit 0
    _cb(0, 1000)
    signal.emit.assert_called_with(0)
