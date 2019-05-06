from abc import ABC, abstractmethod
import json
import inspect
from inspect import signature

class JsonSerializable(ABC):
    def json_serialize(self):
        out_dict = {}
        for name, parameter in signature(self.__class__).parameters.items():
            value = getattr(self, name)
            if isinstance(value, JsonSerializable):
                value = value.json_serialize()
            out_dict[name] = value
        return out_dict

    def to_json(self):
        d = self.json_serialize()
        out_data = d.copy()
        for k, v in d.items():
            if isinstance(v, JsonSerializable):
                out_data[k] = v.json_serialize()
        return json.dumps(out_data)

    @classmethod
    def from_json(cls, data:dict):
        this_params = {}
        for name, parameter in signature(cls).parameters.items():
            assert parameter.annotation != inspect._empty
            if isinstance(parameter.annotation, JsonSerializable):
                this_params[name] = parameter.annotation.from_json(data[name])
            else:
                this_params[name] = data[name]
        return cls(**this_params)
