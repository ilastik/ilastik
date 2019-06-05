from abc import ABC, abstractmethod
import json
import inspect
from inspect import signature

class JsonSerializable(ABC):
    @property
    def json_data(self):
        out_dict = {'__class__': self.__class__.__name__}
        for name, parameter in signature(self.__class__).parameters.items():
            value = getattr(self, name)
            if isinstance(value, JsonSerializable):
                value = value.json_data
            out_dict[name] = value
        return out_dict

    def to_json(self):
        d = self.json_data
        out_data = d.copy()
        for k, v in d.items():
            if isinstance(v, JsonSerializable):
                out_data[k] = v.json_data
        return json.dumps(out_data)

    @classmethod
    def from_json(cls, data:str):
        return cls.from_json_data(json.loads(data))

    @classmethod
    def from_json_data(cls, data:dict):
        data = data.copy()
        assert '__class__' not in data or data['__class__'] == cls.__name__
        this_params = {}
        for name, parameter in signature(cls).parameters.items():
            assert parameter.annotation != inspect._empty
            if name not in data: #might be a missing optional
                continue
            if issubclass(parameter.annotation, JsonSerializable):
                this_params[name] = parameter.annotation.from_json(data.pop(name))
            else:
                this_params[name] = data.pop(name)
        if len(data) > 0:
            print(f"WARNING: Unused arguments when deserializing {cls.__name__}: {data}")
        return cls(**this_params)
