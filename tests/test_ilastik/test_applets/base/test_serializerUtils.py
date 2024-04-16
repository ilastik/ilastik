import h5py

from ilastik.applets.base.appletSerializer.serializerUtils import deleteIfPresent


def test_deleteIfPresent_present(empty_in_memory_project_file: h5py.File):
    test_group_name = "test_group_42"
    _ = empty_in_memory_project_file.create_group(test_group_name)
    assert test_group_name in empty_in_memory_project_file

    deleteIfPresent(empty_in_memory_project_file, test_group_name)

    assert test_group_name not in empty_in_memory_project_file


def test_deleteIfPresent_not_present(empty_in_memory_project_file: h5py.File):
    test_group_name = "test_group_42"
    assert test_group_name not in empty_in_memory_project_file

    deleteIfPresent(empty_in_memory_project_file, test_group_name)

    assert test_group_name not in empty_in_memory_project_file
