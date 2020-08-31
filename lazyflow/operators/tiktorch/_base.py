from typing import List


class IConnection:
    def get_devices(self):
        raise NotImplementedError

    def create_model_session(self, model_str: bytes, devices: List[str]):
        raise NotImplementedError


class IConnectionFactory:
    def ensure_connection(self, config) -> IConnection:
        raise NotImplementedError
