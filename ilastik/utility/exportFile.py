from __future__ import print_function
from builtins import range
import collections
import numpy as np
import numpy.lib.recfunctions as nlr
import h5py
from vigra import AxisTags
from lazyflow.utility import OrderedSignal
from sys import stdout
from zipfile import ZipFile
from ilastik.applets.objectExtraction.opObjectExtraction import default_features_key
import logging

logger = logging.getLogger(__name__)
try:
    from ilastik.plugins import pluginManager
except:
    logger.warning('could not import pluginManager')

class Default(object):
    DivisionNames = {"names": ("timestep", "object_id", "lineage_id", "track_id", "child1_object_id", "child1_track_id", "child2_object_id", "child2_track_id")}
    ManualDivMap = [1, 0, 1, 1, 1, 1, 1, 1]
    KnimeId = {"names": ("object_id",)}
    IlastikId = {"names": ("timestep", "labelimage_oid")}
    Lineage = {"names": ("lineage_id",)}
    TrackId = {"names": ("track_id",)}
    LabelRoiPath = "/images/{}/labeling"
    RawRoiPath = "/images/{}/raw"
    RawPath = "/images/raw"
    TrackColumnName = "track_id{}"
    TimeColumnName = "timestep"


def flatten_tracking_table(table, extra_table, obj_counts, max_tracks, t_range):
    #array = np.zeros(sum(obj_counts), ",".join(["i"] * max_tracks))
    #array.dtype.names = ["track%i" % i for i in xrange(1, max_tracks + 1)]
    array = np.zeros(sum(obj_counts), [(Default.TrackColumnName.format(i), "i") for i in range(1, max_tracks + 1)])
    row = 0
    for i, count in enumerate(obj_counts):
        for o in range(1, count + 1):
            track = []
            if t_range[0] <= i <= t_range[1]:
                if o in table[i]:
                    if hasattr(table[i][o], "__iter__"):
                        track.extend(table[i][o])
                    else:
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
    selection = list(selection)
    frames = table.meta.shape[0]

    logger.info('Fetching object features for feature table...')
    computed_feature = table([]).wait()

    signal(0)

    feature_long_names = [] # For example, "Size in Pixels"
    feature_short_names = [] # For example, "Count"
    feature_plugins = []
    feature_channels = []
    feature_types = []

    for plugin_name, feature_dict in computed_feature[0].items():
        all_props = None
        
        if plugin_name==default_features_key:
            plugin = pluginManager.getPluginByName("Standard Object Features", "ObjectFeatures")
        else:
            plugin = pluginManager.getPluginByName(plugin_name, "ObjectFeatures")
        if plugin:
            plugin_feature_names = {el:{} for el in list(feature_dict.keys())}
            all_props = plugin.plugin_object.fill_properties(plugin_feature_names) #fill in display name and such

        for feat_name, feat_array in feature_dict.items():
            if all_props:
                long_name = all_props[feat_name]["displaytext"]
            else:
                long_name = feat_name
            if (plugin_name == default_features_key or \
                     long_name in selection or \
                     feat_name in selection) and \
                     long_name not in feature_long_names:
                feature_long_names.append(long_name)
                feature_short_names.append(feat_name)
                feature_plugins.append(plugin_name)
                feature_channels.append((feat_array.shape[1]))
                feature_types.append(feat_array.dtype)

    signal(25)

    obj_count = []
    for t, cf in computed_feature.items():
        obj_count.append(cf[default_features_key]["Count"].shape[0] - 1)  # no background

    signal(50)

    dtype_names = []
    dtype_types = []
    dtype_to_key = {}

    for i, name in enumerate(feature_long_names):
        if feature_channels[i] > 1:
            for c in range(feature_channels[i]):
                dtype_names.append("%s_%i" % (name, c))
                dtype_types.append(feature_types[i].name)
                dtype_to_key[dtype_names[-1]] = (feature_plugins[i], feature_short_names[i], c)
        else:
            dtype_names.append(name)
            dtype_types.append(feature_types[i].name)
            dtype_to_key[dtype_names[-1]] = (feature_plugins[i], feature_short_names[i], 0)

    feature_table = np.zeros((sum(obj_count),), dtype=",".join(dtype_types))
    feature_table.dtype.names = list(map(str, dtype_names))

    signal(75)

    start = 0
    end = obj_count[0]
    for t, cf in computed_feature.items():
        for name in dtype_names:
            plugin, feat_name, index = dtype_to_key[name]
            data_len = len(cf[plugin][feat_name][1:, index])
            feature_table[name][start:start + data_len] = cf[plugin][feat_name][1:, index]
        start = end
        try:
            end += obj_count[int(t) + 1]
        except IndexError:
            end = sum(obj_count)

    signal(100)

    return feature_table


