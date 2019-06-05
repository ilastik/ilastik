from collections import OrderedDict
from itertools import product
import numpy as np
from typing import Dict, Tuple, Iterator, List

from ilastik.utility import JsonSerializable

INT = np.int64
FLOAT = np.float64

class Point5D(JsonSerializable):
    LABELS = 'txyzc'
    SPATIAL_LABELS = 'xyz'
    LABEL_MAP = {label:index for index, label in enumerate(LABELS)}
    DTYPE = np.float64
    INF = float('inf')
    NINF = -INF

    def __init__(self, *, t:float, x:float, y:float, z:float, c:float):
        assert all(v == float('inf') or int(v) == v for v in (t,c,x,y,z)), f"Point5D accepts only ints or 'inf' {(t,c,x,y,z)}"
        self._coords = {'t':self.DTYPE(t), 'c':self.DTYPE(c),
                        'x':self.DTYPE(x), 'y':self.DTYPE(y), 'z':self.DTYPE(z)}

    def __hash__(self):
        return hash(self.to_tuple(self.LABELS))

    @classmethod
    def from_tuple(cls, tup:Tuple[float,float,float,float,float], labels:str):
        return cls(**{label:value for label, value in zip(labels, tup)})

    @classmethod
    def from_np(cls, arr:np.ndarray, labels:str):
        return cls.from_tuple(tuple(arr), labels)

    def to_tuple(self, axis_order:str):
        return tuple(self._coords[label] for label in axis_order)

    def to_dict(self):
        return self._coords.copy()

    def to_np(self, axis_order:str=LABELS):
        return np.asarray(self.to_tuple(axis_order))

    def to_np_int(self, axis_order:str):
        return self.to_np(axis_order).astype(np.int64)

    def __repr__(self):
        contents = ",".join((f"{label}:{val}" for label, val in self._coords.items()))
        return f"{self.__class__.__name__}({contents})"

    @classmethod
    def inf(cls, *, t:float=INF, x:float=INF, y:float=INF, z:float=INF, c:float=INF):
        return cls(t=t, x=x, y=y, z=z, c=c)

    @classmethod
    def ninf(cls, *, t:float=NINF, x:float=NINF, y:float=NINF, z:float=NINF, c:float=NINF):
        return cls(t=t, x=x, y=y, z=z, c=c)

    @classmethod
    def zero(cls, *, t:float=0, x:float=0, y:float=0, z:float=0, c:float=0):
        return cls(t=t or 0, x=x or 0, y=y or 0, z=z or 0, c=c or 0)

    @classmethod
    def one(cls, *, t:float=1, x:float=1, y:float=1, z:float=1, c:float=1):
        return cls(t=t, x=x, y=y, z=z, c=c)

    def __getitem__(self, key):
        return self._coords[key]

    @property
    def t(self):
        return self['t']

    @property
    def x(self):
        return self['x']

    @property
    def y(self):
        return self['y']

    @property
    def z(self):
        return self['z']

    @property
    def c(self):
        return self['c']

    def with_coord(self, *, t=None, c=None, x=None, y=None, z=None):
        params = self.to_dict()
        params['t'] = t if t is not None else params['t']
        params['c'] = c if c is not None else params['c']
        params['x'] = x if x is not None else params['x']
        params['y'] = y if y is not None else params['y']
        params['z'] = z if z is not None else params['z']
        return self.__class__(**params)

    def __np_op(self, other, op):
        other = other.to_np(self.LABELS) if hasattr(other, 'to_np') else other
        raw = getattr(self.to_np(self.LABELS), op)(other)
        return Point5D.from_np(raw, self.LABELS)

    def _compare(self, other, op):
        return all(self.__np_op(other, op).to_tuple(self.LABELS))

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
        return self.__np_op(other, '__sub__')

    def __neg__(self):
        raw = self.to_np(self.LABELS)
        return Point5D.from_np(-raw, self.LABELS)

    def __mod__(self, other):
        return self.__np_op(other, '__mod__')

    def __add__(self, other):
        return self.__np_op(other, '__add__')

    def __floordiv__(self, other):
        return self.__np_op(other, '__floordiv__')

    def __truediv__(self, other):
        return self.__np_op(other, '__truediv__')

    def __mul__(self, other):
        return self.__np_op(other, '__mul__')

    def clamped(self, minimum:'Point5D'=None, maximum:'Point5D'=None):
        minimum = minimum or self.zero()
        maximum = maximum or self.inf()
        result = np.maximum(self.to_np(self.LABELS), minimum.to_np(self.LABELS))
        result = np.minimum(result, maximum.to_np(self.LABELS))
        return self.__class__(**{label:val for label, val in zip(self.LABELS, result)})

    def as_shape(self) -> 'Shape5D':
        return Shape5D(**self.to_dict)

    @classmethod
    def as_ceil(cls, arr:np.ndarray):
        raw = np.ceil(arr).astype(cls.DTYPE)
        return Point5D.from_np(raw, cls.LABELS)

    def ceiling(self):
        raw = np.ceil(self.to_np(self.LABELS)).astype(np.float32)
        return self.from_np(raw, self.LABELS)

