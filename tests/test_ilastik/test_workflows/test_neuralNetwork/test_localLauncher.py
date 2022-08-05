import grpc
import platform
import pytest

from ilastik.workflows.neuralNetwork._localLauncher import LocalServerLauncher

from tiktorch.proto.inference_pb2 import Empty
from tiktorch.proto.inference_pb2_grpc import FlightControlStub


def test_local_launcher(tiktorch_executable_path):
    launcher = LocalServerLauncher(tiktorch_executable_path)
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
