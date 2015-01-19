import numpy as np
import numpy.lib.recfunctions as nlr
import h5py
from vigra import AxisTags
from lazyflow.utility import OrderedSignal
from sys import stdout


def flatten_tracking_tablet(table, extra_table, obj_counts, max_tracks):
    array = np.zeros(sum(obj_counts), ",".join(["i"] * max_tracks))
    array.dtype.names = ["track%i" % i for i in xrange(1, max_tracks+1)]
    row = 0
    for i, count in enumerate(obj_counts):
        for o in xrange(1, count + 1):
            track = []
            if o in table[i]:
                track.append(table[i][o])
                if i in extra_table and o in extra_table[i]:
                    track.extend(extra_table[i][o])
            track = list(set(track))
            while len(track) < max_tracks:
                track.append(0)
            array[row] = tuple(track)
            row += 1
    return array


def flatten_ilastik_feature_table(table, selection, signal):
    frames = table.meta.shape[0]

    signal(0)
    if frames > 1:
        computed_feature = {}
        for t in xrange(frames - 1):
            request = table([t, t+1])
            computed_feature.update(request.wait())
            signal(100*t/frames)
    else:
        computed_feature = table([]).wait()
    signal(100)

    print "features ready"

    feature_names = []
    feature_cats = []
    feature_channels = []
    feature_types = []

    for cat_name, category in computed_feature[0].iteritems():
        for feat_name, feat_array in category.iteritems():
            if cat_name == "Default features" or \
                    feat_name not in feature_names and \
                    feat_name in selection:
                feature_names.append(feat_name)
                feature_cats.append(cat_name)
                feature_channels.append((feat_array.shape[1]))
                feature_types.append(feat_array.dtype)

    obj_count = []
    for t, cf in computed_feature.iteritems():
        obj_count.append(cf["Default features"]["Count"].shape[0] - 1)  # no background

    dtype_names = []
    dtype_types = []
    dtype_to_key = {}

    for i, name in enumerate(feature_names):
        if feature_channels[i] > 1:
            for c in xrange(feature_channels[i]):
                dtype_names.append("%s_%i" % (name, c))
                dtype_types.append(feature_types[i].name)
                dtype_to_key[dtype_names[-1]] = (feature_cats[i], name, c)
        else:
            dtype_names.append(name)
            dtype_types.append(feature_types[i].name)
            dtype_to_key[dtype_names[i]] = (feature_cats[i], name, 0)

    feature_table = np.zeros((sum(obj_count),), dtype=",".join(dtype_types))
    feature_table.dtype.names = map(str, dtype_names)

    start = 0
    end = obj_count[0]
    for t, cf in computed_feature.iteritems():
        for name in dtype_names:
            cat, feat_name, index = dtype_to_key[name]
            feature_table[name][start:end] = cf[cat][feat_name][1:, index]
        start = end
        try:
            end += obj_count[int(t) + 1]
        except IndexError:
            end = sum(obj_count)

    return feature_table


def objects_per_frame(labeling_image):
    t_index = labeling_image.meta.axistags.index("t")
    data = labeling_image([]).wait()
    frames = data.shape[t_index]

    if t_index != 0:
        raise RuntimeError("FAIL")

    for t in xrange(frames):
        yield data[t].max()


def prepare_list(list_, names, dtypes=None):
    shape = (len(list_),)
    if dtypes is None:
        if isinstance(list_[0], (tuple, list)):
            dtypes = [np.dtype(type(i)).name for i in list_[0]]
        else:
            dtypes = [np.dtype(type(list_[0])).name]
    array = np.zeros(shape, ",".join(dtypes))
    array.dtype = np.dtype([(names[i], dtypes[i]) for i in xrange(len(names))])

    for i, row in enumerate(list_):
        if len(names) == 1:
            array[i] = (row, )
        else:
            array[i] = row

    return array


def ilastik_ids(obj_counts):
    for t, count in enumerate(obj_counts):
        for o in xrange(1, count+1):
            yield (t, o)


def create_slicing(axistags, dimensions, margin, feature_table):
    """
    Returns an iterator on the slices for each object roi
    """
    assert margin >= 0, "Margin muss be greater than or equal to 0"
    time = feature_table["time"].astype(np.int32)
    minx = feature_table["Coord<Minimum>_0"].astype(np.int32)
    maxx = feature_table["Coord<Maximum>_0"].astype(np.int32)
    miny = feature_table["Coord<Minimum>_1"].astype(np.int32)
    maxy = feature_table["Coord<Maximum>_1"].astype(np.int32)
    table_shape = feature_table.shape[0]
    try:
        minz = feature_table["Coord<Minimum>_2"].astype(np.int32)
        maxz = feature_table["Coord<Maximum>_2"].astype(np.int32)
    except ValueError:
        minz = maxz = [0] * table_shape

    indices = map(axistags.index, "txyzc")
    excludes = indices.count(-1)
    for i in xrange(table_shape):

        slicing = [
            slice(time[i], time[i]+1),
            slice(max(0, minx[i] - margin),
                  min(maxx[i] + margin, dimensions[1])),
            slice(max(0, miny[i] - margin),
                  min(maxy[i] + margin, dimensions[2])),
            slice(max(0, minz[i] - margin),
                  min(maxz[i] + margin, dimensions[3])),
            slice(0, 1)
        ]
        yield map(slicing.__getitem__, indices)[:5-excludes]


