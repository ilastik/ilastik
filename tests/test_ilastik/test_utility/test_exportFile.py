import h5py
import numpy as np
import pytest

from ilastik.utility.exportFile import ExportFile, Mode, create_slicing


class TestCreateSlicing:
    def test_create_slicing_should_raise_if_invalid_slicing_created(self):
        feature_table = np.array(
            [0, 0, 0, 0, 0],
            dtype=[
                ("timestep", "<f4"),
                ("Bounding Box Maximum_0", "<f4"),
                ("Bounding Box Maximum_1", "<f4"),
                ("Bounding Box Minimum_0", "<f4"),
                ("Bounding Box Minimum_1", "<f4"),
            ],
        )
        slicings = create_slicing(axistags="tczyx", dimensions=(1, 64, 64, 1, 1), margin=0, feature_table=feature_table)

        with pytest.raises(ValueError):
            all_slicings = list(slicings)


@pytest.mark.parametrize("n_records", [100, 1000, 1200, 1800, 2000, 2200])
def test_write_huge_tables(tmp_path, n_records):
    """
    test that we can write tables with a large number of columns (>1000)

    xref: https://github.com/ilastik/ilastik/issues/2714
    """
    fname = tmp_path / "test.h5"

    export_file = ExportFile(file_name=fname)

    export_file.add_columns(
        "test_table", np.ones((1, n_records), dtype=[(f"{i}", "f2") for i in range(n_records)]), Mode.NumpyStructArray
    )

    export_file.write_all(mode="h5")

    with h5py.File(fname, "r") as f:
        assert "test_table" in f
        assert f["test_table"].shape == (1, n_records)


def test_table_to_large_raises(tmp_path):
    """
    test that if table really gets to large, it errors out

    xref: https://github.com/ilastik/ilastik/issues/2714
    """
    fname = tmp_path / "test.h5"
    n_records = 2500

    export_file = ExportFile(file_name=fname)

    export_file.add_columns(
        "test_table", np.ones((1, n_records), dtype=[(f"{i}", "f2") for i in range(n_records)]), Mode.NumpyStructArray
    )

    with pytest.raises(ValueError):
        export_file.write_all(mode="h5")
