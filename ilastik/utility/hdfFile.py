import numpy as np
import numpy.lib.recfunctions as nlr
import h5py


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


def flatten_ilastik_feature_table(table, selection):
    frames = table.meta.shape[0]

    if frames > 1:
        computed_feature = {}
        for t in xrange(frames - 1):
            request = table([t, t+1])
            computed_feature.update(request.wait())
            print "%i " % (100 * t / frames)
    else:
        computed_feature = table([]).wait()

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


def prepare_list(list_, names, dtypes):
    array = np.array(list_)
    try:
        shape1 = len(list_[0])
    except TypeError:
        shape1 = 1
    new_dtype = np.dtype(map(lambda i: (names[i], array.dtype if dtypes is None else dtypes[i]),
                             xrange(shape1)))
    array.dtype = new_dtype
    return array


def ilastik_id(obj_counts):
    for t, count in enumerate(obj_counts):
        for o in xrange(1, count+1):
            yield (t, o)


class TableType(object):
    IlastikTrackingTable = 1
    IlastikFeatureTable = 2
    List = 3
    NumpyStructArray = 4


class HdfFile(object):
    def __init__(self, file_name, compression=None):
        self.file_name = file_name
        self.table_dict = {}
        self.compression = compression

    def add_table(self, table_name, table_type, table, extra):
        if table_type == TableType.IlastikTrackingTable:
            if not "counts" in extra or not "max" in extra:
                raise AttributeError("Tracking need 'counts' and 'max' extra")
            columns = flatten_tracking_tablet(table, extra["extra ids"], extra["counts"], extra["max"])
        elif table_type == TableType.List:
            if not "names" in extra:
                raise AttributeError("[Tuple]List needs a tuple for the column name (extra 'names')")
            dtypes = extra["dtypes"] if "dtypes" in extra else None
            columns = prepare_list(table, extra["names"], dtypes)
        elif table_type == TableType.IlastikFeatureTable:
            if "selection" not in extra:
                raise AttributeError("IlastikFeatureTable needs a feature selection (extra 'selection')")
            columns = flatten_ilastik_feature_table(table, extra["selection"])
        elif table_type == TableType.NumpyStructArray:
            columns = table
        else:
            raise AttributeError("TableType not found")
        self._add_columns(table_name, columns)

    def write_all(self):
        count = 0
        with h5py.File(self.file_name, "w") as fout:
            for table_name, table in self.table_dict.iteritems():
                self._make_dataset(fout, table_name, table)
                count += 1
        print "exported %i tables" % count

    def _add_columns(self, table_name, columns):
        if table_name in self.table_dict.iterkeys():
            old = self.table_dict[table_name]
            columns = nlr.merge_arrays((old, columns), flatten=True)

        self.table_dict[table_name] = columns

    def _make_dataset(self, fout, table_name, table):
        meta = {}
        try:
            dset = fout.create_dataset(table_name, table.shape, data=table, **self.compression)
        except TypeError:
            dset = fout.create_dataset(table_name, table.shape, data=table)
        for k, v in meta.iteritems():
            dset.attrs[k] = v