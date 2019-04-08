# To change this license header, choose License Headers in Project Properties.
# To change this template file, choose Tools | Templates
# and open the template in the editor.

__author__ = "John Kirkham <kirkhamj@janelia.hhmi.org>"
__date__ = "$May 14, 2014 10:19:59 PM$"

import sys

if sys.version_info.major >= 3:
    unicode = str

import numpy
import h5py


def write_numpy_structured_array_to_HDF5(fid, internalPath, data, overwrite=False):
    """
        Serializes a NumPy structure array to an HDF5 file by creating a group that contains
        the individual keys as different array. Also, additional attributes are added to the
        group to store the shape and dtype of the NumPy structure array to allow for serialization
        out. Also, will handle normal NumPy arrays as well.

        Note:
            HDF5 does not support generic Python objects. So, serialization of objects to something
            else (perhaps strs of fixed size) must be performed first.

        Note:
            TODO: Write doctests.

        Args:
            fid(HDF5 file):         either an HDF5 file or an HDF5 filename.
            internalPath(str):      an internal path for the HDF5 file.
            data(numpy.ndarray):    the NumPy structure array to save (or normal NumPy array).
            overwrite(bool):        whether to overwrite what is already there.
    """

    close_fid = False

    if isinstance(fid, (str, unicode)):
        fid = h5py.File(fid, "a")
        close_fid = True

    dataset = None

    try:
        dataset = fid.create_dataset(internalPath, data.shape, data.dtype)
    except RuntimeError:
        if overwrite:
            del fid[internalPath]
            dataset = fid.create_dataset(internalPath, data.shape, data.dtype)
        else:
            raise

    dataset[:] = data

    if close_fid:
        fid.close()


def read_numpy_structured_array_from_HDF5(fid, internalPath):
    """
        Serializes a NumPy structure array from an HDF5 file by reading a group that contains
        all the arrays needed by the NumPy structure array. Also, additional attributes are
        added to the group to store the shape and dtype of the NumPy structure array to allow
        for serialization out. Also, it will handle normal NumPy arrays as well.

        Note:
            HDF5 does not support generic Python objects. So, serialization of objects to something
            else (perhaps strs of fixed size) must be performed first.

        Args:
            fid(HDF5 file):         either an HDF5 file or an HDF5 filename.

            internalPath(str):      an internal path for the HDF5 file.

        Note:
            TODO: Write doctests.

        Returns:
            data(numpy.ndarray):  the NumPy structure array.
    """

    close_fid = False

    if isinstance(fid, (str, unicode)):
        fid = h5py.File(fid, "r")
        close_fid = True

    data = fid[internalPath][:]

    if close_fid:
        fid.close()

    return data


# def write_numpy_structured_array_to_HDF5(fid, internalPath, data, overwrite = False):
#    """
#        Serializes a NumPy structure array to an HDF5 file by creating a group that contains
#        the individual keys as different array. Also, additional attributes are added to the
#        group to store the shape and dtype of the NumPy structure array to allow for serialization
#        out. Also, will handle normal NumPy arrays as well.
#
#        Note:
#            HDF5 does not support generic Python objects. So, serialization of objects to something
#            else (perhaps strs of fixed size) must be performed first.
#
#        Note:
#            TODO: Write doctests.
#
#        Args:
#            fid(HDF5 file):         either an HDF5 file or an HDF5 filename.
#            internalPath(str):      an internal path for the HDF5 file.
#            data(numpy.ndarray):    the NumPy structure array to save (or normal NumPy array).
#            overwrite(bool):        whether to overwrite what is already there.
#    """
#
#    close_fid = False
#
#    if isinstance(fid, (str, unicode)):
#        fid = h5py.File(fid, "a")
#        close_fid = True
#
#    if data.dtype.names is None:
#        fid[internalPath] = data
#    else:
#        try:
#            fid.create_group(internalPath)
#        except ValueError:
#            if overwrite:
#                del fid[internalPath]
#                #fid.create_group(internalPath)
#            else:
#                raise
#
#        fid[internalPath].attrs["shape"] = data.shape
#        fid[internalPath].attrs["dtype"] = data.dtype.descr
#
#        for each_name in data.dtype.names:
#            fid[internalPath][each_name] = data[each_name]
#
#    if close_fid:
#        fid.close()
#
#
#
# def read_numpy_structured_array_from_HDF5(fid, internalPath, use_attrs = True, ndim_global = 1):
#    """
#        Serializes a NumPy structure array from an HDF5 file by reading a group that contains
#        all the arrays needed by the NumPy structure array. Also, additional attributes are
#        added to the group to store the shape and dtype of the NumPy structure array to allow
#        for serialization out. Also, it will handle normal NumPy arrays as well.
#
#        Note:
#            HDF5 does not support generic Python objects. So, serialization of objects to something
#            else (perhaps strs of fixed size) must be performed first.
#
#        Args:
#            fid(HDF5 file):         either an HDF5 file or an HDF5 filename.
#
#            internalPath(str):      an internal path for the HDF5 file.
#
#            use_attrs(bool):        whether to use attributes stored on the group
#                                    to build the NumPy structure array. If not true,
#                                    it will determine the types based on the group's
#                                    contents and the ndim_global option.
#
#            ndim_global(int):       The number of dimensions to include as part of the
#                                    structure array. This will take dimensions from the
#                                    beginning of each array to do this. It also requires
#                                    that all the dimensions be the same (else assertion fail).
#
#        Note:
#            TODO: Write doctests.
#
#        Returns:
#            data(numpy.ndarray):  the NumPy structure array.
#    """
#
#    close_fid = False
#
#    if isinstance(fid, (str, unicode)):
#        fid = h5py.File(fid, "r")
#        close_fid = True
#
#    data = None
#
#    if type(fid[internalPath]) is h5py.Dataset:
#        data = fid[internalPath].copy()
#    else:
#        if use_attrs:
#            data_shape = fid[internalPath].attrs["shape"]
#            data_dtype = fid[internalPath].attrs["dtype"]
#
#            data_dtype = data_dtype.tolist()
#            data_dtype = [tuple(each) for each in data_dtype]
#        else:
#            data_shape = [None for _ in xrange(ndim_global)]
#            data_dtype = []
#
#            for each_key in fid[internalPath].keys():
#                each_shape = []
#                each_dtype = fid[internalPath][each_key].dtype
#
#                for each_global_axis in xrange(ndim_global):
#                    if data_shape[each_global_axis] is None:
#                        data_shape[each_global_axis] = fid[internalPath][each_key].shape[each_global_axis]
#                    else:
#                        assert(data_shape[each_global_axis] == fid[internalPath][each_key].shape[each_global_axis])
#
#                for each_local_axis in xrange(ndim_global, len(fid[internalPath][each_key].shape)):
#                    each_shape.append(fid[internalPath][each_key].shape[each_local_axis])
#
#
#                each_shape = tuple(each_shape)
#
#                each_key_ascii = unicodedata.normalize("NFKD", each_key).encode("ascii", "ignore")
#                each_rec_dtype = (each_key_ascii, each_dtype)
#
#                if each_shape:
#                    each_rec_dtype += (each_shape,)
#
#                data_dtype.append(each_rec_dtype)
#
#            data_shape = tuple(data_shape)
#            data_dtype = numpy.dtype(data_dtype)
#
#        data = numpy.zeros(data_shape, dtype = data_dtype)
#
#        for each_name in fid[internalPath].keys():
#            print
#            data[each_name] = fid[internalPath][each_name]
#
#    if close_fid:
#        fid.close()
#
#    return(data)
