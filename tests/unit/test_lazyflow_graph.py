from nose.tools import assert_equal
from nose import SkipTest

class TestOperators:
    def test_register(self):
        # operators = Operators()
        # assert_equal(expected, operators.register(opcls))
        raise SkipTest # TODO: implement your test here

    def test_registerOperatorSubclasses(self):
        # operators = Operators()
        # assert_equal(expected, operators.registerOperatorSubclasses())
        raise SkipTest # TODO: implement your test here

class TestCopyOnWriteView:
    def test___getitem__(self):
        # copy_on_write_view = CopyOnWriteView(shape, dtype)
        # assert_equal(expected, copy_on_write_view.__getitem__(key))
        raise SkipTest # TODO: implement your test here

    def test___init__(self):
        # copy_on_write_view = CopyOnWriteView(shape, dtype)
        raise SkipTest # TODO: implement your test here

    def test___setitem__(self):
        # copy_on_write_view = CopyOnWriteView(shape, dtype)
        # assert_equal(expected, copy_on_write_view.__setitem__(key, value))
        raise SkipTest # TODO: implement your test here

class TestPatchForeignCurrentThread:
    def test_patch_foreign_current_thread(self):
        # assert_equal(expected, patchForeignCurrentThread())
        raise SkipTest # TODO: implement your test here

class TestGetItemRequestObject:
    def test___call__(self):
        # get_item_request_object = GetItemRequestObject(slot, roi, destination, priority)
        # assert_equal(expected, get_item_request_object.__call__())
        raise SkipTest # TODO: implement your test here

    def test___init__(self):
        # get_item_request_object = GetItemRequestObject(slot, roi, destination, priority)
        raise SkipTest # TODO: implement your test here

    def test_adjustPriority(self):
        # get_item_request_object = GetItemRequestObject(slot, roi, destination, priority)
        # assert_equal(expected, get_item_request_object.adjustPriority(delta))
        raise SkipTest # TODO: implement your test here

    def test_allocate(self):
        # get_item_request_object = GetItemRequestObject(slot, roi, destination, priority)
        # assert_equal(expected, get_item_request_object.allocate(priority))
        raise SkipTest # TODO: implement your test here

    def test_cancel(self):
        # get_item_request_object = GetItemRequestObject(slot, roi, destination, priority)
        # assert_equal(expected, get_item_request_object.cancel(level))
        raise SkipTest # TODO: implement your test here

    def test_getResult(self):
        # get_item_request_object = GetItemRequestObject(slot, roi, destination, priority)
        # assert_equal(expected, get_item_request_object.getResult())
        raise SkipTest # TODO: implement your test here

    def test_notify(self):
        # get_item_request_object = GetItemRequestObject(slot, roi, destination, priority)
        # assert_equal(expected, get_item_request_object.notify(closure, **kwargs))
        raise SkipTest # TODO: implement your test here

    def test_onCancel(self):
        # get_item_request_object = GetItemRequestObject(slot, roi, destination, priority)
        # assert_equal(expected, get_item_request_object.onCancel(closure, **kwargs))
        raise SkipTest # TODO: implement your test here

    def test_wait(self):
        # get_item_request_object = GetItemRequestObject(slot, roi, destination, priority)
        # assert_equal(expected, get_item_request_object.wait(timeout))
        raise SkipTest # TODO: implement your test here

    def test_writeInto(self):
        # get_item_request_object = GetItemRequestObject(slot, roi, destination, priority)
        # assert_equal(expected, get_item_request_object.writeInto(destination, priority))
        raise SkipTest # TODO: implement your test here

class TestSlot:
    def test___call__(self):
        # slot = Slot(stype, rtype)
        # assert_equal(expected, slot.__call__(*args, **kwargs))
        raise SkipTest # TODO: implement your test here

    def test___getitem__(self):
        # slot = Slot(stype, rtype)
        # assert_equal(expected, slot.__getitem__(key))
        raise SkipTest # TODO: implement your test here

    def test___init__(self):
        # slot = Slot(stype, rtype)
        raise SkipTest # TODO: implement your test here

    def test_get(self):
        # slot = Slot(stype, rtype)
        # assert_equal(expected, slot.get(roi))
        raise SkipTest # TODO: implement your test here

    def test_graph(self):
        # slot = Slot(stype, rtype)
        # assert_equal(expected, slot.graph())
        raise SkipTest # TODO: implement your test here