def actual_axistags(axistags, shape):
    return AxisTags([axistags[j] for j, s in enumerate(shape) if s > 1])


class Mode(object):
    IlastikTrackingTable = 1
    IlastikFeatureTable = 2
    List = 3
    NumpyStructArray = 4


class ExportFile(object):
    ExportProgress = OrderedSignal()
    InsertionProgress = OrderedSignal()

    def __init__(self, file_name):
        self.file_name = file_name
        self.table_dict = {}
        self.meta_dict = {}

    def add_columns(self, table_name, mode, col_type, extra=None):
        if extra is None:
            extra = {}
        if col_type == Mode.IlastikTrackingTable:
            if not "counts" in extra or not "max" in extra:
                raise AttributeError("Tracking need 'counts' and 'max' extra")
            columns = flatten_tracking_tablet(mode, extra["extra ids"], extra["counts"], extra["max"])
        elif col_type == Mode.List:
            if not "names" in extra:
                raise AttributeError("[Tuple]List needs a tuple for the column name (extra 'names')")
            dtypes = extra["dtypes"] if "dtypes" in extra else None
            columns = prepare_list(mode, extra["names"], dtypes)
        elif col_type == Mode.IlastikFeatureTable:
            if "selection" not in extra:
                raise AttributeError("IlastikFeatureTable needs a feature selection (extra 'selection')")
            columns = flatten_ilastik_feature_table(mode, extra["selection"], self.InsertionProgress)
        elif col_type == Mode.NumpyStructArray:
            columns = mode
        else:
            raise AttributeError("Invalid Mode")
        self._add_columns(table_name, columns)

    def add_rois(self, table_path, image_slot, feature_table_name, margin, type_="image"):
        slicings = create_slicing(image_slot.meta.axistags, image_slot.meta.shape,
                                  margin, self.table_dict[feature_table_name])
        self.InsertionProgress(0)
        for i, slicing in enumerate(slicings):
            roi = image_slot(slicing).wait().squeeze()
            roi_path = table_path.format(i)
            self.table_dict[roi_path] = roi
            self.meta_dict[roi_path] = {
                "type": type_,
                "axistags": actual_axistags(image_slot.meta.axistags, roi.shape).toJSON()
            }
            self.InsertionProgress(100 * i / self.table_dict[feature_table_name].shape[0])
        self.InsertionProgress(100)

    def add_image(self, table, image_slot, type_="image"):
        self.table_dict[table] = image_slot([]).wait().squeeze()
        self.meta_dict[table] = {
            "type": type_,
            "axistags": actual_axistags(image_slot.meta.axistags, image_slot.meta.shape).toJSON()
        }

    def update_meta(self, table, meta):
        self.meta_dict.setdefault(table, {})
        self.meta_dict[table].update(meta)

    def write_all(self, mode, compression=None):
        count = 0
        self.ExportProgress(0)
        if mode in ("h5", "hd5", "hdf5"):
            with h5py.File(self.file_name, "w") as fout:
                for table_name, table in self.table_dict.iteritems():
                    self._make_h5_dataset(fout, table_name, table,
                                          compression if compression is not None else {})
                    count += 1
                    self.ExportProgress(count * 100 / len(self.table_dict))
        elif mode == "csv":
            f_name = self.file_name.rsplit(".", 1)
            if len(f_name) == 1:
                base, ext = f_name, ""
            else:
                base, ext = f_name
            for table_name, table in self.table_dict.iteritems():
                with open("%s_%s.%s" % (base, table_name, ext), "w") as fout:
                    self._make_csv_table(fout, table)
                    count += 1
                    self.ExportProgress(count * 100 / len(self.table_dict))
        self.ExportProgress(100)
        print "exported %i tables" % count

    def _add_columns(self, table_name, columns):
        if table_name in self.table_dict.iterkeys():
            old = self.table_dict[table_name]
            columns = nlr.merge_arrays((old, columns), flatten=True)

        self.table_dict[table_name] = columns

    @staticmethod
    def _make_h5_dataset(fout, table_name, table, compression):
        meta = {}
        try:
            dset = fout.create_dataset(table_name, table.shape, data=table, **compression)
        except TypeError:
            dset = fout.create_dataset(table_name, table.shape, data=table)
        for k, v in meta.iteritems():
            dset.attrs[k] = v

    @staticmethod
    def _make_csv_table(fout, table):
        line = ",".join(table.dtype.names)
        fout.write(line)
        fout.write("\n")
        for row in table:
            line = ",".join(map(str, row))
            fout.write(line)
            fout.write("\n")


class ProgressPrinter(object):
    def __init__(self, name, range_):
        self.first = True
        self.range_ = range_
        self.steps = []
        self.name = name
        self.count = 1

    def __call__(self, p):
        if p == 0 and self.first:
            stdout.write("%s [%i]\n" % (self.name, self.count))
            self.steps = list(self.range_)
            self.count += 1
            self.first = False
        p = int(p)
        if len(self.steps) > 0 and p >= self.steps[-1]:
            stdout.write("%i " % self.steps.pop())
            stdout.flush()
            self.__call__(p)
        if p == 100 and not self.first:
            self.first = True
            stdout.write("\n%s finished\n" % self.name)


if __name__ == "__main__":
    l = [
        1, 2, 3, 4
    ]
    l2 = [
        (1, 2),
        (3, 4),
        (5, 6),
        (7, 8),
    ]

    l = prepare_list(l, ("a",))
    l2 = prepare_list(l2, ("a", "b"))
    print l
    print l2
