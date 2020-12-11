import typing

from configparser import ConfigParser

import attr

from ilastik import config
from volumina.utility import preferences

from . import types


SERVER_CONFIG_GROUP = "ServerConfig"
SERVER_CONFIG_LIST_KEY = "Servers"


def _from_dict(type_, data):
    if not isinstance(data, dict):
        raise ValueError("Expected dict")

    field_names = set(attr.name for attr in attr.fields(type_))
    return type_(**{fn: data.get(fn) for fn in field_names})


class ServerConfigStorage:
    def __init__(self, preferences=preferences) -> None:
        self.__preferences = preferences

    def get_servers(self):
        servers_data = self.__preferences.get(SERVER_CONFIG_GROUP, SERVER_CONFIG_LIST_KEY, [])
        result = []
        for server_dict in servers_data:
            server_dict["devices"] = [_from_dict(types.Device, d) for d in server_dict.get("devices", [])]
            result.append(_from_dict(types.ServerConfig, server_dict))
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

        self.__preferences.set(SERVER_CONFIG_GROUP, SERVER_CONFIG_LIST_KEY, servers_data)


SERVER_CONFIG = ServerConfigStorage()
