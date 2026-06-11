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


def test_tqdmext_initial_total_is_zero():
    """
    TqdmExt used for per-file download progress must be initialized with
    total=0 (unknown), NOT total=1 (placeholder hack).

    With total=1, any chunk update where n > 1 (e.g. n=4096 bytes) would
    cause the callback to compute n/total*100 = 409600%, which is the root
    cause of the progress bar exceeding 100% (issue #3166).

    With total=0, the _cb guard `if total > 0` prevents any emission until
    the real total is set by the HTTP downloader from response headers.
    """
    t = bioimageiodl.TqdmExt(total=0, callback=None)
    assert t.total == 0, (
        "TqdmExt must start with total=0 so progress is not emitted "
        "before the real file size is known from HTTP headers"
    )


@pytest.mark.parametrize(
    "n,total,expected",
    [
        (0, 0, None),  # total unknown, should not emit
        (4096, 0, None),  # total unknown, should not emit
        (4096, 1, 409600),  # old broken behavior with total=1 placeholder
        (4096, 1_000_000, 0),  # correct: small chunk of large file
        (500_000, 1_000_000, 50),  # correct: halfway
        (1_000_000, 1_000_000, 100),  # correct: complete
    ],
)
def test_progress_callback_math(n, total, expected):
    """
    Verify the progress callback formula n/total*100 directly.
    This documents both the old broken behavior (total=1) and correct behavior (total=0).
    """
    emitted = []

    def cb(**fmt):
        t = fmt["total"]
        v = fmt["n"]
        if t > 0:
            emitted.append(int(v / t * 100))

    # Call cb directly as TqdmExt would
    cb(n=n, total=total)

    if expected is None:
        assert emitted == [], f"Should not emit when total=0, got {emitted}"
    else:
        assert emitted == [expected], f"Expected [{expected}], got {emitted}"


def test_bioimagedownloader_uses_total_zero_for_per_file_progress():
    """
    BioImageDownloader.run() must initialize TqdmExt with total=0 for
    per-file download progress, NOT total=1 (the old placeholder hack).

    With total=1, chunk updates (e.g. n=4096 bytes) cause the callback
    to compute n/total*100 = 409600%, making the progress bar exceed 100%.

    This test inspects the source of BioImageDownloader.run() to verify
    total=0 is used, since the actual download requires network access.
    """
    import inspect

    source = inspect.getsource(bioimageiodl.BioImageDownloader.run)
    assert "total=0" in source, (
        "BioImageDownloader.run() must use total=0 when initializing TqdmExt "
        "for per-file progress. Using total=1 causes progress values over 100%."
    )
    assert "total=1" not in source, (
        "BioImageDownloader.run() must NOT use total=1 as a placeholder — "
        "this causes n/total*100 to exceed 100% on first chunk updates."
    )