class TestMetaDict:
    def test___getattr__(self):
        # meta_dict = MetaDict(other)
        # assert_equal(expected, meta_dict.__getattr__(name))
        raise SkipTest # TODO: implement your test here

    def test___init__(self):
        # meta_dict = MetaDict(other)
        raise SkipTest # TODO: implement your test here

    def test___setattr__(self):
        # meta_dict = MetaDict(other)
        # assert_equal(expected, meta_dict.__setattr__(name, value))
        raise SkipTest # TODO: implement your test here

    def test_copy(self):
        # meta_dict = MetaDict(other)
        # assert_equal(expected, meta_dict.copy())
        raise SkipTest # TODO: implement your test here

class TestInputSlot:
    def test___init__(self):
        # input_slot = InputSlot(name, operator, stype, rtype, value, optional)
        raise SkipTest # TODO: implement your test here

    def test___setitem__(self):
        # input_slot = InputSlot(name, operator, stype, rtype, value, optional)
        # assert_equal(expected, input_slot.__setitem__(key, value))
        raise SkipTest # TODO: implement your test here

    def test_axistags(self):
        # input_slot = InputSlot(name, operator, stype, rtype, value, optional)
        # assert_equal(expected, input_slot.axistags())
        raise SkipTest # TODO: implement your test here

    def test_connect(self):
        # input_slot = InputSlot(name, operator, stype, rtype, value, optional)
        # assert_equal(expected, input_slot.connect(partner, notify))
        raise SkipTest # TODO: implement your test here

    def test_connectOk(self):
        # input_slot = InputSlot(name, operator, stype, rtype, value, optional)
        # assert_equal(expected, input_slot.connectOk(partner))
        raise SkipTest # TODO: implement your test here

    def test_connected(self):
        # input_slot = InputSlot(name, operator, stype, rtype, value, optional)
        # assert_equal(expected, input_slot.connected())
        raise SkipTest # TODO: implement your test here

    def test_disconnect(self):
        # input_slot = InputSlot(name, operator, stype, rtype, value, optional)
        # assert_equal(expected, input_slot.disconnect())
        raise SkipTest # TODO: implement your test here

    def test_dtype(self):
        # input_slot = InputSlot(name, operator, stype, rtype, value, optional)
        # assert_equal(expected, input_slot.dtype())
        raise SkipTest # TODO: implement your test here

    def test_dumpToH5G(self):
        # input_slot = InputSlot(name, operator, stype, rtype, value, optional)
        # assert_equal(expected, input_slot.dumpToH5G(h5g, patchBoard))
        raise SkipTest # TODO: implement your test here

    def test_getInstance(self):
        # input_slot = InputSlot(name, operator, stype, rtype, value, optional)
        # assert_equal(expected, input_slot.getInstance(operator))
        raise SkipTest # TODO: implement your test here

    def test_reconstructFromH5G(self):
        # input_slot = InputSlot(name, operator, stype, rtype, value, optional)
        # assert_equal(expected, input_slot.reconstructFromH5G(h5g, patchBoard))
        raise SkipTest # TODO: implement your test here

    def test_setDirty(self):
        # input_slot = InputSlot(name, operator, stype, rtype, value, optional)
        # assert_equal(expected, input_slot.setDirty(*args, **kwargs))
        raise SkipTest # TODO: implement your test here

    def test_setValue(self):
        # input_slot = InputSlot(name, operator, stype, rtype, value, optional)
        # assert_equal(expected, input_slot.setValue(value, notify))
        raise SkipTest # TODO: implement your test here

    def test_shape(self):
        # input_slot = InputSlot(name, operator, stype, rtype, value, optional)
        # assert_equal(expected, input_slot.shape())
        raise SkipTest # TODO: implement your test here

    def test_value(self):
        # input_slot = InputSlot(name, operator, stype, rtype, value, optional)
        # assert_equal(expected, input_slot.value())
        raise SkipTest # TODO: implement your test here

