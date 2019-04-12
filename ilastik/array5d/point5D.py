from collections import OrderedDict
from itertools import product
import numpy as np
from typing import Dict, Tuple, Iterator

def ensure_slice(slc):
    if isinstance(slc, slice):
        return slc
    i = int(slc)
    return slice(i, i+1)

class Point5D(object):
    LABELS = 'txyzc'
    LABEL_MAP = {label:index for index, label in enumerate(LABELS)}
    INT_TYPE = np.uint64
    INF = np.iinfo(INT_TYPE).max #maybe this should be float's inf

    def __init__(self, *, t:int, x:int, y:int, z:int, c:int):
        locs = locals()
        ordered_pairs = ((label, self.INT_TYPE(locs[label])) for label in self.LABELS)
        self._coords = OrderedDict(ordered_pairs)

    @classmethod
    def startpoint(cls, *, t:int=0, x:int=0, y:int=0, z:int=0, c:int=0):
        return cls(t=t or 0, x=x or 0, y=y or 0, z=z or 0, c=c or 0)

    @classmethod
    def endpoint(cls, *, t:int=None, x:int=None, y:int=None, z:int=None, c:int=None):
        inf = Point5D.INF
        return cls(t=t or inf, x=x or inf, y=y or inf, z=z or inf, c=c or inf)

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

    def to_tuple(self, axis_order:str):
        assert sorted(axis_order) == sorted(self.LABELS)
        return tuple((self._coords[label] for label in axis_order))

    def to_dict(self):
        return self._coords.copy()

    def to_np(self, axis_order:str):
        return np.asarray(self.to_tuple(axis_order))

    def __repr__(self):
        contents = ",".join((f"{label}:{val if val != self.INF else 'inf'}" for label, val in self._coords.items()))
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

    def with_coord(self, *, t=None, c=None, x=None, y=None, z=None):
        params = self.to_dict()
        params['t'] = t if t is not None else params['t']
        params['c'] = c if c is not None else params['c']
        params['x'] = x if x is not None else params['x']
        params['y'] = y if y is not None else params['y']
        params['z'] = z if z is not None else params['z']
        return self.__class__(**params)

    def __np_op(self, other, op):
        return getattr(self.to_np(self.LABELS), op)(other.to_np(self.LABELS))

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
        dif = self.to_np(self.LABELS) - other.to_np(self.LABELS)
        params = {label:value for label, value in zip(self.LABELS, dif)}
        return self.__class__(**params)

    def __add__(self, other):
        dif = self.to_np(self.LABELS) + other.to_np(self.LABELS)
        params = {label:value for label, value in zip(self.LABELS, dif)}
        return self.__class__(**params)

    def clamped(self, minimum:'Point5D'=None, maximum:'Point5D'=None):
        minimum = minimum or self.zero()
        maximum = maximum or self.inf()
        result = np.maximum(self.to_tuple(self.LABELS), minimum.to_tuple(self.LABELS), dtype=np.uint64)
        result = np.minimum(result, maximum.to_tuple(self.LABELS), dtype=np.uint64)
        return self.__class__(**{label:val for label, val in zip(self.LABELS, result)})

    def as_shape(self) -> 'Shape5D':
        return Shape5D(**self.to_dict)

