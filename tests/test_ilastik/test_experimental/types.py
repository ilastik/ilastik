import enum


@enum.unique
class TestData(enum.Enum):
    DATA_1_CHANNEL: str = "Data_1channel.png"
    DATA_3_CHANNEL: str = "Data_3channel.png"

    PIXEL_CLASS_1_CHANNEL: str = "PixelClass.ilp"
    PIXEL_CLASS_1_CHANNEL_OUT: str = "PixelClass_Output.npy"

    PIXEL_CLASS_1_CHANNEL_SKLEARN: str = "PixelClassWithSklearn.ilp"
    PIXEL_CLASS_1_CHANNEL_SKLEARN_OUT: str = "PixelClassWithSklearn_Output.npy"

    PIXEL_CLASS_3_CHANNEL: str = "PixelClass3Channel.ilp"
    PIXEL_CLASS_3_CHANNEL_OUT: str = "PixelClass3Channel_Output.npy"


class ApiTestDataLookup:
    def __init__(self, path_by_name):
        self._path_by_name = path_by_name
        self._fields = []

    def find(self, file_name: TestData) -> str:
        return self._path_by_name[file_name.value]
