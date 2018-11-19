import enum
from itertools import chain

class SlotNameEnum(enum.IntEnum):
    @property
    def socketName(self):
        return self.name.replace('_', ' ').title()

    @classmethod
    def asNameList(cls):
        return [item.socketName for item in cls]

    @classmethod
    def getFirst(cls):
        return list(cls)[0]

    @classmethod
    def getLast(cls):
        return list(cls)[-1]

    @classmethod
    def getNext(cls):
        return cls.getLast() + 1

    @classmethod
    def getPairs(cls):
        return [(item.name, item.value) for item in cls]

    @classmethod
    def getKeys(cls):
        return [item.name for item in cls]

    @classmethod
    def extendedWithKeys(cls, new_keys, new_enum_name=None):
        new_enum_name = new_enum_name or cls.__name__ + "Extended"
        new_values_start = cls.getNext()
        new_values_end = new_values_start + len(new_keys)

        new_pairs = list(zip(new_keys, range(new_values_start, new_values_end)))
        return enum.unique(SlotNameEnum(new_enum_name,
                                        chain(cls.getPairs(), new_pairs)))

    @classmethod
    def extendedWithEnum(cls, extra_enum, unique=False):
        wrapper = enum.unique if unique else lambda x: x
        return wrapper(SlotNameEnum(extra_enum.__name__,
                                    chain(cls.getPairs(),
                                          extra_enum.getPairs())))

