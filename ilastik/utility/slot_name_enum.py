import enum
from typing import List, Tuple
from itertools import chain

class SlotNameEnum(enum.IntEnum):
    """A map from slot names to their indices within a multislot

    Do note that the ENUM_NAMEs that you pick matter, as they determine
    the human readable version that you get from instances of this enum:

    e.g a value defined like so:
        MY_DATA_SLOT = 123
    will have its slotName rendered as
        'My Data Slot'
    """

    @property
    def slotName(self) -> str:
        """A 'Human Readable Slot Name' str based on its ENUM_SLOT_NAME"""
        return self.name.replace('_', ' ').title()

    @classmethod
    def asNameList(cls) -> List[str]:
        return [item.slotName for item in cls]

    @classmethod
    def getFirst(cls) -> int:
        return list(cls)[0]

    @classmethod
    def getLast(cls) -> int:
        return list(cls)[-1]

    @classmethod
    def getNext(cls) -> int:
        return cls.getLast() + 1

    @classmethod
    def getPairs(cls) -> List[Tuple[str, int]]:
        return [(item.name, item.value) for item in cls]

    @classmethod
    def extendedWithEnum(cls, extra_enum: 'SlotNameEnum', unique: bool=False) -> 'SlotNameEnum':
        """Crates a new SlotNameEnum combining the keys from cls and extra_enum"""

        wrapper = enum.unique if unique else lambda x: x
        return wrapper(SlotNameEnum(extra_enum.__name__,
                                    chain(cls.getPairs(),
                                          extra_enum.getPairs())))

