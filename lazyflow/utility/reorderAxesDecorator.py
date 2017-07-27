import functools
from lazyflow.operators.opReorderAxes import OpReorderAxes


def reorder_options(internal_axes_order, exceptions=[],
                    output_axes_order='tczyx'):
    """
        Adds reorder options to the specific operator class that the decorator
        reorder accesses. This is not done by handing arguments to the reorder
        decorator directly, because then the reorder decorator would need to be
        wrapped, which would lead return a function (wrapper) as the operator
        class, which conflicts with inheritance of the specific operator (as
        the inheriting operator class appears to be a function). Therefore the
        arguments are outsourced in this decorator.

        note: Use this function decorator only in combination with the reorder
              decorator and as second (inner) decorator.
              (see example usage below)

        @param internal_axes_order: str Axes order the decorated operator
                                        assumes internally.ResizedShape
        @param exceptions: list(str) List of slot names that do not need to be
                                     reordered.
        @param output_axes_order: str Output Axes order for all reordered
                                      output slots.

        Example usage:

            @reorder
            @reorder_options('tzyxc', ['ResizedShape'])
            class OpResize5D(Operator):
                ...

    """
    assert isinstance(internal_axes_order, str)
    assert isinstance(exceptions, list)
    assert all([isinstance(ex, str) for ex in exceptions])
    assert isinstance(output_axes_order, str)

    def add_exceptions(cls):
        assert all([ex in [s.name for s in cls.inputSlots + cls.outputSlots]
                    for ex in exceptions])
        cls._internal_axes_order = internal_axes_order
        cls._reorder_exceptions = exceptions
        cls._output_axes_order = output_axes_order
        return cls

    return add_exceptions


def guard_methods(cls):
    """
        helper function for reorder
    """
    methods = [member for member, member_type in cls.__dict__.items()
               if isinstance(member_type, type(lambda:0)) and
               member != '__getattribute__' and  # will be adapted individually
               member != '__init__'  # will be adapted individually
               ]

    class_methods = [member for member, member_type in cls.__dict__.items()
                     if isinstance(member_type, classmethod)]

    property_methods = [member for member, member_type in cls.__dict__.items()
                        if isinstance(member_type, property)]

    # flag when methods are called from within the class
    cls._inner_call = 0
    # overwrite methods with guarded versions thereof
    for meth in methods:
        old_meth = getattr(cls, meth)

        def guard(fn):
            @functools.wraps(old_meth)
            def wrap(self, *args, **kwargs):
                if self._inner_call:
                    return fn(self, *args, **kwargs)
                else:
                    self._inner_call = True
                    ret = fn(self, *args, **kwargs)
                    self._inner_call = False
                    return ret
            return wrap

        setattr(cls, meth, guard(old_meth))

    # overwrite class methods with guarded versions thereof
    for meth in class_methods:
        old_meth = getattr(cls, meth)

        def guard(fn):
            @functools.wraps(old_meth)
            def wrap(self, *args, **kwargs):
                if self._inner_call:
                    return fn(*args, **kwargs)
                else:
                    self._inner_call = True
                    ret = fn(*args, **kwargs)
                    self._inner_call = False
                    return ret
            return wrap

        setattr(cls, meth, guard(old_meth))

    # overwrite property methods with guarded versions thereof
    for meth in property_methods:
        old_get = getattr(cls, meth).__get__

        def guard(fn):
            @property
            def wrap(self):
                if self._inner_call:
                    return fn(self)
                else:
                    self._inner_call = True
                    ret = fn(self)
                    self._inner_call = False
                    return ret
            return wrap

        setattr(cls, meth, guard(old_get))

    return cls


def reorder(cls):
    """
        Decorator function to reorder all input and output channels, to
        preserve an inner axes order within the operator. Must be used in
        combination with reorder_options.
    """
    if '_reorder_exceptions' not in dir(cls):
        cls._reorder_exceptions = []

    cls = guard_methods(cls)

    inputSlots = [s.name for s in cls.inputSlots
                  if s.name not in cls._reorder_exceptions]
    outputSlots = [s.name for s in cls.outputSlots
                   if s.name not in cls._reorder_exceptions]

    # change __init__ in order to squeeze in the opReorderAxes ops
    old_meth = getattr(cls, '__init__')

    def guard(fn):
        @functools.wraps(old_meth)
        def wrap(self, *args, **kwargs):
            self._inner_call = True
            ret = fn(self, *args, **kwargs)

            self._reorderedOutput = {}
            for name in outputSlots:
                self._reorderedOutput[name] = OpReorderAxes(parent=self.parent)
                self._reorderedOutput[name].AxisOrder.setValue(
                    cls._output_axes_order)
                slot = self.__getattribute__(name)
                self._reorderedOutput[name].Input.connect(slot)

            self._inner_call = False

            self._reorderedInput = {}
            for name in inputSlots:
                self._reorderedInput[name] = OpReorderAxes(parent=self)
                # or  ...... parent=self.parent)
                self._reorderedInput[name].AxisOrder.setValue(
                    self._internal_axes_order)
                slot = self.__getattribute__(name)
                self._reorderedInput[name].Input.connect(slot)

            return ret
        return wrap

    setattr(cls, '__init__', guard(old_meth))

    # old_meth = getattr(cls, 'setupOutputs')

    # def guard(fn):
    #     @functools.wraps(old_meth)
    #     def wrap(self):
    #         # self._inner_call = False
    #         # for name in outputSlots:
    #         #     slot = self.__getattribute__(name)
    #         #     # slot.connect(self._reorderedOutput[name].Output)
    #         #     print('slot here', slot)
    #         #     # print('done here')
    #         #     # self._reorderedOutput[name].Input.connect()

    #         self._inner_call = True
    #         ret = fn(self)
    #         self._inner_call = False
    #         return ret
    #     return wrap

    # setattr(cls, 'setupOutputs', guard(old_meth))

    # change __getattribute__ in order to squeeze in the opReorderAxes ops
    def __getattribute__(self, name):
        if name in inputSlots:
            if self._inner_call:
                # print('inner call to {}'.format(name))
                return self._reorderedInput[name].Output

        if name in outputSlots:
            if not self._inner_call:
                # print('outer call to {}'.format(name))
                return self._reorderedOutput[name].Output

        return super(cls, self).__getattribute__(name)

    setattr(cls, '__getattribute__', __getattribute__)

    return cls


if __name__ == '__main__':
    class Slot(object):
        def __init__(self, name):
            self.name = name

    @reorder
    @reorder_options('tzyxc', ['a', 'b', 'c', 'd'])
    class Test(object):
        inputSlots = [
            Slot('a'),
            Slot('b')
        ]
        outputSlots = [
            Slot('c'),
            Slot('d')
        ]

        def __init__(self):
            print('init called, self:', self)

        def some_method(self):
            print('some methods called')

        @classmethod
        def class_meth(self, x):
            print('class_meth call', self)
            print('class meth x', x)
            return 'class_meth'

        @staticmethod
        def static_meth():
            return 'static_meth'

        @property
        def property_meth(self):
            return 'property_meth'

        def except_fct(self):
            return 'except_fct'

        def setupOutputs(self):
            pass

    test = Test()
    print(test.some_method())
    print(test.except_fct())
    print(test.class_meth(5))
    print(test.static_meth())
    print(test.property_meth)
