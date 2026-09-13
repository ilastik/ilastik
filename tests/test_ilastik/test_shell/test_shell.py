from qtpy.QtCore import QRect
from ilastik.shell.gui.ilastikShell import IlastikShell
from ilastik.shell.projectManager import ProjectManager

import h5py
import os
import pytest
import tempfile
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


def test_createAndLoadNewProject_shows_dialog_on_oserror():
    """
    When createBlankProjectFile raises an OSError (e.g. file locked by another
    process), createAndLoadNewProject should show a QMessageBox.critical dialog
    and return early without attempting to load the project.

    Fixes #3098: Trying to overwrite locked project file fails silently.
    """
    from unittest.mock import MagicMock, patch

    shell = MagicMock(spec=IlastikShell)
    shell._workflow_cmdline_args = []

    with (
        patch(
            "ilastik.shell.gui.ilastikShell.ProjectManager.createBlankProjectFile",
            side_effect=OSError("Unable to lock file"),
        ),
        patch("ilastik.shell.gui.ilastikShell.QMessageBox.critical") as mock_critical,
    ):
        IlastikShell.createAndLoadNewProject(shell, "/fake/path/project.ilp", MagicMock())

    # Error dialog must have been shown
    mock_critical.assert_called_once()
    args = mock_critical.call_args[0]
    assert "Failed to create project file" in args[1]
    assert "/fake/path/project.ilp" in args[2]

    # Project must NOT have been loaded
    shell._loadProject.assert_not_called()


def test_createBlankProjectFile_does_not_corrupt_locked_file():
    """
    When the target file exists but is locked by another process,
    createBlankProjectFile must raise an OSError and leave the original
    file intact (not truncate/corrupt it).

    Regression test for https://github.com/ilastik/ilastik/issues/3235
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = os.path.join(tmpdir, "test.ilp")

        # Create a valid project file first
        with h5py.File(project_path, "w") as f:
            f.create_dataset("ilastikVersion", data=b"1.4.2")
            f.create_dataset("workflowName", data=b"PixelClassification")
        original_size = os.path.getsize(project_path)
        assert original_size > 0

        # Simulate the file being locked by another process:
        # Patch h5py.File so that opening in "r" mode raises OSError (locked),
        # while "w" mode is also blocked to prevent actual truncation.
        real_h5py_file = h5py.File

        def mock_h5py_file(name, mode="r", *args, **kwargs):
            if mode == "r" and str(name) == project_path:
                raise OSError("Unable to synchronously open file (unable to lock file)")
            return real_h5py_file(name, mode, *args, **kwargs)

        with patch("ilastik.shell.projectManager.h5py.File", side_effect=mock_h5py_file):
            with pytest.raises(OSError, match="locked by another process"):
                ProjectManager.createBlankProjectFile(project_path)

        # Verify the file was NOT corrupted - still has original size and is readable
        assert os.path.getsize(project_path) == original_size
        with h5py.File(project_path, "r") as f:
            assert "ilastikVersion" in f
            assert f["ilastikVersion"][()] == b"1.4.2"
