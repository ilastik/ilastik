import typing

from configparser import ConfigParser

import attr

from ilastik import config
from volumina.utility import preferences

from . import types


SERVER_CONFIG_GROUP = "ServerConfig"
SERVER_CONFIG_LIST_KEY = "Servers"


class ServerConfigStorage:
    def __init__(self) -> None:
        pass

    def _parse_autostart(self, entry):
        if entry == "1":
            return True
        else:
            return False

    def _parse_server_section(self, section):
        id_ = section.replace(self.PREFIX, '')
        items = self._config.items(section)
        data = dict(items)
        data["autostart"] = self._parse_autostart(data.get("autostart", "0"))

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
        servers_data = preferences.get(SERVER_CONFIG_GROUP, SERVER_CONFIG_LIST_KEY, [])
        result = []
        for server_dict in servers_data:
            server_dict["devices"] = [types.Device(**d) for d in server_dict.get("devices", [])]
            result.append(
                types.ServerConfig(**server_dict)
            )
        return result

    def get_server(self, id_) -> typing.Optional[types.ServerConfig]:
        for srv in self.get_servers():
            if srv.id == id_:
                return srv

        return None

    def store(self, servers) -> None:
        servers_data = []

        for srv in servers:
            servers_data.append(attr.asdict(srv))

        preferences.set(SERVER_CONFIG_GROUP, SERVER_CONFIG_LIST_KEY, servers_data)


SERVER_CONFIG = ServerConfigStorage()