class TestOutputSlot:
    def test___init__(self):
        # output_slot = OutputSlot(name, operator, stype, rtype)
        raise SkipTest # TODO: implement your test here

    def test___setitem__(self):
        # output_slot = OutputSlot(name, operator, stype, rtype)
        # assert_equal(expected, output_slot.__setitem__(key, value))
        raise SkipTest # TODO: implement your test here

    def test_axistags(self):
        # output_slot = OutputSlot(name, operator, stype, rtype)
        # assert_equal(expected, output_slot.axistags())
        raise SkipTest # TODO: implement your test here

    def test_disconnect(self):
        # output_slot = OutputSlot(name, operator, stype, rtype)
        # assert_equal(expected, output_slot.disconnect())
        raise SkipTest # TODO: implement your test here

    def test_disconnectSlot(self):
        # output_slot = OutputSlot(name, operator, stype, rtype)
        # assert_equal(expected, output_slot.disconnectSlot(partner))
        raise SkipTest # TODO: implement your test here

    def test_dtype(self):
        # output_slot = OutputSlot(name, operator, stype, rtype)
        # assert_equal(expected, output_slot.dtype())
        raise SkipTest # TODO: implement your test here

    def test_dumpToH5G(self):
        # output_slot = OutputSlot(name, operator, stype, rtype)
        # assert_equal(expected, output_slot.dumpToH5G(h5g, patchBoard))
        raise SkipTest # TODO: implement your test here

    def test_getInstance(self):
        # output_slot = OutputSlot(name, operator, stype, rtype)
        # assert_equal(expected, output_slot.getInstance(operator))
        raise SkipTest # TODO: implement your test here

    def test_reconstructFromH5G(self):
        # output_slot = OutputSlot(name, operator, stype, rtype)
        # assert_equal(expected, output_slot.reconstructFromH5G(h5g, patchBoard))
        raise SkipTest # TODO: implement your test here

    def test_registerDirtyCallback(self):
        # output_slot = OutputSlot(name, operator, stype, rtype)
        # assert_equal(expected, output_slot.registerDirtyCallback(function, **kwargs))
        raise SkipTest # TODO: implement your test here

    def test_setDirty(self):
        # output_slot = OutputSlot(name, operator, stype, rtype)
        # assert_equal(expected, output_slot.setDirty(*args, **kwargs))
        raise SkipTest # TODO: implement your test here

    def test_shape(self):
        # output_slot = OutputSlot(name, operator, stype, rtype)
        # assert_equal(expected, output_slot.shape())
        raise SkipTest # TODO: implement your test here

    def test_unregisterDirtyCallback(self):
        # output_slot = OutputSlot(name, operator, stype, rtype)
        # assert_equal(expected, output_slot.unregisterDirtyCallback(function))
        raise SkipTest # TODO: implement your test here

class TestMultiInputSlot:
    def test___getitem__(self):
        # multi_input_slot = MultiInputSlot(name, operator, stype, rtype, level, value, optional)
        # assert_equal(expected, multi_input_slot.__getitem__(key))
        raise SkipTest # TODO: implement your test here

    def test___init__(self):
        # multi_input_slot = MultiInputSlot(name, operator, stype, rtype, level, value, optional)
        raise SkipTest # TODO: implement your test here

    def test___len__(self):
        # multi_input_slot = MultiInputSlot(name, operator, stype, rtype, level, value, optional)
        # assert_equal(expected, multi_input_slot.__len__())
        raise SkipTest # TODO: implement your test here

    def test_connect(self):
        # multi_input_slot = MultiInputSlot(name, operator, stype, rtype, level, value, optional)
        # assert_equal(expected, multi_input_slot.connect(partner, notify))
        raise SkipTest # TODO: implement your test here

    def test_connectOk(self):
        # multi_input_slot = MultiInputSlot(name, operator, stype, rtype, level, value, optional)
        # assert_equal(expected, multi_input_slot.connectOk(partner))
        raise SkipTest # TODO: implement your test here

    def test_connected(self):
        # multi_input_slot = MultiInputSlot(name, operator, stype, rtype, level, value, optional)
        # assert_equal(expected, multi_input_slot.connected())
        raise SkipTest # TODO: implement your test here

    def test_disconnect(self):
        # multi_input_slot = MultiInputSlot(name, operator, stype, rtype, level, value, optional)
        # assert_equal(expected, multi_input_slot.disconnect())
        raise SkipTest # TODO: implement your test here

    def test_dumpToH5G(self):
        # multi_input_slot = MultiInputSlot(name, operator, stype, rtype, level, value, optional)
        # assert_equal(expected, multi_input_slot.dumpToH5G(h5g, patchBoard))
        raise SkipTest # TODO: implement your test here

    def test_getInstance(self):
        # multi_input_slot = MultiInputSlot(name, operator, stype, rtype, level, value, optional)
        # assert_equal(expected, multi_input_slot.getInstance(operator))
        raise SkipTest # TODO: implement your test here

    def test_graph(self):
        # multi_input_slot = MultiInputSlot(name, operator, stype, rtype, level, value, optional)
        # assert_equal(expected, multi_input_slot.graph())
        raise SkipTest # TODO: implement your test here

    def test_notifySubSlotDirty(self):
        # multi_input_slot = MultiInputSlot(name, operator, stype, rtype, level, value, optional)
        # assert_equal(expected, multi_input_slot.notifySubSlotDirty(slots, indexes, roi))
        raise SkipTest # TODO: implement your test here

    def test_propagateDirty(self):
        # multi_input_slot = MultiInputSlot(name, operator, stype, rtype, level, value, optional)
        # assert_equal(expected, multi_input_slot.propagateDirty(slot, roi))
        raise SkipTest # TODO: implement your test here

    def test_reconstructFromH5G(self):
        # multi_input_slot = MultiInputSlot(name, operator, stype, rtype, level, value, optional)
        # assert_equal(expected, multi_input_slot.reconstructFromH5G(h5g, patchBoard))
        raise SkipTest # TODO: implement your test here

    def test_removeSlot(self):
        # multi_input_slot = MultiInputSlot(name, operator, stype, rtype, level, value, optional)
        # assert_equal(expected, multi_input_slot.removeSlot(index, notify, event))
        raise SkipTest # TODO: implement your test here

    def test_resize(self):
        # multi_input_slot = MultiInputSlot(name, operator, stype, rtype, level, value, optional)
        # assert_equal(expected, multi_input_slot.resize(size, notify, event))
        raise SkipTest # TODO: implement your test here

    def test_setDirty(self):
        # multi_input_slot = MultiInputSlot(name, operator, stype, rtype, level, value, optional)
        # assert_equal(expected, multi_input_slot.setDirty(roi))
        raise SkipTest # TODO: implement your test here

    def test_setValue(self):
        # multi_input_slot = MultiInputSlot(name, operator, stype, rtype, level, value, optional)
        # assert_equal(expected, multi_input_slot.setValue(value))
        raise SkipTest # TODO: implement your test here

    def test_value(self):
        # multi_input_slot = MultiInputSlot(name, operator, stype, rtype, level, value, optional)
        # assert_equal(expected, multi_input_slot.value())
        raise SkipTest # TODO: implement your test here

