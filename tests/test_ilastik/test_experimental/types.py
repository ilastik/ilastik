import enum


@enum.unique
class TestData(enum.Enum):
    DATA_1_CHANNEL: str = "Data_1channel.png"
    DATA_3_CHANNEL: str = "Data_3channel.png"
    DATA_1_CHANNEL_3D: str = "Data_3D.npy"

    PIXEL_CLASS_1_CHANNEL: str = "PixelClass.ilp"
    PIXEL_CLASS_1_CHANNEL_OUT: str = "PixelClass_Output.npy"

    PIXEL_CLASS_1_CHANNEL_SKLEARN: str = "PixelClassWithSklearn.ilp"
    PIXEL_CLASS_1_CHANNEL_SKLEARN_OUT: str = "PixelClassWithSklearn_Output.npy"

    PIXEL_CLASS_3_CHANNEL: str = "PixelClass3Channel.ilp"
    PIXEL_CLASS_3_CHANNEL_OUT: str = "PixelClass3Channel_Output.npy"

    PIXEL_CLASS_3D: str = "PixelClass3D.ilp"
    PIXEL_CLASS_3D_OUT: str = "PixelClass3D_Output.npy"

    PIXEL_CLASS_NO_CLASSIFIER: str = "PixelClassNoClassifier.ilp"
    PIXEL_CLASS_NO_DATA: str = "PixelClassNoData.ilp"

    PIXEL_CLASS_3D_2D_3D_FEATURE_MIX: str = "PixelClass3D_2D_3D_feature_mix.ilp"
    PIXEL_CLASS_3D_2D_3D_FEATURE_MIX_OUT: str = "PixelClass3D_2D_3D_feature_mix_Output.npy"


class ApiTestDataLookup:
    def __init__(self, path_by_name):
        self._path_by_name = path_by_name
        self._fields = []

    def find(self, file_name: TestData) -> str:
        return self._path_by_name[file_name.value]
