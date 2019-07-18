import typing

from configparser import ConfigParser

import attr

from ilastik import config

from . import types


class ServerConfigStorage:
    PREFIX = "tiktorch-server::"
    DEVICE_PREFIX = "device::"

    def __init__(self, config: ConfigParser, dst: str) -> None:
        self._config = config
        self._dst = dst

    def _parse_server_section(self, section):
        id_ = section.replace(self.PREFIX, '')
        items = self._config.items(section)
        data = dict(items)

        try:
            data["devices"] = self._parse_devices(data["devices"])
        except Exception:
            data["devices"] = []

        return types.ServerConfig(**{
            "id": id_,
            **data,
        })

    def _parse_device(self, dev_str):
        id_, name, *rest = dev_str.split("::")

        enabled = False
        if len(rest) == 1 and rest[0] == "enabled":
            enabled = True

        return types.Device(id=id_, name=name, enabled=enabled)

    def _parse_devices(self, devices_str):
        devs = devices_str.split('\n')
        res = []
        for dev in devs:
            try:
                res.append(self._parse_device(dev))
            except Exception:
                pass

        return res

    def get_servers(self):
        res = []

        for section in self._config.sections():
            if section.startswith(self.PREFIX):
                try:
                    srv = self._parse_server_section(section)
                except Exception:
                    continue

                res.append(srv)

        return res

    def get_server(self, id_) -> typing.Optional[types.ServerConfig]:
        for srv in self.get_servers():
            if srv.id == id_:
                return srv

        return None

    def _server_as_dict(self, srv):
        return attr.asdict(srv)

    def _serialize_device(self, device):
        device_str = f"{device['id']}::{device['name']}"
        if device["enabled"]:
            device_str += "::enabled"
        return device_str

    def _serialize_devices(self, devices):
        result = []

        for dev in devices:
            try:
                result.append(self._serialize_device(dev))
            except Exception:
                pass

        if len(result) > 1:
            result.insert(0, '')

        return '\n'.join(result)

    def _write_server_entry(self, srv):
        section_id = f"{self.PREFIX}{srv.id}"

        self._config.add_section(section_id)
        for key, value in self._server_as_dict(srv).items():
            if key == "id":
                continue

            if key == "devices":
                value = self._serialize_devices(value)

            self._config.set(section_id, key, value)

    def store(self, servers) -> None:
        current_servers = self.get_servers()

        for srv in current_servers:
            self._config.remove_section(f"{self.PREFIX}{srv.id}")

        for srv in servers:
            self._write_server_entry(srv)

        if isinstance(self._dst, str):
            with open(self._dst, 'w+') as out:
                self._config.write(out)
        else:
            self._config.write(self._dst)


SERVER_CONFIG = ServerConfigStorage(config.cfg, config.CONFIG_PATH)