class TestMultiOutputSlot:
    def test___getitem__(self):
        # multi_output_slot = MultiOutputSlot(name, operator, stype, rtype, level)
        # assert_equal(expected, multi_output_slot.__getitem__(key))
        raise SkipTest # TODO: implement your test here

    def test___init__(self):
        # multi_output_slot = MultiOutputSlot(name, operator, stype, rtype, level)
        raise SkipTest # TODO: implement your test here

    def test___len__(self):
        # multi_output_slot = MultiOutputSlot(name, operator, stype, rtype, level)
        # assert_equal(expected, multi_output_slot.__len__())
        raise SkipTest # TODO: implement your test here

    def test___setitem__(self):
        # multi_output_slot = MultiOutputSlot(name, operator, stype, rtype, level)
        # assert_equal(expected, multi_output_slot.__setitem__(key, value))
        raise SkipTest # TODO: implement your test here

    def test_append(self):
        # multi_output_slot = MultiOutputSlot(name, operator, stype, rtype, level)
        # assert_equal(expected, multi_output_slot.append(outputSlot, event))
        raise SkipTest # TODO: implement your test here

    def test_clearAllSlots(self):
        # multi_output_slot = MultiOutputSlot(name, operator, stype, rtype, level)
        # assert_equal(expected, multi_output_slot.clearAllSlots())
        raise SkipTest # TODO: implement your test here

    def test_connectOk(self):
        # multi_output_slot = MultiOutputSlot(name, operator, stype, rtype, level)
        # assert_equal(expected, multi_output_slot.connectOk(partner))
        raise SkipTest # TODO: implement your test here

    def test_disconnect(self):
        # multi_output_slot = MultiOutputSlot(name, operator, stype, rtype, level)
        # assert_equal(expected, multi_output_slot.disconnect())
        raise SkipTest # TODO: implement your test here

    def test_disconnectSlot(self):
        # multi_output_slot = MultiOutputSlot(name, operator, stype, rtype, level)
        # assert_equal(expected, multi_output_slot.disconnectSlot(partner))
        raise SkipTest # TODO: implement your test here

    def test_dumpToH5G(self):
        # multi_output_slot = MultiOutputSlot(name, operator, stype, rtype, level)
        # assert_equal(expected, multi_output_slot.dumpToH5G(h5g, patchBoard))
        raise SkipTest # TODO: implement your test here

    def test_execute(self):
        # multi_output_slot = MultiOutputSlot(name, operator, stype, rtype, level)
        # assert_equal(expected, multi_output_slot.execute(slot, roi, result))
        raise SkipTest # TODO: implement your test here

    def test_getInstance(self):
        # multi_output_slot = MultiOutputSlot(name, operator, stype, rtype, level)
        # assert_equal(expected, multi_output_slot.getInstance(operator))
        raise SkipTest # TODO: implement your test here

    def test_getOutSlot(self):
        # multi_output_slot = MultiOutputSlot(name, operator, stype, rtype, level)
        # assert_equal(expected, multi_output_slot.getOutSlot(slot, key, result))
        raise SkipTest # TODO: implement your test here

    def test_getSubOutSlot(self):
        # multi_output_slot = MultiOutputSlot(name, operator, stype, rtype, level)
        # assert_equal(expected, multi_output_slot.getSubOutSlot(slots, indexes, key, result))
        raise SkipTest # TODO: implement your test here

    def test_graph(self):
        # multi_output_slot = MultiOutputSlot(name, operator, stype, rtype, level)
        # assert_equal(expected, multi_output_slot.graph())
        raise SkipTest # TODO: implement your test here

    def test_insert(self):
        # multi_output_slot = MultiOutputSlot(name, operator, stype, rtype, level)
        # assert_equal(expected, multi_output_slot.insert(index, outputSlot, event))
        raise SkipTest # TODO: implement your test here

    def test_pop(self):
        # multi_output_slot = MultiOutputSlot(name, operator, stype, rtype, level)
        # assert_equal(expected, multi_output_slot.pop(index, event))
        raise SkipTest # TODO: implement your test here

    def test_reconstructFromH5G(self):
        # multi_output_slot = MultiOutputSlot(name, operator, stype, rtype, level)
        # assert_equal(expected, multi_output_slot.reconstructFromH5G(h5g, patchBoard))
        raise SkipTest # TODO: implement your test here

    def test_remove(self):
        # multi_output_slot = MultiOutputSlot(name, operator, stype, rtype, level)
        # assert_equal(expected, multi_output_slot.remove(outputSlot, event))
        raise SkipTest # TODO: implement your test here

    def test_resize(self):
        # multi_output_slot = MultiOutputSlot(name, operator, stype, rtype, level)
        # assert_equal(expected, multi_output_slot.resize(size, event))
        raise SkipTest # TODO: implement your test here

    def test_setDirty(self):
        # multi_output_slot = MultiOutputSlot(name, operator, stype, rtype, level)
        # assert_equal(expected, multi_output_slot.setDirty(roi))
        raise SkipTest # TODO: implement your test here

