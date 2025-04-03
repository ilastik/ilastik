import grpc
import os
import platform
import pytest
from unittest import mock

from ilastik.workflows.neuralNetwork._localLauncher import LocalServerLauncher

from tiktorch.proto.utils_pb2 import Empty
from tiktorch.proto.inference_pb2_grpc import FlightControlStub


@pytest.fixture
def macos_arm64_mock():
    with mock.patch("platform.system", new=lambda: "darwin"), mock.patch("platform.machine", new=lambda: "arm64"):
        yield


@pytest.fixture
def launcher(tiktorch_executable_path):
    return LocalServerLauncher(tiktorch_executable_path)


def test_local_launcher(launcher):
    conn_str = launcher.start()

    chan = grpc.insecure_channel(conn_str)
    client = FlightControlStub(chan)

    result = client.Ping(Empty())
    assert isinstance(result, Empty)

    launcher.stop()

    with pytest.raises(grpc.RpcError) as error:
        client.Ping(Empty())

    # :( osx/linux - win inconsistency https://github.com/grpc/grpc/issues/24206
    if platform.system() == "Windows":
        assert error.value.code() in [grpc.StatusCode.UNKNOWN, grpc.StatusCode.UNAVAILABLE]
    else:
        assert error.value.code() is grpc.StatusCode.UNAVAILABLE


def test_local_launcher_macos_silicon_env_override(macos_arm64_mock, launcher):
    with mock.patch("os.environ", new={}):
        assert launcher._proc_env.get("PYTORCH_ENABLE_MPS_FALLBACK") == "1"


def test_local_launcher_macos_silicon_no_env_override_if_default(macos_arm64_mock, launcher):
    """should not modify env on silicon mac variable if set by user"""
    with mock.patch("os.environ", new={"PYTORCH_ENABLE_MPS_FALLBACK": "some_test_value"}):
        assert launcher._proc_env.get("PYTORCH_ENABLE_MPS_FALLBACK") == "some_test_value"


def test_local_launcher_macos_silicon_no_env_override_if_not_arm(launcher):
    """should not modify env variable if on mac intel machines"""
    with (
        mock.patch("platform.system", new=lambda: "darwin"),
        mock.patch("platform.machine", new=lambda: "x86_64"),
        mock.patch("os.environ", new={}),
    ):
        assert "PYTORCH_ENABLE_MPS_FALLBACK" not in launcher._proc_env


@pytest.mark.parametrize("system", ["Linux", "Windows"])
def test_local_launcher_passthrough_env(system, launcher):
    current_env = os.environ.copy()
    with mock.patch("platform.system", new=lambda: system):
        assert launcher._proc_env == current_env
