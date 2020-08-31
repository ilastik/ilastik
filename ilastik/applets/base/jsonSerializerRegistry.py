"""
This module provides an interface to define serializers
without modifying a serializable class (e.g. adding toJson, todict methods).
This enables defining serialization protocol for third-party library classes and simplifies versioning.

Usage example:
>>> class Foo:
...     def __init__(self, val: int):
...         self.val = val
...
...     def __repr__(self):
...         return f"Foo({self.val})"

>>> @register_serializer(Foo)
... class MyObjSerializer(IDictSerializer):
...     def serialize(self, obj):
...         return {
...             "val": obj.val,
...         }
...
...     def deserialize(self, dct):
...         return Foo(dct["val"])

>>> serialize(Foo(42))
{'val': 42, '__serializer_version': 1}

>>> deserialize(Foo, {"val": 42, "__serializer_version": 1})
Foo(42)

"""
import abc

from typing import TypeVar, Dict, Any, Generic, Type, Callable, Union, Tuple


T = TypeVar("T")


class IDictSerializer(abc.ABC, Generic[T]):
    @abc.abstractmethod
    def serialize(self, obj: T) -> Dict[str, Any]:
        ...

    @abc.abstractmethod
    def deserialize(self, dct: Dict[str, Any]) -> T:
        ...


class RegistryError(Exception):
    pass


class DuplicateEntryError(RegistryError):
    pass


class SerializationError(RegistryError):
    pass


class DeserializationError(RegistryError):
    pass


class _DictSerialzierRegistry:
    _VERSION_TAG = "__serializer_version"

    def __init__(self) -> None:
        self._serializer_by_type: Dict[Type, IDictSerializer] = {}

    def register_serializer(self, type_: Type) -> Callable[[Type[IDictSerializer]], Type[IDictSerializer]]:
        def _register_serializer(serializer_cls: Type[IDictSerializer]) -> Type[IDictSerializer]:
            if not issubclass(serializer_cls, IDictSerializer):
                raise TypeError("Serializer class should inherit from IDictSerializer")

            entry = self._serializer_by_type.get(type_)
            if entry is not None:
                raise DuplicateEntryError(f"Entry for type {type_} already exists {entry}")

            self._serializer_by_type[type_] = serializer_cls()
            return serializer_cls

        return _register_serializer

    registerSerializer = register_serializer

    def serialize(self, obj: Any) -> Dict[str, Any]:
        serializer_cls = self._serializer_by_type.get(type(obj), None)

        if not serializer_cls:
            raise RegistryError(f"No serializer for class {type(obj)} found")

        serialized_data = serializer_cls.serialize(obj)
        serialized_data[self._VERSION_TAG] = 1  # TODO: Add proper versioning

        return serialized_data

    def deserialize(self, type_: Type[T], dct: Dict[str, Any]) -> T:
        serializer_cls = self._serializer_by_type.get(type_, None)

        if not serializer_cls:
            raise RegistryError(f"No deserializer for class {type} found")

        serializer_version = dct.pop(self._VERSION_TAG, None)

        if serializer_version is None:
            raise DeserializationError("Malformed dict. No version tag")

        return serializer_cls.deserialize(dct)

    def is_type_known(self, type_: Type) -> bool:
        return type_ in self._serializer_by_type


_SERIALIZER_REGISTRY = _DictSerialzierRegistry()


def register_serializer(type_: Type) -> Callable[[Type[IDictSerializer]], Type[IDictSerializer]]:
    return _SERIALIZER_REGISTRY.register_serializer(type_)


registerSerializer = register_serializer


def deserialize(expected_type: Type[T], dct: Dict[str, Any]) -> T:
    return _SERIALIZER_REGISTRY.deserialize(expected_type, dct)


def serialize(obj: Any) -> Dict[str, Any]:
    return _SERIALIZER_REGISTRY.serialize(obj)


def is_type_known(type_: Type) -> bool:
    return _SERIALIZER_REGISTRY.is_type_known(type_)