class TestInputDict:
    def test___getitem__(self):
        # input_dict = InputDict(operator)
        # assert_equal(expected, input_dict.__getitem__(key))
        raise SkipTest # TODO: implement your test here

    def test___init__(self):
        # input_dict = InputDict(operator)
        raise SkipTest # TODO: implement your test here

    def test___setitem__(self):
        # input_dict = InputDict(operator)
        # assert_equal(expected, input_dict.__setitem__(key, value))
        raise SkipTest # TODO: implement your test here

    def test_reconstructFromH5G(self):
        # input_dict = InputDict(operator)
        # assert_equal(expected, input_dict.reconstructFromH5G(h5g, patchBoard))
        raise SkipTest # TODO: implement your test here

class TestOutputDict:
    def test___getitem__(self):
        # output_dict = OutputDict(operator)
        # assert_equal(expected, output_dict.__getitem__(key))
        raise SkipTest # TODO: implement your test here

    def test___init__(self):
        # output_dict = OutputDict(operator)
        raise SkipTest # TODO: implement your test here

    def test___setitem__(self):
        # output_dict = OutputDict(operator)
        # assert_equal(expected, output_dict.__setitem__(key, value))
        raise SkipTest # TODO: implement your test here

    def test_reconstructFromH5G(self):
        # output_dict = OutputDict(operator)
        # assert_equal(expected, output_dict.reconstructFromH5G(h5g, patchBoard))
        raise SkipTest # TODO: implement your test here

class TestOperatorMetaClass:
    def test___call__(self):
        # operator_meta_class = OperatorMetaClass(classname, bases, classDict)
        # assert_equal(expected, operator_meta_class.__call__(*args, **kwargs))
        raise SkipTest # TODO: implement your test here

    def test___init__(self):
        # operator_meta_class = OperatorMetaClass(classname, bases, classDict)
        raise SkipTest # TODO: implement your test here

    def test___new__(self):
        # operator_meta_class = OperatorMetaClass(classname, bases, classDict)
        raise SkipTest # TODO: implement your test here

