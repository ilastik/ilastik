import typing

from uuid import uuid4

import attr


def _validate_id(inst, attrib, value):
    if not value:
        raise ValueError("id should not be empty")

    if not isinstance(value, str):
        raise ValueError("id should be as string")


def _non_empty(inst, attrib, value):
    if not value:
        raise ValueError(f"{attrib} should not be empty")


@attr.s(auto_attribs=True, kw_only=True, frozen=True)
class Device:
    id: str = attr.ib(validator=_validate_id)
    name: str = attr.ib(validator=_non_empty)
    enabled: bool = False


@attr.s(auto_attribs=True, kw_only=True) #, frozen=True)
class ServerConfig:
    id: str = attr.ib(validator=_validate_id)
    address: str = attr.ib(validator=_non_empty)
    devices: typing.List[Device] = attr.ib()
    name: str = attr.ib(default="Unknown", validator=_non_empty)

    def evolve(self, **kwargs):
        return attr.evolve(self, **kwargs)

    @classmethod
    def default(cls, **kwargs):
        defaults = {
            "id": uuid4().hex,
            "name": "MyServer",
            "address": "127.0.0.1:5567",
            "devices": [],
            **kwargs,
        }
        return cls(**defaults)

    @devices.validator
    def _validate_devices(self, attrib, value):
        if not isinstance(value, list):
            raise ValueError("devices attribute should contain list of devices")

        for dev in value:
            if not isinstance(dev, Device):
                raise ValueError("devices entries should be instance of Device class")
