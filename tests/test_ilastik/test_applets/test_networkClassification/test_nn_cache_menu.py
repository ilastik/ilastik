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
import pathlib
from unittest.mock import MagicMock, patch

import pytest


def test_get_bioimageio_cache_path_from_settings():
    """Uses bioimageio.spec settings when available."""
    from ilastik.applets.neuralNetwork.nnClassGui import get_bioimageio_cache_path

    mock_settings = MagicMock()
    mock_settings.cache_path = "/some/cache/bioimageio"

    with patch.dict("sys.modules", {"bioimageio.spec._internal.settings": MagicMock(settings=mock_settings)}):
        result = get_bioimageio_cache_path()

    assert result == pathlib.Path("/some/cache/bioimageio")


def test_get_bioimageio_cache_path_fallback_on_import_error():
    """Falls back to platformdirs when bioimageio.spec is not installed."""
    from ilastik.applets.neuralNetwork.nnClassGui import get_bioimageio_cache_path

    expected = pathlib.Path("/fallback/cache/bioimageio")

    with patch.dict("sys.modules", {"bioimageio.spec._internal.settings": None}):
        with patch("platformdirs.user_cache_dir", return_value=str(expected)):
            result = get_bioimageio_cache_path()

    assert result == expected


def test_get_bioimageio_cache_path_fallback_on_attribute_error():
    """Falls back to platformdirs when settings has no cache_path attribute."""
    from ilastik.applets.neuralNetwork.nnClassGui import get_bioimageio_cache_path

    expected = pathlib.Path("/fallback/cache/bioimageio")

    mock_module = MagicMock()
    del mock_module.settings  # triggers AttributeError on access

    with patch.dict("sys.modules", {"bioimageio.spec._internal.settings": mock_module}):
        with patch("platformdirs.user_cache_dir", return_value=str(expected)):
            result = get_bioimageio_cache_path()

    assert result == expected


def test_get_bioimageio_cache_path_returns_path_object():
    """Always returns a pathlib.Path regardless of source."""
    from ilastik.applets.neuralNetwork.nnClassGui import get_bioimageio_cache_path

    with patch.dict("sys.modules", {"bioimageio.spec._internal.settings": None}):
        with patch("platformdirs.user_cache_dir", return_value="/any/path"):
            result = get_bioimageio_cache_path()

    assert isinstance(result, pathlib.Path)
