import collections
import functools
import types

from lazyflow.graph import Operator
from lazyflow.operators.opReorderAxes import OpReorderAxes
from lazyflow.slot import InputSlot, OutputSlot

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
                                        assumes internally.
        @param exceptions: list(str) List of slot names that do not need to be
                                     reordered.
        @param output_axes_order: str Output Axes order for all reordered
                                      output slots.

        Example usage: (for a 'real-life example check OpGraphCut in ilastik)

            @reorder
            @reorder_options('tzyxc', ['ResizedShape'])
            class OpResize5D(Operator):
                ...

    """
    assert isinstance(internal_axes_order, str)
    assert isinstance(exceptions, list)
    assert all([isinstance(ex, str) for ex in exceptions])
    assert isinstance(output_axes_order, str)

    def set_options(cls):
        assert all([ex in [s.name for s in cls.inputSlots + cls.outputSlots]
                    for ex in exceptions])
        cls._internal_axes_order = internal_axes_order
        cls._reorder_exceptions = exceptions
        cls._output_axes_order = output_axes_order
        return cls
    return set_options


def guard_methods(cls):
    """ 
        helper function for reorder
        
        Flag with 'self._inner_call' when methods are called from within the class
        as opposed to accessing a slot of the operator from the "outside"
    """
    methods = [member for member, member_type in cls.__dict__.items()
               if isinstance(member_type, types.FunctionType) and
               member != '__getattribute__' and  # will be adapted individually
               member != '__init__' and  # will be adapted individually
               member != 'setupOutputs'  # will be adapted individually
               ]

    class_methods = [member for member, member_type in cls.__dict__.items()
                     if isinstance(member_type, classmethod)]

    property_methods = [member for member, member_type in cls.__dict__.items()
                        if isinstance(member_type, property)]

    # overwrite methods with guarded versions thereof
    for meth in methods:
        old_meth = getattr(cls, meth)

        def guard(fn):
            @functools.wraps(old_meth)
            def wrap(self, *args, **kwargs):
                if self._inner_call:
                    return fn(self, *args, **kwargs)
                else:
                    try:
                        self._inner_call = True
                        ret = fn(self, *args, **kwargs)
                        self._inner_call = False
                        return ret
                    except Exception:
                        raise
                    finally:
                        self._inner_call = False
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
                    try:
                        self._inner_call = True
                        ret = fn(*args, **kwargs)
                        self._inner_call = False
                        return ret
                    except Exception:
                        raise
                    finally:
                        self._inner_call = False
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
                    try:
                        self._inner_call = True
                        ret = fn(self)
                        self._inner_call = False
                        return ret
                    except Exception:
                        raise
                    finally:
                        self._inner_call = False
            return wrap

        setattr(cls, meth, guard(old_get))

    return cls


def reorder(cls):
    """
        Decorator function to reorder all input and output channels, to preserve an inner axes order within the
        operator.
        Must be used in combination with reorder_options!!!

        For every slot of a decorated operator, the distinction has to be made, if the slot was called by the operator
        itself, i.e. by one of its methods, or on the operator object from the 'outside'.

        Pseudo example to clarify:

        @reorder
        @reorder_options(internal_axis_order='set in stone by dev',
                         exceptions: 'i_already_follow_the_new_outside_order',
                         output_axes_order: 'the bright future')
        class MyOp(operator):
            Input = InputSlot()
            Output = OutputSlot()

            anarchySlot = InputSlot()

            def __init__(self):
                super().__init__()
                self.childOp = ChildOp()

                # direct connection of slots, not affected by reorder decorator
                self.childOp.InputA.connect(self.anarchySlot)

            def setupOutputs(self):
                # everything in here is automatically converted with respect to the inner and outer axes orders
                # In-between childOp's slot and this operator's slot a hidden OpReorderAxes is connected, which was
                # added by the reorder decorator
                self.childOp.InputB.connect(self.Input)
                self.Output.connect(self.childOp.Output)
    """
    if '_reorder_exceptions' not in dir(cls):
        cls._reorder_exceptions = []

    cls = guard_methods(cls)

    inputSlots = [s.name for s in cls.inputSlots
                  if s.name not in cls._reorder_exceptions]
    outputSlots = [s.name for s in cls.outputSlots
                   if s.name not in cls._reorder_exceptions]

    inner_prefix = 'inner_'
    cls._inner_call = False  # use this variable to distinguish in __getattribute__, which slot to return

    old_new = getattr(cls, '__new__')
    def guard(fn):
        @functools.wraps(old_new)
        def wrap(cls, *args, **kwargs):
            # add input slots with outer axis order
            for name in inputSlots:
                outer_name = inner_prefix + name
                # check if slot is already there
                if outer_name not in [s.name for s in cls.inputSlots]:
                    cls.inputSlots.append(InputSlot(outer_name))
            
            # add output slots with outer axis order
            for name in outputSlots:
                outer_name = inner_prefix + name
                # check if slot is already there
                if outer_name not in [s.name for s in cls.outputSlots]:
                    cls.outputSlots.append(OutputSlot(outer_name))

            return fn(cls, *args, **kwargs)
        return wrap

    setattr(cls, '__new__', guard(old_new))

    # change __init__ in order to squeeze in the opReorderAxes ops
    old_init = getattr(cls, '__init__')
    def guard(fn):
        @functools.wraps(old_init)
        def wrap(self, *args, graph=None, parent=None, **kwargs):
            ret = fn(self, *args, graph=graph, parent=parent, **kwargs)
            graph, parent = self.graph, self.parent
            self._inner_call = False

            self._opReorderInput = {}
            for name in inputSlots:
                self._opReorderInput[name] = OpReorderAxes(parent=self)
            
            self._opReorderOutput = {}
            for name in outputSlots:
                self._opReorderOutput[name] = OpReorderAxes(parent=self)

            return ret
        return wrap

    setattr(cls, '__init__', guard(old_init))

    # change setupOutputs in order to connect the squeezed in opReorderAxes ops
    old_setupOutputs = getattr(cls, 'setupOutputs')
    def guard(fn):
        @functools.wraps(old_setupOutputs)
        def wrap(self, *args, **kwargs):
            self._inner_call = False
            for name in inputSlots:
                self._opReorderInput[name].AxisOrder.setValue(self._internal_axes_order)

                slot = self.__getattribute__(name)
                self._opReorderInput[name].Input.connect(slot)

                inner_slot = self.__getattribute__(inner_prefix + name)
                inner_slot.connect(self._opReorderInput[name].Output, permit_distant_connection=True)
            
            for name in outputSlots:
                self._opReorderOutput[name].AxisOrder.setValue(cls._output_axes_order)

                inner_slot = self.__getattribute__(inner_prefix + name)
                self._opReorderOutput[name].Input.connect(inner_slot)
                
                slot = self.__getattribute__(name)
                slot.connect(self._opReorderOutput[name].Output)

            self._inner_call = True
            ret = fn(self, *args, **kwargs)
            self._inner_call = False

            return ret
        return wrap

    setattr(cls, 'setupOutputs', guard(old_setupOutputs))

    # change __getattribute__ in order to squeeze in the opReorderAxes ops
    def __getattribute__(self, name):
        if name in inputSlots:
            if self._inner_call:
                name = inner_prefix + name
        elif name in outputSlots:
            if self._inner_call:
                name = inner_prefix + name

        return super(cls, self).__getattribute__(name)

    setattr(cls, '__getattribute__', __getattribute__)
    return cls


if __name__ == '__main__':
    import vigra
    import os
    from lazyflow.graph import Graph
    from lazyflow.stype import ArrayLike

    from lazyflow.tools.schematic import generateSvgFileForOperator
    from lazyflow.operatorWrapper import OperatorWrapper

    test_args = ['arg0', 1, False]

    outer_order = 'tczyx'
    outer_shape = (1, 2, 3, 4, 5)
    inner_order = 'zyxct'
    inner_shape = tuple([outer_shape[outer_order.find(x)] for x in inner_order])

    svg_dir = '/Users/Fynn/Desktop/svg_tmp/'

    class OpSum(Operator):
        InputA = InputSlot()
        InputB = InputSlot()

        Output = OutputSlot()

        def setupOutputs(self):
            assert self.InputA.meta.getAxisKeys() == list(inner_order)
            assert self.InputA.meta.shape == self.InputB.meta.shape, "Can't add images of different shapes!"
            self.Output.meta.assignFrom(self.InputA.meta)

        def execute(self, slot, subindex, roi, result):
            a = self.InputA.get(roi).wait()
            b = self.InputB.get(roi).wait()
            result[...] = a + b
            return result

        def propagateDirty(self, slot, subindex, roi):
            self.Output.setDirty(roi)

    @reorder
    @reorder_options(inner_order, [], outer_order)
    class LazyOp(Operator):
        """ test op """
        name = 'LazyOp'

        in_a = InputSlot(stype=ArrayLike)
        in_b = InputSlot(stype=ArrayLike)

        out_a = OutputSlot(stype=ArrayLike)
        out_b = OutputSlot(stype=ArrayLike)

        def __init__(self, inner_order, *args, **kwargs):
            print('\tinit')
            super().__init__(*args, **kwargs)
            self.inner_order = inner_order
            self.opSum = OpSum(parent=self)

            # try here
            # # out_a pass-through of in_a
            # self.out_a.connect(self.in_a)
            print('\tinit done')

        def meth(self, *args):
            assert isinstance(self, LazyOp)
            assert len(args) == len(test_args)
            for test, got in zip(test_args, args):
                assert test == got

            return 'meth'

        @classmethod
        def class_meth(cls, *args):
            assert isinstance(cls, type)
            assert len(args) == len(test_args), (args, test_args)
            for test, got in zip(test_args, args):
                assert test == got

            return 'class_meth'

        @staticmethod
        def static_meth(*args):
            assert len(args) == len(test_args)
            for test, got in zip(test_args, args):
                assert test == got

            return 'static_meth'

        @property
        def property_meth(self):
            assert isinstance(self, LazyOp)
            return 'property_meth'

        def except_meth(self, *args):
            assert isinstance(self, LazyOp)
            assert len(args) == len(test_args)
            for test, got in zip(test_args, args):
                assert test == got

            return 'except_meth'

        def setupOutputs(self):
            # print('\tsetup outputs')
            # out_a pass-through of in_a
            self.out_a.connect(self.in_a)

            # out_b, sum of in_a and in_b
            # print('\n\n\n\n\n\nhere')
            self.opSum.InputA.connect(self.in_a)
            # print('here\n\n\n\n\n\n ')
            self.opSum.InputB.connect(self.in_b)
            self.out_b.connect(self.opSum.Output)
            # print('\tdone, inner shape', self.out_b.meta['shape'])

        def propagateDirty(self, slot, subindex, roi):
            # print('\tpropagateDirty')
            self.out_b.setDirty(roi)
            if slot == self.in_a:
                self.out_a.setDirty(roi)
            # print('\tpropagateDirty done')

    # single example operator
    lazyOp = LazyOp(graph=Graph(), inner_order=inner_order)
    lazyOp.setupOutputs()
    svg_path = os.path.join(svg_dir, 'lazyOp.svg')
    generateSvgFileForOperator(svg_path, lazyOp, 5)

    # embed tests in trivial parent operator
    class OpParent(Operator):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.lazyOp1 = LazyOp(inner_order=inner_order, parent=self)
            self.lazyOp2 = LazyOp(inner_order='txyzc', parent=self)

        def setupOutputs(self):
            tags = vigra.defaultAxistags(outer_order)
            a = vigra.VigraArray(outer_shape, value=1, axistags=tags)
            b = vigra.VigraArray(outer_shape, value=2, axistags=tags)
            # print('in a1')
            self.lazyOp1.in_a.setValue(a)
            # print('in a1 done')
            # print('in b1')
            self.lazyOp1.in_b.setValue(b)
            # print('in b1 done')            
            self.lazyOp1.setupOutputs()
            self.lazyOp2.setupOutputs()

            self.lazyOp2.in_a.connect(self.lazyOp1.out_a)
            self.lazyOp2.in_b.connect(self.lazyOp1.out_b)

        def check_lazyOp1(self):
            # check that method types are treated correctly (actual tests in LazyOp)
            self.lazyOp1.meth(*test_args)
            self.lazyOp1.class_meth(*test_args)
            self.lazyOp1.static_meth(*test_args)
            self.lazyOp1.property_meth
            self.lazyOp1.except_meth(*test_args)

            # when accessing the child's operators they should conform with the outside order. Here, the shape of the
            # resulting numpy.ndarray is tested to make sure we are not just checking meta data.
            assert self.lazyOp1.out_a[:].wait().shape == outer_shape
            assert self.lazyOp1.out_b[:].wait().shape == outer_shape

            tags = vigra.defaultAxistags(outer_order)
            expect = vigra.VigraArray(outer_shape, value=3, axistags=tags)

            assert (expect == self.lazyOp1.out_b[:].wait()).all()
            assert expect.axistags == self.lazyOp1.out_b.meta.axistags
            assert expect.shape == self.lazyOp1.out_b.meta.shape

        def check_lazyOp2(self):
            assert self.lazyOp2.in_a[:].wait().shape == outer_shape
            assert self.lazyOp2.in_b[:].wait().shape == outer_shape
            assert self.lazyOp2.out_a[:].wait().shape == outer_shape
            assert self.lazyOp2.out_b[:].wait().shape == outer_shape

            tags = vigra.defaultAxistags(outer_order)
            expect = vigra.VigraArray(outer_shape, value=4, axistags=tags)
            assert (expect == self.lazyOp2.out_b[:].wait()).all()
            assert expect.axistags == self.lazyOp2.out_b.meta.axistags
            assert expect.shape == self.lazyOp2.out_b.meta.shape

            # checking inner shapes by pretending to make inner calls
            self.lazyOp2._inner_call = True
            assert self.lazyOp2.in_a[:].wait().shape == inner_shape
            assert self.lazyOp2.in_b[:].wait().shape == inner_shape
            assert self.lazyOp2.out_a[:].wait().shape == inner_shape
            assert self.lazyOp2.out_b[:].wait().shape == inner_shape

    # ensemble of two example operators
    opParent = OpParent(graph=Graph())
    opParent.setupOutputs()
    opParent.check_lazyOp1()
    opParent.check_lazyOp2()
    generateSvgFileForOperator(os.path.join(svg_dir, 'opParent.svg'), opParent, 5)

    lazyWrap = OperatorWrapper(LazyOp, operator_kwargs={'inner_order': inner_order}, parent=opParent)
    lazyWrap.in_a.resize(1)
    lazyWrap.in_b.resize(1)
    tags = vigra.defaultAxistags(outer_order)
    a = vigra.VigraArray(outer_shape, value=1, axistags=tags)
    b = vigra.VigraArray(outer_shape, value=2, axistags=tags)
    print('in a1')
    lazyWrap.in_a[0].setValue(a)
    print('in a1 done')
    print('in b1')
    lazyWrap.in_b[0].setValue(b)
    print('in b1 done')

    lazyWrap.setupOutputs()
    print('innerOp')
    print(lazyWrap.innerOperators[0].out_a[:].wait().shape)
    print('slot')
    # print(lazyWrap.out_a[0][:].wait().shape)
    # generateSvgFileForOperator(os.path.join(svg_dir, 'lazyWrap.svg'), lazyWrap, 5)