class Shape5D(Point5D):
    DTYPE = np.uint64
    def __init__(cls, *, t:int=1, x:int=1, y:int=1, z:int=1, c:int=1):
        super().__init__(t=t, x=x, y=y, z=z, c=c)

    def __repr__(self):
        contents = ",".join((f"{label}:{val}" for label, val in self._coords.items() if val != 1))
        return f"{self.__class__.__name__}({contents})"

    def to_tuple(self, axis_order:str):
        return tuple(int(v) for v in super().to_tuple(axis_order))

    @property
    def spatial_axes(self):
        return {k:self._coords[k] for k in self.SPATIAL_LABELS}

    @property
    def missing_spatial_axes(self):
        return {k:v for k,v in self.spatial_axes.items() if v == 1}

    @property
    def present_spatial_axes(self) -> Dict[str, float]:
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

    @property
    def is_line(self):
        return len(self.present_spatial_axes) <= 1

    @property
    def is_scalar(self):
        return self.c == 1

    @property
    def volume(self) -> int:
        return self.x * self.y * self.z

    def to_slice_5d(self, offset:Point5D=Point5D.zero()) -> 'Slice5D':
        return Slice5D.create_from_start_stop(offset, self + offset)

    @classmethod
    def from_point(cls, point:Point5D):
        return cls(**{k:v or 1 for k, v in point.to_dict().items()})

