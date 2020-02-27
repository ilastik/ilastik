from configparser import ConfigParser
from io import StringIO

import pytest

from ilastik.applets.serverConfiguration.configStorage import ServerConfigStorage
from ilastik.applets.serverConfiguration import types


class TestServerParse:
    MALFORMED_MULTI_SERVER = """
[tiktorch-server::myid1]
    name = MyServer1
    type = local
    address = 127.0.0.1
    autostart = 1
    port = 5543
    devices =
        cpu0::CPU0
        gpu1::MyCoolGPU::enabled

[tiktorch-server::myid2]
    name = MyServer2
    type = local

[tiktorch-server::myid3]
    name = MyServer3
    type = remote
    address = 8.8.8.8
    port = 5543
    autostart = 0
    ssh_key = /home/user/.ssh/id_rsa
    username = testuser
    devices =
        cpu0::CPU0
        gpu1::MyCoolGPU::enabled
"""

    NO_SERVER = ""

    SINGLE_SERVER = """
[tiktorch-server::myid1]
    name = MyServer1
    type = local
    address = 127.0.0.1
    port = 5543
    devices =
        cpu0::CPU0
        gpu1::MyCoolGPU::enabled
"""

    @pytest.fixture
    def parse(self):
        def _parse(conf_str):
            conf = ConfigParser()
            conf.read_string(conf_str)
            srv_storage = ServerConfigStorage(conf, dst='')
            return srv_storage.get_servers()

        return _parse

    def test_parsing_server(self, parse):
        servers = parse(self.SINGLE_SERVER)

        assert 1 == len(servers)
        srv = servers[0]

        assert isinstance(srv, types.ServerConfig)
        assert "MyServer1" == srv.name
        assert "local" == srv.type
        assert "127.0.0.1" == srv.address
        assert "5543" == srv.port

    def test_parsing_multiserver(self, parse):
        servers = parse(self.MALFORMED_MULTI_SERVER)

        assert 2 == len(servers)
        fst, snd = servers

        assert isinstance(fst, types.ServerConfig)
        assert "MyServer1" == fst.name
        assert "local" == fst.type
        assert "127.0.0.1" == fst.address
        assert fst.autostart
        assert "5543" == fst.port

        assert isinstance(snd, types.ServerConfig)
        assert "MyServer3" == snd.name
        assert "remote" == snd.type
        assert "8.8.8.8" == snd.address
        assert "5543" == snd.port
        assert "testuser" == snd.username
        assert not snd.autostart
        assert "/home/user/.ssh/id_rsa" == snd.ssh_key

    def test_parsing_noserver(self, parse):
        servers = parse(self.NO_SERVER)
        assert not servers


class TestServerParseDevices:
    NORMAL_DEVS = """
[tiktorch-server::myid1]
    name = MyServer1
    type = local
    address = 127.0.0.1
    port = 5543
    devices =
        cpu0::CPU0
        gpu1::MyCoolGPU::enabled
"""

    MALFORMED_DEVS = """
[tiktorch-server::gpu]
    name = MalformedGPU
    type = local
    address = 127.0.0.1
    port = 5543
    devices =
        ::cpu0::CPU0:::::::
        gpu1::MyCoolGPU::1


        gpu2::NormalGPU::enabled
"""

    EMPTY_DEVS = """
[tiktorch-server::gpu2]
    name = MalformedGPU2
    type = local
    address = 127.0.0.1
    port = 5543
    devices =
"""

    NO_DEVS = """
[tiktorch-server::gpu2]
    name = MalformedGPU2
    type = local
    address = 127.0.0.1
    port = 5543
"""

    @pytest.fixture
    def parse(self):
        def _parse(conf_str):
            conf = ConfigParser()
            conf.read_string(conf_str)
            srv_storage = ServerConfigStorage(conf, dst='')
            servers = srv_storage.get_servers()
            assert len(servers) == 1
            return servers[0].devices

        return _parse

    def test_parsing_devices(self, parse):
        devices = parse(self.NORMAL_DEVS)
        assert 2 == len(devices)
        fst, snd = devices

        assert "cpu0" == fst.id
        assert "CPU0" == fst.name
        assert not fst.enabled

        assert "gpu1" == snd.id
        assert "MyCoolGPU" == snd.name
        assert snd.enabled

    def test_parsing_malformed_devices(self, parse):
        devices = parse(self.MALFORMED_DEVS)
        assert 2 == len(devices)
        fst, snd = devices

        assert "gpu1" == fst.id
        assert "MyCoolGPU" == fst.name
        assert not fst.enabled

        assert "gpu2" == snd.id
        assert "NormalGPU" == snd.name
        assert snd.enabled

    def test_parsing_devices_empty_entry(self, parse):
        devices = parse(self.EMPTY_DEVS)
        assert not devices

    def test_parsing_devices_no_entry(self, parse):
        devices = parse(self.NO_DEVS)
        assert not devices


class TestStoringServers:
    @pytest.fixture
    def store(self):
        def _store(dst, servers):
            conf = ConfigParser()
            conf.read_string(dst.read())
            srv_storage = ServerConfigStorage(conf, dst=dst)
            srv_storage.store(servers)

        return _store

    @pytest.fixture
    def servers(self):
        return [
            types.ServerConfig(id='myid1', name='Server1', type='local', address='127.0.0.1', port='3123', devices=[types.Device(id='cpu0', name='MyCpu1', enabled=True), types.Device(id='gpu1', name='GPU1', enabled=False)])
        ]

    def test_me(self, store, servers):
        out = StringIO()
        store(out, servers)
        assert 'myid1' in out.getvalue()
        assert 'cpu0::MyCpu1::enabled' in out.getvalue()


CONFIG = """
[ilastik]
debug: false
plugin_directories: ~/.ilastik/plugins,

[lazyflow]
threads: -1
total_ram_mb: 0

[tiktorch-server::myid1]
name = MyServer1
type = remote
address = 127.0.0.1
port = 5543
devices =
   cpu0::CPU0
   gpu1::GPU6::enabled
"""

def test_server_config_storing_server():
    conf = ConfigParser()
    conf.read_string(CONFIG)
    out = StringIO()
    srv_storage = ServerConfigStorage(conf, dst=out)
    srv_storage.store([types.ServerConfig.default(id="srvid1", name="MyTestServer")])

    result = out.getvalue()

    assert "srvid1" in result
    assert "MyServer1" not in result, "absent sections should be removed"
    assert "ilastik" in result, "non related sections of config should stay"
