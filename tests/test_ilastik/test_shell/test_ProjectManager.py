import os
import pytest
import h5py

from ilastik.shell.projectManager import ProjectManager


def test_create_blank_project_file_does_not_truncate_on_lock_error(tmp_path, monkeypatch):
    """
    Regression test for #3098.

    Verifies that if project creation fails due to an HDF5 file lock error,
    the existing project file is not truncated or modified.
    """
    project_path = tmp_path / "locked_project.ilp"

    # Create an existing dummy project file
    with open(project_path, "wb") as f:
        f.write(b"ORIGINAL_CONTENT")

    original_size = os.path.getsize(project_path)

    # Simulate an HDF5 lock error during file creation
    def mock_h5py_file(*args, **kwargs):
        raise OSError("Unable to lock file")

    monkeypatch.setattr(h5py, "File", mock_h5py_file)

    # Attempting to overwrite should raise the custom error
    with pytest.raises(ProjectManager.ProjectFileLockedError):
        ProjectManager.createBlankProjectFile(str(project_path))

    # Confirm the file still exists and was not truncated
    assert project_path.exists()
    assert os.path.getsize(project_path) == original_size

    with open(project_path, "rb") as f:
        assert f.read() == b"ORIGINAL_CONTENT"