def objects_per_frame(label_image_slot):
    t_index = label_image_slot.meta.axistags.index("t")
    assert t_index == 0, "This function assumes that the first axis is time."    

    num_frames = label_image_slot.meta.shape[0]
    for t in range(num_frames):
        frame_data = label_image_slot[t:t+1].wait()
        yield frame_data.max()


def division_flatten_dict(divisions, dict_):
    list_ = []
    for t, o, _, _, _, _, _ in divisions:
        try:
            list_.append(dict_[t][o])
        except (IndexError, TypeError, KeyError):
            list_.append(0)
    return list_


def flatten_dict(dict_, object_count):
    list_ = [0] * sum(object_count)
    i = 0
    for t, count in enumerate(object_count):
        for o in range(1, count + 1):
            try:
                item = dict_[t][o]
            except (IndexError, TypeError, KeyError):
                item = 0
            list_[i] = item
            i += 1
    return list_


def prepare_list(list_, names, dtypes=None):
    """Handle lists for export

    Args:
        list_ (list): list of iterables, [(),(),...], will do automagic for
          list of strings [str, str, str]
        names (tuple,): Description
        dtypes (iterable, optional): iterable of dtypes, or something that can
          be understood as dtypes

    Returns:
        ndarray: data as numpy array with named dtypes. dtypes are derived from
          data if not given explicitly in optional `dtypes` argument

    """
    n_items = len(list_)

    # make sure inner items are iterables
    first_row = list_[0]
    if isinstance(first_row, str) or not isinstance(first_row, collections.Iterable):
        list_ = [(x,) for x in list_]
        first_row = list_[0]

    if dtypes is None:
        # generate a list of structured dtypes:
        dtypes = []
        for col, (item, col_name) in enumerate(zip(first_row, names)):
            item_dtype = np.dtype(type(item))
            col_dtype = (col_name, item_dtype)
            if item_dtype == np.str:
                maxlen = max(len(row_data[col]) for row_data in list_)
                col_dtype = (col_name, item_dtype, maxlen)
            dtypes.append(col_dtype)

    assert isinstance(dtypes, collections.Iterable)
    assert len(first_row) == len(dtypes)
    array = np.zeros((n_items,), dtype=dtypes)
    array[:] = list_
    return array


def ilastik_ids(obj_counts):
    for t, count in enumerate(obj_counts):
        for o in range(1, count + 1):
            yield (t, o)


