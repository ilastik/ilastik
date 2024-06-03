import dataclasses
import enum
from typing import Dict, Union


@enum.unique
class TestData(str, enum.Enum):
    __test__ = False
    DATA_1_CHANNEL: str = ("Data_1channel.png", "yx", "yxc")
    DATA_3_CHANNEL: str = ("Data_3channel.png", "yxc", "yxc")
    DATA_1_CHANNEL_3D: str = ("Data_3D.npy", "zyxc", "zyxc")

    def __new__(cls, value, axes, headless_axes):
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj.axes = axes
        obj.data_axes = headless_axes
        return obj


@enum.unique
class TestProjects(enum.Enum):
    __test__ = False
    PIXEL_CLASS_1_CHANNEL_XYC: str = "PixelClass.ilp"
    PIXEL_CLASS_1_CHANNEL_XY: str = "2464_PixelClassification_xy_input.ilp"
    PIXEL_CLASS_3_CHANNEL: str = "PixelClass3Channel.ilp"
    PIXEL_CLASS_3D: str = "PixelClass3D.ilp"
    PIXEL_CLASS_NO_CLASSIFIER: str = "PixelClassNoClassifier.ilp"
    PIXEL_CLASS_NO_DATA: str = "PixelClassNoData.ilp"
    PIXEL_CLASS_3D_2D_3D_FEATURE_MIX: str = "PixelClass3D_2D_3D_feature_mix.ilp"

    AUTOCONTEXT_2D: str = "Autocontext_2D.ilp"
    AUTOCONTEXT_3D: str = "Autocontext_3D.ilp"


@enum.unique
class ResultData(str, enum.Enum):
    __test__ = False
    DATA_1_CHANNEL_PC1XYC: str = ("res-Data_1channel_pc1xyc.npy", "yxc")
    DATA_1_CHANNEL_PC1XY: str = ("res-Data_1channel_pc1xy.npy", "yxc")
    DATA_3_CHANNEL_PC3C: str = ("res-Data_3channel_pc3c.npy", "yxc")
    DATA_1_CHANNEL_3D_pc3d: str = ("res-Data_3D_pc3d.npy", "zyxc")
    DATA_1_CHANNEL_3D_pc3d2dfm: str = ("res-Data_3D_pc3d2dfm.npy", "zyxc")

    DATA_1_CHANNEL_ACS1: str = ("res-Data_1channel_ac2ds1.npy", "yxc")
    DATA_1_CHANNEL_ACS2: str = ("res-Data_1channel_ac2ds2.npy", "yxc")
    DATA_1_CHANNEL_3D_ACS1: str = ("res-Data_3D_ac2ds1.npy", "zyxc")
    DATA_1_CHANNEL_3D_ACS2: str = ("res-Data_3D_ac2ds2.npy", "zyxc")

    def __new__(cls, value, axes):
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj.axes = axes
        return obj


TestResultsLookup = {
    TestProjects.PIXEL_CLASS_1_CHANNEL_XYC: {
        TestData.DATA_1_CHANNEL: {"Probabilities": ResultData.DATA_1_CHANNEL_PC1XYC}
    },
    TestProjects.PIXEL_CLASS_1_CHANNEL_XY: {
        TestData.DATA_1_CHANNEL: {"Probabilities": ResultData.DATA_1_CHANNEL_PC1XY}
    },
    TestProjects.PIXEL_CLASS_3_CHANNEL: {TestData.DATA_3_CHANNEL: {"Probabilities": ResultData.DATA_3_CHANNEL_PC3C}},
    TestProjects.PIXEL_CLASS_3D: {TestData.DATA_1_CHANNEL_3D: {"Probabilities": ResultData.DATA_1_CHANNEL_3D_pc3d}},
    TestProjects.PIXEL_CLASS_3D_2D_3D_FEATURE_MIX: {
        TestData.DATA_1_CHANNEL_3D: {"Probabilities": ResultData.DATA_1_CHANNEL_3D_pc3d2dfm}
    },
    TestProjects.AUTOCONTEXT_2D: {
        TestData.DATA_1_CHANNEL: {
            "Probabilities Stage 1": ResultData.DATA_1_CHANNEL_ACS1,
            "Probabilities Stage 2": ResultData.DATA_1_CHANNEL_ACS2,
        }
    },
    TestProjects.AUTOCONTEXT_3D: {
        TestData.DATA_1_CHANNEL_3D: {
            "Probabilities Stage 1": ResultData.DATA_1_CHANNEL_3D_ACS1,
            "Probabilities Stage 2": ResultData.DATA_1_CHANNEL_3D_ACS2,
        }
    },
}


@dataclasses.dataclass
class Dataset:
    path: str
    #: Axes to use for api prediction
    axes: str
    #: Axes to use for headless run
    data_axes: str

    def __str__(self):
        return self.path


class ApiTestDataLookup:
    def __init__(self, path_by_name: Dict[Union[TestData, TestProjects, ResultData], str]):
        self._path_by_name = path_by_name
        self._fields = []

    def find_project(self, file_name: TestProjects) -> str:
        return self._path_by_name[file_name.value]

    def find_dataset(self, file_name: TestData) -> Dataset:
        path = self._path_by_name[file_name.value]
        return Dataset(path, file_name.axes, file_name.data_axes)

    def find_test_result(
        self, project_file_name: TestProjects, input_file_name: TestData, export_source: str
    ) -> Dataset:
        result_filename = TestResultsLookup.get(project_file_name, {}).get(input_file_name, {}).get(export_source)
        path = self._path_by_name[result_filename.value]
        return Dataset(path, result_filename.axes, result_filename.axes)
