from collections import defaultdict
from io import StringIO

import pytest

from ilastik.applets.serverConfiguration.configStorage import (
    ServerConfigStorage,
    SERVER_CONFIG_GROUP,
    SERVER_CONFIG_LIST_KEY,
)
from ilastik.applets.serverConfiguration import types


class PreferencesStub:
    def __init__(self):
        self.config = defaultdict(dict)

    def set_server_configs(self, data):
        self.set(SERVER_CONFIG_GROUP, SERVER_CONFIG_LIST_KEY, data)

    def get_server_configs(self):
        print(self.config)
        return self.get(SERVER_CONFIG_GROUP, SERVER_CONFIG_LIST_KEY)

    def set(self, group, key, value):
        self.config[group][key] = value

    def get(self, group, key, default=None):
        return self.config[group].get(key, default)


@pytest.fixture
def prefs_stub():
    return PreferencesStub()


@pytest.fixture
def config_storage(prefs_stub):
    return ServerConfigStorage(prefs_stub)


class TestServerParse:
    def test_parsing_server(self, prefs_stub, config_storage):
        prefs_stub.set_server_configs(
            [
                {
                    "id": "myid1",
                    "name": "MyServer1",
                    "address": "127.0.0.1:4412",
                    "devices": [
                        {"id": "cpu0", "name": "CPU0", "enabled": False},
                        {"id": "gpu1", "name": "MyCoolGPU", "enabled": True},
                    ],
                }
            ]
        )
        servers = config_storage.get_servers()
        assert 1 == len(servers)
        srv = servers[0]
        assert isinstance(srv, types.ServerConfig)
        assert "MyServer1" == srv.name
        assert "127.0.0.1:4412" == srv.address

        assert 2 == len(srv.devices)
        fst, snd = srv.devices

        assert "cpu0" == fst.id
        assert "CPU0" == fst.name
        assert not fst.enabled

        assert "gpu1" == snd.id
        assert "MyCoolGPU" == snd.name
        assert snd.enabled

    def test_parsing_extra_keys(self, prefs_stub, config_storage):
        prefs_stub.set_server_configs(
            [
                {
                    "id": "myid1",
                    "myadditional_key": "some",
                    "name": "MyServer1",
                    "address": "127.0.0.1:4412",
                    "devices": [
                        {"id": "cpu0", "attr2": 12, "name": "CPU0", "enabled": False},
                        {"id": "gpu1", "name": "MyCoolGPU", "enabled": True},
                    ],
                }
            ]
        )
        servers = config_storage.get_servers()
        assert 1 == len(servers)
        srv = servers[0]
        assert isinstance(srv, types.ServerConfig)
        assert "MyServer1" == srv.name
        assert "127.0.0.1:4412" == srv.address

    def test_parsing_multiserver(self, prefs_stub, config_storage):
        prefs_stub.set_server_configs(
            [
                {
                    "id": "myid1",
                    "name": "MyServer1",
                    "address": "127.0.0.1:4412",
                    "devices": [
                        {"id": "cpu0", "name": "CPU0", "enabled": False},
                        {"id": "gpu1", "name": "MyCoolGPU", "enabled": True},
                    ],
                },
                {
                    "id": "myid3",
                    "name": "MyServer3",
                    "address": "8.8.8.8:5543",
                    "devices": [
                        {"id": "cpu0", "name": "CPU0", "enabled": False},
                        {"id": "gpu1", "name": "MyCoolGPU", "enabled": True},
                    ],
                },
            ]
        )
        servers = config_storage.get_servers()

        assert 2 == len(servers)
        fst, snd = servers

        assert isinstance(fst, types.ServerConfig)
        assert "MyServer1" == fst.name
        assert "127.0.0.1:4412" == fst.address

        assert isinstance(snd, types.ServerConfig)
        assert "MyServer3" == snd.name
        assert "8.8.8.8:5543" == snd.address

    def test_parsing_no_entry(self, prefs_stub, config_storage):
        servers = config_storage.get_servers()
        assert not servers

    def test_parsing_empty_list(self, prefs_stub, config_storage):
        prefs_stub.set_server_configs([])
        servers = config_storage.get_servers()
        assert not servers


class TestStoringServers:
    @pytest.fixture
    def store(self):
        def _store(dst, prefs_stub, config_storage):
            conf = ConfigParser()
            conf.read_string(dst.read())
            srv_storage = ServerConfigStorage(conf, dst=dst)
            srv_storage.store(servers)

        return _store

    @pytest.fixture
    def servers(self):
        return [
            types.ServerConfig(
                id="myid1",
                name="Server1",
                address="127.0.0.1:3123",
                devices=[
                    types.Device(id="cpu0", name="MyCpu1", enabled=True),
                    types.Device(id="gpu1", name="GPU1", enabled=False),
                ],
            )
        ]

    def test_storing(self, servers, prefs_stub, config_storage):
        config_storage.store(servers)
        configs = prefs_stub.get_server_configs()

        assert isinstance(configs, list)
        assert len(configs) == 1
        server = configs[0]

        assert server["id"] == "myid1"
        assert server["name"] == "Server1"
        assert server["address"] == "127.0.0.1:3123"

        devices = server.get("devices")
        assert isinstance(devices, list)
        assert len(devices) == 2

        dev1, dev2 = devices
        assert dev1["id"] == "cpu0"
        assert dev1["name"] == "MyCpu1"
        assert dev1["enabled"]

        assert dev2["id"] == "gpu1"
        assert dev2["name"] == "GPU1"
        assert not dev2["enabled"]
