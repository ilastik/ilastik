import pytest
import numpy as np

from ilastik.utility.exportFile import create_slicing


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