def create_slicing(axistags, dimensions, margin, feature_table):
    """
    Returns an iterator on the slices for each object roi
        yields also the actual object id
    """
    assert margin >= 0, "Margin muss be greater than or equal to 0"
    time = feature_table[Default.TimeColumnName].astype(np.int32)
    minx = feature_table["Bounding Box Minimum_0"].astype(np.int32)
    maxx = feature_table["Bounding Box Maximum_0"].astype(np.int32)
    miny = feature_table["Bounding Box Minimum_1"].astype(np.int32)
    maxy = feature_table["Bounding Box Maximum_1"].astype(np.int32)
    table_shape = feature_table.shape[0]
    try:
        minz = feature_table["Bounding Box Minimum_2"].astype(np.int32)
        maxz = feature_table["Bounding Box Maximum_2"].astype(np.int32)
    except ValueError:
        minz = maxz = [0] * table_shape

    indices = list(map(axistags.index, "txyzc"))
    excludes = indices.count(-1)
    oid = 1
    for i in range(table_shape):
        if time[i] != time[i - 1]:
            oid = 1
        # noinspection PyTypeChecker
        slicing = [
            slice(time[i], time[i] + 1),
            slice(max(0, minx[i] - margin),
                  min(maxx[i] + margin, dimensions[1])),
            slice(max(0, miny[i] - margin),
                  min(maxy[i] + margin, dimensions[2])),
            slice(max(0, minz[i] - margin),
                  min(maxz[i] + margin, dimensions[3])),
            slice(None)
        ]
        yield [slicing[x] for x in indices][:5 - excludes], oid
        oid += 1


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

    def add_columns(self, table_name, col_data, mode, extra=None):
        """
        Adds new columns to the table ( creates the table if neccessary )
        :param table_name: the table name
        :type table_name: str
        :param col_data: the actual data to be added
        :type col_data: list, dict, numpy.array, whatever is supported
        :param mode: the type of the table data
        :type mode: exportFile.Mode
        :param extra: extra information for the given mode
        :type extra: dict
        """
        if extra is None:
            extra = {}
        if mode == Mode.IlastikTrackingTable:
            if not "counts" in extra or not "max" in extra:
                raise AttributeError("Tracking need 'counts', 'max' extra")
            columns = flatten_tracking_table(col_data, extra["extra ids"], extra["counts"], extra["max"],
                                             extra["range"])
        elif mode == Mode.List:
            if not "names" in extra:
                raise AttributeError("[Tuple]List needs a tuple for the column name (extra 'names')")
            dtypes = extra["dtypes"] if "dtypes" in extra else None
            columns = prepare_list(col_data, extra["names"], dtypes)
        elif mode == Mode.IlastikFeatureTable:
            if "selection" not in extra:
                raise AttributeError("IlastikFeatureTable needs a feature selection (extra 'selection')")
            columns = flatten_ilastik_feature_table(col_data, extra["selection"], self.InsertionProgress)
        elif mode == Mode.NumpyStructArray:
            columns = col_data
        else:
            raise AttributeError("Invalid Mode")
        self._add_columns(table_name, columns)

    def add_rois(self, table_path, image_slot, feature_table_name, margin, type_="image"):
        """
        Adds the rois as images to the table
        :param table_path: the new name for the table
        :type table_path: str
        :param image_slot: the slot to read the data from
        :type image_slot: lazyflow.slot.Slot
        :param feature_table_name: the already added feature table to read the coords from
        :type feature_table_name: str
        :param margin: the margin to be added around the images
        :type margin: int
        :param type_: "image" for normal images, "labeling" for labeling images
        :type type_: str
        """
        assert type_ in ("labeling", "image"), "Type must be 'labeling' or 'image'"
        slicings = create_slicing(image_slot.meta.axistags, image_slot.meta.shape,
                                  margin, self.table_dict[feature_table_name])
        self.InsertionProgress(0)

        if type_ == "labeling":
            vec = self._normalize
        else:
            vec = lambda _: lambda y: y
        for i, (slicing, oid) in enumerate(slicings):
            roi = image_slot(slicing).wait()
            roi = vec(oid)(roi)
            roi_path = table_path.format(i)
            self.meta_dict[roi_path] = {
                "type": type_,
                "axistags": actual_axistags(image_slot.meta.axistags, roi.shape).toJSON()
            }
            self.table_dict[roi_path] = roi.squeeze()
            self.InsertionProgress(100 * i / self.table_dict[feature_table_name].shape[0])
        self.InsertionProgress(100)

    @staticmethod
    def _normalize(oid):
        def f(pixel_value):
            return 1 if pixel_value == oid else 0

        return np.vectorize(f)

    def add_image(self, table, image_slot):
        """
        Adds an image as a table
        :param table: the name for the image
        :type table: str
        :param image_slot: the slot to read the image from
        :type image_slot: lazyflow.slot.Slot
        """
        self.table_dict[table] = image_slot([]).wait().squeeze()
        self.meta_dict[table] = {
            "type": "image",
            "axistags": actual_axistags(image_slot.meta.axistags, image_slot.meta.shape).toJSON()
        }

    def update_meta(self, table, meta):
        """
        Adds meta information to the table
        :param table: the table to add meta to
        :type table: str
        :param meta: the meta information to add
        :type meta: dict
        """
        self.meta_dict.setdefault(table, {})
        self.meta_dict[table].update(meta)

    def write_all(self, mode, compression=None):
        """
        Writes all tables to the file
        :param mode: "h[d[f]]5" or "csv" at the moment
        :type mode: str
        :param compression: the compression settings
        :type compression: dict
        """
        count = 0
        self.ExportProgress(0)
        if mode in ("h5", "hd5", "hdf5"):
            with h5py.File(self.file_name, "w") as fout:
                for table_name, table in self.table_dict.items():
                    self._make_h5_dataset(fout, table_name, table, self.meta_dict.get(table_name, {}),
                                          compression if compression is not None else {})
                    count += 1
                    self.ExportProgress(count * 100 / len(self.table_dict))
        elif mode == "csv":
            f_name = self.file_name.rsplit(".", 1)
            if len(f_name) == 1:
                base, ext = f_name, ""
            else:
                base, ext = f_name
            file_names = []
            for table_name, table in self.table_dict.items():
                file_names.append("{name}_{table}.{ext}".format(name=base, table=table_name, ext=ext))
                with open(file_names[-1], "w") as fout:
                    self._make_csv_table(fout, table)
                    count += 1
                    self.ExportProgress(count * 100 / len(self.table_dict))
            if False:
                with ZipFile("{name}.zip".format(name=base), "w") as zip_file:
                    for file_name in file_names:
                        zip_file.write(file_name)
        self.ExportProgress(100)
        logger.info("exported %i tables" % count)

    def _add_columns(self, table_name, columns):
        if table_name in iter(self.table_dict.keys()):
            old = self.table_dict[table_name]
            columns = nlr.merge_arrays((old, columns), flatten=True)

        self.table_dict[table_name] = columns

    @staticmethod
    def _make_h5_dataset(fout, table_name, table, meta, compression):

        sanitized_table = ExportFile._sanitize_table_for_hdf5_export(table)
        try:
            dset = fout.create_dataset(table_name, sanitized_table.shape, data=sanitized_table, **compression)
        except TypeError:
            dset = fout.create_dataset(table_name, sanitized_table.shape, data=sanitized_table)
        for k, v in meta.items():
            dset.attrs[k] = v

    @staticmethod
    def _sanitize_table_for_hdf5_export(table):
        # sanitize the dtypes, this makes a temporary copy of the table :/
        # but this is needed, unfortunately due to hdf5 not having unicode support
        names = table.dtype.names
        if names is None:
            return table
        hasstrings = [name for name in names if table[name].dtype.type == np.str_]
        if not hasstrings:
            return table
        table_copy = {name: table[name] for name in names}
        dtypes = {name: table_copy[name].dtype for name in names}
        for string_column in hasstrings:
            column = np.core.defchararray.encode(table[string_column], 'utf-8')
            dtypes[string_column] = column.dtype
            table_copy[string_column] = column

        return np.array(list(zip(*[table_copy[name] for name in names])), dtype=[(name, dtypes[name]) for name in names])


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
    def __init__(self, name, range_, max_=0):
        self.first = True
        self.range_ = range_
        self.steps = []
        self.name = name
        self.count = 1
        self.max_ = max_

    def __call__(self, p):
        if p == 0 and self.first:
            stdout.write("%s [%i%s]\n" % (self.name, self.count, ("/%i" % self.max_) if self.max_ > 0 else ""))
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
            stdout.write("\n")


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
    print(l)
    print(l2)