class TestOperator:
    def test___new__(self):
        # operator = Operator(*args, **kwargs)
        raise SkipTest # TODO: implement your test here

    def test_connect(self):
        # operator = Operator(*args, **kwargs)
        # assert_equal(expected, operator.connect(**kwargs))
        raise SkipTest # TODO: implement your test here

    def test_connected(self):
        # operator = Operator(*args, **kwargs)
        # assert_equal(expected, operator.connected())
        raise SkipTest # TODO: implement your test here

    def test_disconnect(self):
        # operator = Operator(*args, **kwargs)
        # assert_equal(expected, operator.disconnect())
        raise SkipTest # TODO: implement your test here

    def test_dumpToH5G(self):
        # operator = Operator(*args, **kwargs)
        # assert_equal(expected, operator.dumpToH5G(h5g, patchBoard))
        raise SkipTest # TODO: implement your test here

    def test_execute(self):
        # operator = Operator(*args, **kwargs)
        # assert_equal(expected, operator.execute(slot, roi, result))
        raise SkipTest # TODO: implement your test here

    def test_getSubOutSlot(self):
        # operator = Operator(*args, **kwargs)
        # assert_equal(expected, operator.getSubOutSlot(slots, indexes, key, result))
        raise SkipTest # TODO: implement your test here

    def test_notifyConnect(self):
        # operator = Operator(*args, **kwargs)
        # assert_equal(expected, operator.notifyConnect(inputSlot))
        raise SkipTest # TODO: implement your test here

    def test_notifyConnectAll(self):
        # operator = Operator(*args, **kwargs)
        # assert_equal(expected, operator.notifyConnectAll())
        raise SkipTest # TODO: implement your test here

    def test_notifyDirty(self):
        # operator = Operator(*args, **kwargs)
        # assert_equal(expected, operator.notifyDirty(inputSlot, key))
        raise SkipTest # TODO: implement your test here

    def test_notifyDisconnect(self):
        # operator = Operator(*args, **kwargs)
        # assert_equal(expected, operator.notifyDisconnect(slot))
        raise SkipTest # TODO: implement your test here

    def test_notifySubConnect(self):
        # operator = Operator(*args, **kwargs)
        # assert_equal(expected, operator.notifySubConnect(slots, indexes))
        raise SkipTest # TODO: implement your test here

    def test_notifySubDisconnect(self):
        # operator = Operator(*args, **kwargs)
        # assert_equal(expected, operator.notifySubDisconnect(slots, indexes))
        raise SkipTest # TODO: implement your test here

    def test_notifySubSlotDirty(self):
        # operator = Operator(*args, **kwargs)
        # assert_equal(expected, operator.notifySubSlotDirty(slots, indexes, key))
        raise SkipTest # TODO: implement your test here

    def test_notifySubSlotInsert(self):
        # operator = Operator(*args, **kwargs)
        # assert_equal(expected, operator.notifySubSlotInsert(slots, indexes))
        raise SkipTest # TODO: implement your test here

    def test_notifySubSlotRemove(self):
        # operator = Operator(*args, **kwargs)
        # assert_equal(expected, operator.notifySubSlotRemove(slots, indexes))
        raise SkipTest # TODO: implement your test here

    def test_notifySubSlotResize(self):
        # operator = Operator(*args, **kwargs)
        # assert_equal(expected, operator.notifySubSlotResize(slots, indexes, size, event))
        raise SkipTest # TODO: implement your test here

    def test_propagateDirty(self):
        # operator = Operator(*args, **kwargs)
        # assert_equal(expected, operator.propagateDirty(inputSlot, roi))
        raise SkipTest # TODO: implement your test here

    def test_reconstructFromH5G(self):
        # operator = Operator(*args, **kwargs)
        # assert_equal(expected, operator.reconstructFromH5G(h5g, patchBoard))
        raise SkipTest # TODO: implement your test here

    def test_setInSlot(self):
        # operator = Operator(*args, **kwargs)
        # assert_equal(expected, operator.setInSlot(slot, key, value))
        raise SkipTest # TODO: implement your test here

    def test_setSubInSlot(self):
        # operator = Operator(*args, **kwargs)
        # assert_equal(expected, operator.setSubInSlot(slots, indexes, key, value))
        raise SkipTest # TODO: implement your test here

    def test_setupOutputs(self):
        # operator = Operator(*args, **kwargs)
        # assert_equal(expected, operator.setupOutputs())
        raise SkipTest # TODO: implement your test here