class Shape5D(Point5D):
    def __init__(cls, *, t:int=1, x:int=1, y:int=1, z:int=1, c:int=1):
        assert t > 0 and x > 0 and y > 0 and z > 0 and c > 0
        super().__init__(t=t, x=x, y=y, z=z, c=c)

    @property
    def spatial_axes(self):
        return {k:v for k,v in self._coords.items() if k in 'xyz'}

    @property
    def missing_spatial_axes(self):
        return {k:v for k,v in self.spatial_axes.items() if v == 1}

    @property
    def present_spatial_axes(self) -> int:
        return {k:v for k,v in self.spatial_axes.items() if k not in self.missing_spatial_axes}

    @property
    def is_static(self):
        return self.t == 1

    @property
    def is_volume(self):
        return len(self.present_spatial_axes) <= 3

    @property
    def is_flat(self):
        return len(self.present_spatial_axes) <= 2

    def is_line(self):
        return len(self.present_spatialaxes) <= 1

    @property
    def is_scalar(self):
        return self.c == 1

    def to_slice_5d(self, start:Point5D=None) -> 'Slice5D':
        return Slice5D.from_start_stop(start or Point5D.zero(), self)

    @classmethod
    def from_point(cls, point:Point5D):
        d = {k:v or 1 for k, v in point.to_dict().items()}
        return cls(**d)

    def _ranges(self, *, block_shape:'Shape5D', start_point:Point5D=None) -> Iterator[Iterator[int]]:
        start_point = start_point or Point5D.zero()

        starts = start_point.to_tuple()
        ends = self.to_tuple()
        steps = block_shape.to_tuple()
        return (range(s, e, stp) for s, e, stp in zip(starts, ends, steps))

    def split(self, block_shape:'Shape5D') -> Iterator['Roi5D']:
        for begin_tuple in product(*self._ranges(block_shape)):
            start = Point5D.from_tuple(begin_tuple)
            stop = (start + block_shape).clamped(maximum=elf.stop)
            yield Slice5D.from_start_stop(start, stop)

class Slice5D(object):
    def __init__(self, *, t=slice(None), c=slice(None), x=slice(None), y=slice(None), z=slice(None)):
        self._slices = {'t':ensure_slice(t),
                        'x':ensure_slice(x), 'y':ensure_slice(y), 'z':ensure_slice(z),
                        'c':ensure_slice(c)}

        self.start = Point5D.startpoint(**{label:slc.start for label, slc in self._slices.items()})
        self.stop = Point5D.endpoint(**{label:slc.stop for label, slc in self._slices.items()})

    @classmethod
    def from_start_stop(cls, start:Point5D, stop:Point5D):
        slices = {}
        for label in Point5D.LABELS:
            slice_stop = stop[label]
            slice_stop = None if slice_stop == Point5D.INF else slice_stop
            slices[label] = slice(start[label], slice_stop)
        return cls(**slices)

    @property
    def t(self):
        return self._slices['t']

    @property
    def c(self):
        return self._slices['c']

    @property
    def x(self):
        return self._slices['x']

    @property
    def y(self):
        return self._slices['y']

    @property
    def z(self):
        return self._slices['z']

    def with_coord(self, *, t=None, c=None, x=None, y=None, z=None):
        params = {}
        params['t'] = t or self.t
        params['c'] = c or self.c
        params['x'] = x or self.x
        params['y'] = y or self.y
        params['z'] = z or self.z
        return self.__class__(**params)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.start == other.start and self.stop == other.stop

    def __ne__(self, other):
        return not self == other

    def axis_span(self, label):
        return self.stop[label] - self.start[label]

    @classmethod
    def all(cls):
        return cls.from_start_stop(Point5D.zero(), Point5D.inf())

    @property
    def shape(self) -> Shape5D:
        return Shape5D(**(self.stop - self.start).to_dict())

    def clamped(self, *, minimum:Point5D=None, maximum:Point5D=None) -> 'Roi5D':
        return self.__class__(self.start.clamped(minimum, maximum),
                              self.stop.clamped(minimum, maximum))

    def clamped_with_roi(self, roi):
        return self.clamped(minimum=roi.start, maximum=roi.stop)

    def offset(self, offset:Point5D):
        return self.__class__.from_start_stop(self.start + offset, self.stop + offset)

    def to_slices(self, axis_order=Point5D.LABELS):
        return tuple([self._slices[label] for label in axis_order])

    def to_tuple(self, axis_order:str, bounding_shape:Shape5D):
        return (self.start.to_tuple(axis_order),
                self.stop.clamped(maximum=bounding_shape).to_tuple(axis_order))

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return str([self.start, self.stop])

class Slice2D(Slice5D):
    def __init__(self, *, x=slice(None), y=slice(None)):
        super().__init__(x=x, y=y)

    def to_tuple(self, axis_order:str, bounding_shape:Shape5D):
        assert sorted(axis_order) == sorted('xy')
        start = [self.start[label] for label in axis_order]
        stop = [self.stop.clamped(maximum=bounding_shape)[label] for label in axis_order]
        return (start, stop)
