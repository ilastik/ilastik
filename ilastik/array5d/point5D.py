from collections import OrderedDict
from itertools import product
import numpy as np
from typing import Dict, Tuple, Iterator

class Point5D(object):
    LABELS = 'txyzc'
    LABEL_MAP = {label:index for index, label in enumerate(LABELS)}
    INT_TYPE = np.uint64

    def __init__(self, *, t:int, x:int, y:int, z:int, c:int):
        locs = locals()
        ordered_pairs = ((label, self.INT_TYPE(locs[label])) for label in self.LABELS)
        self._coords = OrderedDict(ordered_pairs)

    @classmethod
    def startpoint(cls, *, t:int=0, x:int=0, y:int=0, z:int=0, c:int=0):
        return cls(t=t or 0, x=x or 0, y=y or 0, z=z or 0, c=c or 0)

    @classmethod
    def endpoint(cls, *, shape:'Shape5D', t:int=None, x:int=None, y:int=None, z:int=None, c:int=None):
        return cls(t=t or shape.t, x=x or shape.x, y=y or shape.y, z=z or shape.z, c=c or shape.z)

    @classmethod
    def from_tuple(cls, tup:Tuple[int,int,int,int,int]):
        return cls(**{label:value for label, value in zip(cls.LABELS, tup)})

    @classmethod
    def startpoint_from_tuple(cls, tup: Tuple[int, int, int, int, int]):
        d = {k:v for k,v in zip(cls.LABELS, tup) if v is not None}
        return cls.startpoint(**d)

    @classmethod
    def endpoint_from_tuple(cls, tup: Tuple[int, int, int, int, int]):
        d = {k:v for k,v in zip(self.LABELS, tup) if v is not None}
        return cls.endpoint(**d)

    @classmethod
    def from_dict_with_defaults(cls, d:Dict, defaults:'Point5D'):
        if not set(d.keys()).issubset(set(cls.LABELS)):
            raise Exception(f"Invalid keys in dict {d}")
        params = {**defaults.to_dict(), **d}
        return cls(**params)

    def to_tuple(self, axis_order=None):
        axis_order = axis_order or self.LABELS
        return tuple((self._coords[label] for label in axis_order))

    def to_dict(self):
        return self._coords.copy()

    def to_np(self):
        return np.asarray(list(self._coords.values()))

    def __repr__(self):
        contents = ",".join((f"{label}:{val}" for label, val in self._coords.items()))
        return f"{self.__class__.__name__}({contents})"

    def __str__(self):
        return self.__repr__()

    @classmethod
    def zero(cls):
        return cls(**{label: 0 for label in cls.LABELS})

    @classmethod
    def one(cls):
        return cls(**{label: 1 for label in cls.LABELS})

    @classmethod
    def inf(cls):
        return cls(**{label: np.iinfo(np.uint64).max for label in cls.LABELS})

    def __getitem__(self, key):
        return self._coords[key]

    @property
    def t(self):
        return self._coords['t']

    @property
    def x(self):
        return self._coords['x']

    @property
    def y(self):
        return self._coords['y']

    @property
    def z(self):
        return self._coords['z']

    @property
    def c(self):
        return self._coords['c']

    def with_axis_as(self, label, value):
        params = self.to_dict()
        params[label] = value
        return self.__class__(**params)

    def __np_op(self, other, op):
        return getattr(self.to_np(), op)(other.to_np())

    def _compare(self, other, op):
        return all(self.__np_op(other, op))

    def __gt__(self, other):
        return self._compare(other, '__gt__')

    def __ge__(self, other):
        return self._compare(other, '__ge__')

    def __lt__(self, other):
        return self._compare(other, '__lt__')

    def __le__(self, other):
        return self._compare(other, '__le__')

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self._compare(other, '__eq__')

    def __ne__(self, other):
        return not self.__eq__(other)

    def __sub__(self, other):
        dif = self.to_np() - other.to_np()
        params = {label:value for label, value in zip(self.LABELS, dif)}
        return self.__class__(**params)

    def __add__(self, other):
        dif = self.to_np() + other.to_np()
        params = {label:value for label, value in zip(self.LABELS, dif)}
        return self.__class__(**params)

    def clamped(self, minimum:'Point5D'=None, maximum:'Point5D'=None):
        minimum = minimum or self.zero()
        maximum = maximum or self.inf()
        result = np.maximum(self.to_tuple(), minimum.to_tuple(), dtype=np.uint64)
        result = np.minimum(result, maximum.to_tuple(), dtype=np.uint64)
        return self.__class__(**{label:val for label, val in zip(self.LABELS, result)})

    def as_shape(self) -> 'Shape5D':
        return Shape5D(**self.to_dict)