class TestOperatorWrapper:
    def test___init__(self):
        # operator_wrapper = OperatorWrapper(operator, register)
        raise SkipTest # TODO: implement your test here

    def test_disconnect(self):
        # operator_wrapper = OperatorWrapper(operator, register)
        # assert_equal(expected, operator_wrapper.disconnect())
        raise SkipTest # TODO: implement your test here

    def test_dumpToH5G(self):
        # operator_wrapper = OperatorWrapper(operator, register)
        # assert_equal(expected, operator_wrapper.dumpToH5G(h5g, patchBoard))
        raise SkipTest # TODO: implement your test here

    def test_getOutSlot(self):
        # operator_wrapper = OperatorWrapper(operator, register)
        # assert_equal(expected, operator_wrapper.getOutSlot(slot, key, result))
        raise SkipTest # TODO: implement your test here

    def test_getSubOutSlot(self):
        # operator_wrapper = OperatorWrapper(operator, register)
        # assert_equal(expected, operator_wrapper.getSubOutSlot(slots, indexes, key, result))
        raise SkipTest # TODO: implement your test here

    def test_inputSlots(self):
        # operator_wrapper = OperatorWrapper(operator, register)
        # assert_equal(expected, operator_wrapper.inputSlots())
        raise SkipTest # TODO: implement your test here

    def test_notifyDirty(self):
        # operator_wrapper = OperatorWrapper(operator, register)
        # assert_equal(expected, operator_wrapper.notifyDirty(slot, key))
        raise SkipTest # TODO: implement your test here

    def test_notifySubSlotDirty(self):
        # operator_wrapper = OperatorWrapper(operator, register)
        # assert_equal(expected, operator_wrapper.notifySubSlotDirty(slots, indexes, key))
        raise SkipTest # TODO: implement your test here

    def test_outputSlots(self):
        # operator_wrapper = OperatorWrapper(operator, register)
        # assert_equal(expected, operator_wrapper.outputSlots())
        raise SkipTest # TODO: implement your test here

    def test_reconstructFromH5G(self):
        # operator_wrapper = OperatorWrapper(operator, register)
        # assert_equal(expected, operator_wrapper.reconstructFromH5G(h5g, patchBoard))
        raise SkipTest # TODO: implement your test here

    def test_setInSlot(self):
        # operator_wrapper = OperatorWrapper(operator, register)
        # assert_equal(expected, operator_wrapper.setInSlot(slot, key, value))
        raise SkipTest # TODO: implement your test here

    def test_setSubInSlot(self):
        # operator_wrapper = OperatorWrapper(operator, register)
        # assert_equal(expected, operator_wrapper.setSubInSlot(multislot, slot, index, key, value))
        raise SkipTest # TODO: implement your test here

class TestOperatorGroupGraph:
    def test___init__(self):
        # operator_group_graph = OperatorGroupGraph(originalGraph)
        raise SkipTest # TODO: implement your test here

    def test_dumpToH5G(self):
        # operator_group_graph = OperatorGroupGraph(originalGraph)
        # assert_equal(expected, operator_group_graph.dumpToH5G(h5g, patchBoard))
        raise SkipTest # TODO: implement your test here

    def test_finalize(self):
        # operator_group_graph = OperatorGroupGraph(originalGraph)
        # assert_equal(expected, operator_group_graph.finalize())
        raise SkipTest # TODO: implement your test here

    def test_freeWorkers(self):
        # operator_group_graph = OperatorGroupGraph(originalGraph)
        # assert_equal(expected, operator_group_graph.freeWorkers())
        raise SkipTest # TODO: implement your test here

    def test_putFinalize(self):
        # operator_group_graph = OperatorGroupGraph(originalGraph)
        # assert_equal(expected, operator_group_graph.putFinalize(reqObject))
        raise SkipTest # TODO: implement your test here

    def test_putTask(self):
        # operator_group_graph = OperatorGroupGraph(originalGraph)
        # assert_equal(expected, operator_group_graph.putTask(reqObject))
        raise SkipTest # TODO: implement your test here

    def test_reconstructFromH5G(self):
        # operator_group_graph = OperatorGroupGraph(originalGraph)
        # assert_equal(expected, operator_group_graph.reconstructFromH5G(h5g, patchBoard))
        raise SkipTest # TODO: implement your test here

    def test_registerOperator(self):
        # operator_group_graph = OperatorGroupGraph(originalGraph)
        # assert_equal(expected, operator_group_graph.registerOperator(op))
        raise SkipTest # TODO: implement your test here

    def test_removeOperator(self):
        # operator_group_graph = OperatorGroupGraph(originalGraph)
        # assert_equal(expected, operator_group_graph.removeOperator(op))
        raise SkipTest # TODO: implement your test here

    def test_replaceOperator(self):
        # operator_group_graph = OperatorGroupGraph(originalGraph)
        # assert_equal(expected, operator_group_graph.replaceOperator(op1, op2))
        raise SkipTest # TODO: implement your test here

    def test_suspended(self):
        # operator_group_graph = OperatorGroupGraph(originalGraph)
        # assert_equal(expected, operator_group_graph.suspended())
        raise SkipTest # TODO: implement your test here

