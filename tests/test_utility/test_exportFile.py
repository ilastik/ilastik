import numpy as np
from ilastik.utility.exportFile import create_slicing


class TestCreateSlicing:
    def test_produce_valid_slicing_with_0_margin(self):
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

        all_slicings = list(slicings)
        assert 5 == len(all_slicings)

        assert [np.s_[0:1], np.s_[:], np.s_[0:1], np.s_[0:1], np.s_[0:1]] == all_slicings[0][0]
