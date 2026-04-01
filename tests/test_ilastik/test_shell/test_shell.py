from qtpy.QtCore import QRect
from ilastik.shell.gui.ilastikShell import IlastikShell

import pytest
from unittest.mock import patch


@pytest.mark.parametrize(
    "loaded_geometry, screen_geometry, expected_geometry",
    [
        (QRect(10, 10, 100, 100), QRect(0, 0, 1024, 800), QRect(10, 10, 100, 100)),
        (QRect(-10, 10, 100, 100), QRect(0, 0, 1024, 800), QRect(462, 10, 100, 100)),
        (QRect(10, -10, 100, 100), QRect(0, 0, 1024, 800), QRect(10, 350, 100, 100)),
        (QRect(10, 10, 2042, 100), QRect(0, 0, 1024, 800), QRect(0, 10, 1024, 100)),
        (QRect(10, 10, 100, 50000), QRect(0, 0, 1024, 800), QRect(10, 0, 100, 800)),
        (QRect(10, 10, 100, 100), QRect(1042, 0, 1024, 800), QRect(1504, 10, 100, 100)),
        (QRect(10, 10, 100, 100), QRect(1042, 750, 1024, 800), QRect(1504, 1100, 100, 100)),
        (QRect(2000, 50000, 100, 100), QRect(0, 0, 1024, 800), QRect(462, 350, 100, 100)),
    ],
    ids=[
        "fits-in-screen",
        "left-edge-out-of-screen",
        "top-edge-out-of-screen",
        "right-edge-out-of-screen",
        "bottom-edge-out-of-screen",
        "screen-x-nonzero",
        "screen-x-and-y-nonzero",
        "origin-out-of-screen",
    ],
)
def test_valid_screen_geometry(loaded_geometry: QRect, screen_geometry: QRect, expected_geometry: QRect):

    with patch("qtpy.QtWidgets.qApp.primaryScreen") as ps_mock:
        ps_mock.return_value.availableGeometry.return_value = screen_geometry
        resulting_geometry = IlastikShell._valid_screen_geometry(loaded_geometry)
        assert resulting_geometry == expected_geometry
