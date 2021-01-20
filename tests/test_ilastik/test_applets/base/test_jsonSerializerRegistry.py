import pytest
import json

from ilastik.applets.base.jsonSerializerRegistry import (
    _DictSerialzierRegistry,
    IDictSerializer,
    SerializationError,
    DeserializationError,
    DuplicateEntryError,
    RegistryError,
)


class MyObj:
    def __init__(self, val):
        self.val = val

    def __eq__(self, other):
        return isinstance(other, MyObj) and other.val == self.val

    def __repr__(self):
        return f"MyObj(val={self.val})"


class MyParentObject:
    def __init__(self, val):
        self.nested_val = val

    def __eq__(self, other):
        return isinstance(other, MyParentObject) and other.nested_val == self.nested_val

    def __repr__(self):
        return f"MyNestedObj(val={self.nested_val})"


class TestDictSerializerRegistry:
    @pytest.fixture
    def registry(self):
        return _DictSerialzierRegistry()

    @pytest.fixture
    def serializer(self, registry):
        # TODO: Should raise on duplicates
        @registry.register_serializer(MyObj)
        class MyObjSerializer(IDictSerializer):
            def serialize(self, obj: MyObj):
                return {
                    "val": obj.val,
                }

            def deserialize(self, dct):
                return MyObj(dct["val"])

    @pytest.fixture
    def nested_serializer(self, serializer, registry):
        @registry.register_serializer(MyParentObject)
        class MyParentObjectSerializer(IDictSerializer):
            def serialize(self, obj: MyParentObject):
                return {
                    "nested_val": registry.serialize(obj.nested_val),
                }

            def deserialize(self, dct):
                return MyParentObject(registry.deserialize(MyObj, dct["nested_val"]))

    def test_serialization_should_raise_if_type_is_not_known(self, registry):
        with pytest.raises(RegistryError):
            registry.serialize(MyObj("val"))

    def test_serialization_of_known_type_should_not_raise(self, registry, serializer):
        assert registry.serialize(MyObj("val"))

    def test_serialization_format_contains_tag(self, registry, serializer):
        assert {
            "__serializer_version": 1,
            "val": "myval",
        } == registry.serialize(MyObj("myval"))

    def test_serialization_of_nested_objects(self, registry, nested_serializer):
        assert {
            "__serializer_version": 1,
            "nested_val": {"__serializer_version": 1, "val": "myval"},
        } == registry.serialize(MyParentObject(MyObj("myval")))

    def test_deserialization_should_raise_if_no_version_tag(self, registry, serializer):
        with pytest.raises(DeserializationError):
            registry.deserialize(MyObj, {"val": 1})

    def test_deserialization_should_deserialize_when_version_tag_is_present(self, registry, serializer):
        res = registry.deserialize(MyObj, {"__serializer_version": 1, "val": 42})
        assert MyObj(42) == res

    def test_deserialization_of_nested_objects_is_not_automatic(self, registry, serializer):
        res = registry.deserialize(MyObj, {"__serializer_version": 1, "val": {"__serializer_version": 1, "val": 33}})
        res2 = registry.deserialize(MyObj, {"__serializer_version": 1, "val": {"val": 33}})

        assert MyObj({"__serializer_version": 1, "val": 33}) == res
        assert MyObj({"val": 33}) == res2

    def test_deserialization_of_nested_objects(self, registry, nested_serializer):
        res = registry.deserialize(
            MyParentObject, {"__serializer_version": 1, "nested_val": {"__serializer_version": 1, "val": 12}}
        )
        assert MyParentObject(MyObj(val=12)) == res

    def test_deserialization_of_nested_dict(self, registry, nested_serializer):
        res = registry.deserialize(MyObj, {"__serializer_version": 1, "val": {"otherval": 13}})
        assert MyObj({"otherval": 13}) == res

    def test_registration_raises_on_duplicates(self, registry, serializer):
        with pytest.raises(DuplicateEntryError) as e:

            @registry.register_serializer(MyObj)
            class MyDummySerializer(IDictSerializer):
                def serialize(self, obj: MyObj):
                    ...

                def deserialize(self, dct):
                    ...

    def test_registration_raises_if_not_subclass_of_IDictSerializer(self, registry, serializer):
        with pytest.raises(TypeError) as e:

            @registry.register_serializer(MyObj)
            class MyDummySerializer:
                def serialize(self, obj: MyObj):
                    ...

                def deserialize(self, dct):
                    ...
