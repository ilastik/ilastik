class State:
    """
    Stores model state
    As opaque serialized tensors
    """

    model: bytes
    optimizer: bytes

    def __init__(self, *, model: bytes, optimizer: bytes) -> None:
        self.model = model
        self.optimizer = optimizer


class Model:
    code: bytes
    config: dict

    def __init__(self, *, code: bytes, config: dict) -> None:
        self.code = code
        self.config = config

    def __bool__(self) -> bool:
        return bool(self.code)


Model.Empty = Model(b"", {})