class TestOperatorGroup:
    def test___init__(self):
        # operator_group = OperatorGroup(graph, register)
        raise SkipTest # TODO: implement your test here

    def test_getOutSlot(self):
        # operator_group = OperatorGroup(graph, register)
        # assert_equal(expected, operator_group.getOutSlot(slot, key, result))
        raise SkipTest # TODO: implement your test here

    def test_getSubOutSlot(self):
        # operator_group = OperatorGroup(graph, register)
        # assert_equal(expected, operator_group.getSubOutSlot(slots, indexes, key, result))
        raise SkipTest # TODO: implement your test here

    def test_setupInputSlots(self):
        # operator_group = OperatorGroup(graph, register)
        # assert_equal(expected, operator_group.setupInputSlots())
        raise SkipTest # TODO: implement your test here

    def test_setupOutputSlots(self):
        # operator_group = OperatorGroup(graph, register)
        # assert_equal(expected, operator_group.setupOutputSlots())
        raise SkipTest # TODO: implement your test here

class TestWorker:
    def test___init__(self):
        # worker = Worker(graph)
        raise SkipTest # TODO: implement your test here

    def test_run(self):
        # worker = Worker(graph)
        # assert_equal(expected, worker.run())
        raise SkipTest # TODO: implement your test here

    def test_signalWorkAvailable(self):
        # worker = Worker(graph)
        # assert_equal(expected, worker.signalWorkAvailable())
        raise SkipTest # TODO: implement your test here

class TestGraph:
    def test___init__(self):
        # graph = Graph(numThreads, softMaxMem)
        raise SkipTest # TODO: implement your test here

    def test_dumpToH5G(self):
        # graph = Graph(numThreads, softMaxMem)
        # assert_equal(expected, graph.dumpToH5G(h5g, patchBoard))
        raise SkipTest # TODO: implement your test here

    def test_finalize(self):
        # graph = Graph(numThreads, softMaxMem)
        # assert_equal(expected, graph.finalize())
        raise SkipTest # TODO: implement your test here

    def test_putFinalize(self):
        # graph = Graph(numThreads, softMaxMem)
        # assert_equal(expected, graph.putFinalize(reqObject))
        raise SkipTest # TODO: implement your test here

    def test_putTask(self):
        # graph = Graph(numThreads, softMaxMem)
        # assert_equal(expected, graph.putTask(reqObject))
        raise SkipTest # TODO: implement your test here

    def test_reconstructFromH5G(self):
        # graph = Graph(numThreads, softMaxMem)
        # assert_equal(expected, graph.reconstructFromH5G(h5g, patchBoard))
        raise SkipTest # TODO: implement your test here

    def test_registerOperator(self):
        # graph = Graph(numThreads, softMaxMem)
        # assert_equal(expected, graph.registerOperator(op))
        raise SkipTest # TODO: implement your test here

    def test_removeOperator(self):
        # graph = Graph(numThreads, softMaxMem)
        # assert_equal(expected, graph.removeOperator(op))
        raise SkipTest # TODO: implement your test here

    def test_replaceOperator(self):
        # graph = Graph(numThreads, softMaxMem)
        # assert_equal(expected, graph.replaceOperator(op1, op2))
        raise SkipTest # TODO: implement your test here

    def test_resumeGraph(self):
        # graph = Graph(numThreads, softMaxMem)
        # assert_equal(expected, graph.resumeGraph())
        raise SkipTest # TODO: implement your test here

    def test_stopGraph(self):
        # graph = Graph(numThreads, softMaxMem)
        # assert_equal(expected, graph.stopGraph())
        raise SkipTest # TODO: implement your test here

    def test_stopGraphs(self):
        # graph = Graph(numThreads, softMaxMem)
        # assert_equal(expected, graph.stopGraphs())
        raise SkipTest # TODO: implement your test here

    def test_suspendGraph(self):
        # graph = Graph(numThreads, softMaxMem)
        # assert_equal(expected, graph.suspendGraph())
        raise SkipTest # TODO: implement your test here

