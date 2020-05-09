import io
from typing import Callable


class RemoteFile(io.BytesIO):
    def __init__(self, close_callback: Callable[["RemoteFile"], None], mode: str, data: bytes):
        self.mode = mode
        self.close_callback = close_callback
        super().__init__(data)

    def write(self, data: bytes):
        if self.mode == "r":
            raise RuntimeError("This is a readonly file!")
        super().write(data)

    def close(self):
        self.close_callback(self)
        super().close()
