from dataclasses import dataclass
from os import PathLike


@dataclass(frozen=True)
class InfoMessageData:
    title: str
    filename: PathLike
    message_id: str
