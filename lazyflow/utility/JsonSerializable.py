from abc import ABC, abstractmethod
from collections.abc import Mapping
import json
import inspect

def get_constructor_params(klass):
    args_kwargs = sorted([inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD])
    for kls in klass.__mro__:
        params = inspect.signature(kls).parameters
        param_kinds = sorted(p.kind for p in params.values())
        if param_kinds != args_kwargs:
            return params.items()
    raise Exception('Unexpected signature for klass {klass}: {params}')

def hint_to_wrapper(type_hint):
    if str(type_hint).find('List[') >= 0:
        item_type = type_hint.__args__[0]
        return lambda value: [from_json_data(item_type, v) for v in value]
    raise NotImplemented(f"Don't know how to unwrap {type_hint}")

def from_json_data(cls, data):
    backup = data.copy() if isinstance(data, Mapping) else data #delete this
    if not inspect.isclass(cls):
        wrapper = hint_to_wrapper(cls)
        return wrapper(data)
    if isinstance(data, cls):
        return data
    if isinstance(data, Mapping):
        data = data.copy()
        assert '__class__' not in data or data['__class__'] == cls.__name__
        this_params = {}
        for name, parameter in get_constructor_params(cls):
            type_hint = parameter.annotation
            assert type_hint != inspect._empty, f"Missing type hint for param {name}"
            if name not in data: #might be a missing optional
                continue
            value = data.pop(name)
            if hasattr(type_hint, 'from_json_data') and not isinstance(value, type_hint):
                this_params[name] = type_hint.from_json_data(value)
            else:
                this_params[name] = from_json_data(type_hint, value)
        if len(data) > 0:
            print(f"WARNING: Unused arguments when deserializing {cls.__name__}: {data}")
        return cls(**this_params)
    return cls(data)


class JsonSerializable(ABC):
    @property
    def json_data(self):
        out_dict = {'__class__': self.__class__.__name__}
        for name, parameter in inspect.signature(self.__class__).parameters.items():
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
        #import pydevd; pydevd.settrace()
        return from_json_data(cls, data)
