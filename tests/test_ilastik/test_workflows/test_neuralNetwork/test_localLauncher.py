import grpc
import pytest

from ilastik.workflows.neuralNetwork._localLauncher import LocalServerLauncher

from tiktorch.proto.inference_pb2 import Empty
from tiktorch.proto.inference_pb2_grpc import FlightControlStub


def test_local_launcher(tiktorch_executable_path):
    launcher = LocalServerLauncher(tiktorch_executable_path)
    addr, port = launcher.start()

    chan = grpc.insecure_channel(f"{addr}:{port}")
    client = FlightControlStub(chan)

    result = client.Ping(Empty())
    assert isinstance(result, Empty)
    client.Shutdown(Empty())

    launcher.stop()

    with pytest.raises(grpc.RpcError) as error:
        client.Ping(Empty())

    assert error.value.code() is grpc.StatusCode.UNAVAILABLE