class Shape5D(Point5D):
    def __init__(cls, *, t:int=1, x:int=1, y:int=1, z:int=1, c:int=1):
        assert t > 0 and x > 0 and y > 0 and z > 0 and c > 0
        super().__init__(t=t, x=x, y=y, z=z, c=c)

    def to_roi(self, begin:Point5D=None) -> 'Roi5D':
        return Roi5D(begin or Point5D.zero(), self)

    @classmethod
    def from_point(cls, point:Point5D):
        d = {k:v or 1 for k, v in point.to_dict().items()}
        return cls(**d)

class Roi5D(object):
    def __init__(self, inclusive_begin: Point5D, exclusive_end: Point5D=None):
        if exclusive_end is None:
            exclusive_end = Point5D.endpoint(**inclusive_begin.to_dict())
        assert exclusive_end > inclusive_begin, f"end: {exclusive_end}   begin {inclusive_begin}"
        self.begin = inclusive_begin
        self.end = exclusive_end

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.begin == other.begin and self.end == other.end

    def __ne__(self, other):
        return not self == other

    def ranges(self, block_shape:Shape5D) -> Iterator[Iterator[int]]:
        starts = self.begin.to_tuple()
        ends = self.end.to_tuple()
        steps = block_shape.to_tuple()
        return (range(s, e, stp) for s, e, stp in zip(starts, ends, steps))

    def split(self, block_shape:Shape5D) -> Iterator['Roi5D']:
        for begin_tuple in product(*self.ranges(block_shape)):
            begin = Point5D.from_tuple(begin_tuple)
            end = (begin + block_shape).clamped(maximum=self.end)
            yield Roi5D(begin, end)

    def axis_span(self, label):
        return self.end[label] - self.begin[label]

    @classmethod
    def cutout(cls, begin_tuple:Tuple[int, int, int, int, int], end_tuple:Tuple[int,int,int,int,int],
               image_shape:Shape5D):
        end = (v or image_shape[k] for k,v in zip(Point5D.LABELS, begin_tuple))
        return cls(Point5D.startpoint_from_tuple(begin_tuple), Point5D.from_tuple(end))

    @classmethod
    def all(cls):
        return cls(Point5D.zero(), Point5D.inf())

    @property
    def shape(self) -> Shape5D:
        d = (self.end - self.begin).to_dict()
        return Shape5D(**d)

    def clamped(self, minimum:Point5D=None, maximum:Point5D=None) -> 'Roi5D':
        return self.__class__(self.begin.clamped(minimum, maximum),
                              self.end.clamped(minimum, maximum))

    def clamped_with_roi(cls, roi):
        return cls.clamped(minimum=roi.begin, maximum=roi.end)

    def to_slices(self, axis_order=None):
        slices = []
        for begin_coord, end_coord in zip(self.begin.to_tuple(axis_order), self.end.to_tuple(axis_order)):
            begin_coord = begin_coord if begin_coord != float('-inf') else None
            end_coord = end_coord if end_coord != float('inf') else None
            slices.append(slice(begin_coord, end_coord))

        return tuple(slices)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return str([self.begin, self.end])

    def to_tuple(self, axis_order=None):
        return (self.begin.to_tuple(axis_order), self.end.to_tuple(axis_order))


test_dict = OrderedDict(zip('txyzc', [1,2,3,4,5]))
assert Point5D(**test_dict).to_tuple() == tuple(test_dict.values())
assert Point5D(**test_dict).to_dict() == test_dict

partialDict = {'t':0, 'x':12, 'y':13, 'z':14}
endpointFromDict = Point5D.endpoint(**partialDict, shape=Shape5D(c=1))
assert endpointFromDict.to_dict() == {**partialDict, **{'t': 1, 'c': 1}}

startpointFromDict = Point5D.startpoint(**partialDict)
assert startpointFromDict.to_dict() == {**partialDict, **{'c': 0}}


point = Point5D.startpoint(**partialDict)
fullRoi = Shape5D.from_point(point).to_roi()

assert Point5D.one().with_axis_as('t', 123).to_tuple() == (123,1,1,1,1)


t1c1z1x100y200 = Point5D(t=1, c=1, z=1, x=100, y=200)
fullRoix100y200 = Shape5D(**{'x': 100, 'y': 200}).to_roi()

al = Roi5D.all()

assert fullRoix100y200.end.to_tuple('yx') == (200, 100)
assert fullRoix100y200.shape.to_dict() == {'t': 1, 'x': 100, 'y': 200, 'z': 1, 'c': 1} 