class Slice5D(JsonSerializable):
    """A labeled 5D slice"""

    DTYPE = np.int64

    @classmethod
    def ensure_slice(cls, slc):
        if isinstance(slc, slice):
            return slc
        i = int(slc)
        return slice(i, i+1)

    def __init__(self, *, t=slice(None), c=slice(None), x=slice(None), y=slice(None), z=slice(None)):
        self._slices = {'t':self.ensure_slice(t), 'c':self.ensure_slice(c),
                        'x':self.ensure_slice(x), 'y':self.ensure_slice(y), 'z':self.ensure_slice(z)}

        self.start = Point5D.zero(**{label:slc.start for label, slc in self._slices.items()})
        self.stop = Point5D.inf(**{label:Point5D.INF if slc.stop is None else slc.stop
                                   for label, slc in self._slices.items()})

    def __eq__(self, other):
        if not isinstance(other, Slice5D):
            return False
        return self._slices == other._slices

    def rebuild(self, *, t=slice(None), c=slice(None), x=slice(None), y=slice(None), z=slice(None)):
        return self.__class__(t=t, c=c, x=x, y=y, z=z)

    def __hash__(self):
        return hash((self.start, self.stop))

    def contains(self, other:'Slice5D'):
        assert other.is_defined()
        return self.start <= other.start and self.stop >= other.stop

    def is_defined(self) -> bool:
        return all(slc.stop is not None for slc in self._slices.values())

    def defined_with(self, shape:Shape5D) -> 'Slice5D':
        """Slice5D can have slices which are open to interpretation, like slice(None). This method
        forces those slices expand into their interpretation within an array of shape 'shape'"""
        params = {}
        for key, slc in self._slices.items():
            start = slc.start or 0
            stop = shape[key] if slc.stop is None else slc.stop
            params[key] = slice(start, stop)
        return self.rebuild(**params)

    def to_dict(self):
        return self._slices.copy()

    @staticmethod
    def all() -> 'Slice5D':
        #FIXME: halo stuff might need negative indices and "all" starts at 0, messing up the meaning of "clamp"
        return Slice5D()

    @classmethod
    def make_slices(cls, start:Point5D, stop:Point5D):
        slices = {}
        for label in Point5D.LABELS:
            slice_stop = stop[label]
            slice_stop = None if slice_stop == Point5D.INF else slice_stop
            slices[label] = slice(start[label], slice_stop)
        return slices

    @classmethod
    def create_from_start_stop(cls, start:Point5D, stop:Point5D):
        return cls(**cls.make_slices(start, stop))

    @classmethod
    def from_json_data(cls, data:dict):
        start = Point5D.from_json(data['start'])
        stop = Point5D.from_json(data['stop'])
        return cls.create_from_start_stop(start, stop)

    @property
    def json_data(self):
        return {'start': self.start.json_data, 'stop': self.stop.json_data}

    def from_start_stop(self, start:Point5D, stop:Point5D):
        slices = self.make_slices(start, stop)
        return self.rebuild(**slices)

    def _ranges(self, block_shape:Shape5D) -> Iterator[Iterator[int]]:
        starts = self.start.to_np_int(Point5D.LABELS)
        ends = self.stop.to_np_int(Point5D.LABELS)
        steps = block_shape.to_np_int(Point5D.LABELS)
        return (range(s, e, stp) for s, e, stp in zip(starts, ends, steps))

    def split(self, block_shape:Shape5D) -> Iterator['Slice5D']:
        for begin_tuple in product(*self._ranges(block_shape)):
            start = Point5D.from_tuple(begin_tuple, Point5D.LABELS)
            stop = (start + block_shape).clamped(maximum=self.stop)
            yield self.from_start_stop(start, stop)

    def get_tiles(self, tile_shape:Shape5D) -> Iterator['Slice5D']:
        assert self.is_defined()
        start = (self.start // tile_shape) * tile_shape
        stop = Point5D.as_ceil(self.stop.to_np() / tile_shape.to_np()) * tile_shape
        return self.from_start_stop(start, stop).split(tile_shape)

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
        return self.rebuild(**params)

    def with_full_c(self) -> 'Shape5D':
        return self.with_coord(c=slice(None))

    def iter_over(self, axis:str, step:int=1) -> Iterator['Slice5D']:
        assert self.stop[axis] != Point5D.INF
        assert self.shape[axis] % step == 0
        for axis_value in range(int(self.start[axis]), int(self.stop[axis]), step):
            params = self.with_coord(**{axis:slice(axis_value, axis_value + step)}).to_dict()
            yield self.rebuild(**params)

    def frames(self) -> Iterator['Slice5D']:
        return self.iter_over('t')

    def planes(self, key='z') -> Iterator['Slice5D']:
        return self.iter_over(key)

    def channels(self) -> Iterator['Slice5D']:
        return self.iter_over('c')

    def channel_stacks(self, step) -> Iterator['Slice5D']:
        return self.iter_over('c', step=step)

    def images(self, through_axis='z') -> Iterator['Slice5D']:
        for frame in self.frames():
            for plane in frame.planes(through_axis):
                yield plane

    @property
    def shape(self) -> Shape5D:
        assert self.is_defined()
        return Shape5D(**(self.stop - self.start).to_dict())

    def clamped(self, slc:'Slice5D'):
        return self.from_start_stop(self.start.clamped(slc.start, slc.stop),
                                    self.stop.clamped(slc.start, slc.stop))

    def mod_tile(self, tile_shape:Shape5D):
        assert self.is_defined()
        assert self.shape <= tile_shape
        offset = self.start - (self.start % tile_shape)
        return self.from_start_stop(self.start - offset, self.stop - offset)

    def enlarged(self, radius:Point5D):
        start = self.start - radius
        stop = self.stop + radius
        return self.from_start_stop(start, stop)

    def translated(self, offset:Point5D):
        return self.from_start_stop(self.start + offset, self.stop + offset)

    def to_slices(self, axis_order:str=Point5D.LABELS):
        slices = []
        for axis in axis_order:
            slc = self._slices[axis]
            start = slc.start if slc.start is None else self.DTYPE(slc.start)
            stop = slc.stop if slc.stop is None else self.DTYPE(slc.stop)
            slices.append(slice(start, stop))
        return tuple(slices)

    def to_tuple(self, axis_order:str):
        assert self.is_defined()
        return (self.start.to_np_int(axis_order), self.stop.to_np_int(axis_order))

    def __repr__(self):
        assert all(int(v.start) == v.start and int(v.stop) == v.stop for v in self._slices.values() if v != slice(None))
        return ','.join(f"{k}:{int(slc.start)}_{int(slc.stop)}" for k, slc in self._slices.items() if slc != slice(None))
