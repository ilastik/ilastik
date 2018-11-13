import enum

class SlotNameEnum(enum.IntEnum):
    @classmethod
    def asNameList(cls):
        return [item.name.replace('_', ' ').title() for item in cls]

