import functools
from lazyflow.operators.opReorderAxes import OpReorderAxes
from lazyflow.graph import Operator, InputSlot, OutputSlot

def reorder_options(internal_axes_order, exceptions=[]):
    assert isinstance(internal_axes_order, str)
    assert isinstance(exceptions, list)

    def add_exceptions(cls):
        cls._internal_axes_order = internal_axes_order
        cls._reorder_exceptions = exceptions
        return cls

    return add_exceptions


def guard_methods(cls):
    methods = [member for member, member_type in cls.__dict__.items()
               if isinstance(member_type, type(lambda:0)) and
               member != '__getattribute__' and
               member != '__init__' and 
               member != 'setupOutputs']

    class_methods = [member for member, member_type in cls.__dict__.items()
                     if isinstance(member_type, classmethod)]

    property_methods = [member for member, member_type in cls.__dict__.items()
                        if isinstance(member_type, property)]

    # static_methods = [member for member, member_type in cls.__dict__.items()
    #                   if isinstance(member_type, staticmethod)]

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
        print('old_get', old_get)

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
    if '_reorder_exceptions' not in dir(cls):
        cls._reorder_exceptions = []

    cls = guard_methods(cls)

    inputSlots = [s.name for s in cls.inputSlots
                  if s.name not in cls._reorder_exceptions]
    outputSlots = [s.name for s in cls.outputSlots
                   if s.name not in cls._reorder_exceptions]

    # meta = [s[0].meta for s in inputSlots]
    # print('metaData', meta)

    old_meth = getattr(cls, '__init__')
    def guard(fn):
        @functools.wraps(old_meth)
        def wrap(self, *args, **kwargs):
            self._inner_call = True
            ret = fn(self, *args, **kwargs)
            self._inner_call = False
            self._reorderedInput = {}
            for name in inputSlots:
                slot = self.__getattribute__(name)
                reordered = OpReorderAxes(parent=self) 
                reordered.AxisOrder.setValue(self._internal_axes_order)
                self._reorderedInput[name] = reordered
                self._reorderedInput[name].Input.connect(slot)
                # print('slot here', slot.meta.getAxisKeys())
            self._reorderedOutput = {}
            for name in outputSlots:
                self._reorderedOutput[name] = OpReorderAxes(parent=self)
                self._reorderedOutput[name].AxisOrder.setValue('tzyxc')

            return ret
        return wrap

    setattr(cls, '__init__', guard(old_meth))

    # assert self.Input.meta.getAxisKeys() == list('tzyxc')
    
    old_meth = getattr(cls, 'setupOutputs')
    def guard(fn):
        @functools.wraps(old_meth)
        def wrap(self):
            self._inner_call = False
            for name in outputSlots:
                slot = self.__getattribute__(name)
                # print('output here', self._reorderedOutput[name].Output)
                # print('slot here', slot)
                slot.connect(self._reorderedOutput[name].Output)
                # print('done here')
                # self._reorderedOutput[name].Input.connect()

            self._inner_call = True
            ret = fn(self)
            self._inner_call = False
            return ret
        return wrap

    setattr(cls, 'setupOutputs', guard(old_meth))

    old_getattribute = getattr(cls, '__getattribute__')
    def __getattribute__(self, item):
        # print('get item', item)
        if item in inputSlots:
            print('get input slot', item)
            if self._inner_call:
                print('inner call')
                return self._reorderedInput[item].Output

        if item in outputSlots:
            print('get output slot', item)
            if self._inner_call:
                print('inner call')
                return self._reorderedOutput[item].Input
            else:
                print('outer call')
        return super(cls, self).__getattribute__(item)
    # def guard(fn):
    #     @functools.wraps(old_meth)
    #     def wrap(self, arg):
    #         # self._inner_call = True
    #         # self._reorderedInput = []
    #         # for slot in inputSlots:
    #         #     self._reorderedInput.append(
    #         #         OpReorderAxes(parent=self)
    #         #     )
    #         # for reordered in self._reorderedInput:
    #         #     reordered.AxisOrder = self._internal_axes_order
    #         ret = fn(self, arg)
    #         # self._inner_call = False
    #         return ret
    #     return wrap

    setattr(cls, '__getattribute__', __getattribute__)   


    return cls


if __name__ == '__main__':
    class Slot(object):
        def __init__(self, name):
            self.name = name

    @reorder
    @reorder_options('tzyxc', ['except_fct'])
    class Test(object):
        a = Slot('a')
        b = Slot('b')
        c = Slot('c')
        d = Slot('d')

        inputSlots = []
        outputSlots = []

        def __init__(self):
            print('init called, self:', self)
            # print('a', self.a)
            self.inputSlots.append(self.a)
            self.inputSlots.append(self.b)
            self.outputSlots.append(self.c)
            self.outputSlots.append(self.d)
            print('inner call', self._inner_call)
            # print('dict', self.__dict__)

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
    print(test.a)
    print(test.except_fct())

    print(test.class_meth(5))
    print(test.static_meth())
    print(test.property_meth)
