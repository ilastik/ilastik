from builtins import object

###############################################################################
#   lazyflow: data flow based lazy parallel computation framework
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the Lesser GNU General Public License
# as published by the Free Software Foundation; either version 2.1
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# See the files LICENSE.lgpl2 and LICENSE.lgpl3 for full text of the
# GNU Lesser General Public License version 2.1 and 3 respectively.
# This information is also available on the ilastik web site at:
#                 http://ilastik.org/license/
###############################################################################
import os
import re
import fnmatch
import errno
import pathlib
from typing import List

import h5py
import z5py
import numpy


class PathComponents(object):
    """
    Provides a convenient access to path components of a combined external/internal path to a dataset.
    Also, each of the properties listed below is writable, in which case ALL properties are updated accordingly.
    """

    # Only files with these extensions are allowed to have an 'internal' path
    HDF5_EXTS = [".ilp", ".h5", ".hdf5"]
    N5_EXTS = [".n5"]
    NPZ_EXTS = [".npz"]

    def __init__(self, totalPath, cwd=None):
        """
        Initialize the path components.

        :param totalPath: The entire path to the dataset, including any internal path (e.g. the path to an hdf5 dataset).
                          For example, ``totalPath='/some/path/to/file.h5/with/internal/dataset'``

        :param cwd: If provided, relative paths will be converted to absolute paths using this arg as the working directory.
        """
        self._externalPath = None
        self._externalDirectory = None
        self._filename = None
        self._filenameBase = None
        self._extension = None
        self._internalPath = None
        self._internalDatasetName = None
        self._internalDirectory = None

        self._cwd = cwd
        self._init(totalPath, cwd)
        self._initialized = True

    def _init(self, totalPath, cwd):
        ext = None
        extIndex = -1

        if cwd is not None:
            absPath, relPath = getPathVariants(totalPath, cwd)
            totalPath = absPath

        # convention for Windows: use "/"
        totalPath = totalPath.replace("\\", "/")

        # For hdf5/n5 paths, split into external, extension, and internal paths
        for x in self.HDF5_EXTS + self.NPZ_EXTS + self.N5_EXTS:
            if totalPath.find(x) > extIndex:
                extIndex = totalPath.find(x)
                ext = x

        # Comments below refer to this example path:
        # /some/path/to/file.h5/with/internal/dataset
        if ext is not None:
            self._extension = ext  # .h5
            parts = totalPath.split(ext)

            # Must deal with pathological filenames such as /path/to/file.h5_with_duplicate_ext.h5
            while len(parts) > 2:
                parts[0] = parts[0] + ext + parts[1]
                del parts[1]
            self._externalPath = parts[0] + ext  # /some/path/to/file.h5
            self._internalPath = parts[1].replace("\\", "/")  # /with/internal/dataset

            if self._internalPath == "":
                self._internalPath = None
                self._internalDirectory = None
                self._internalDatasetName = None
            else:
                self._internalDirectory = os.path.split(self.internalPath)[0]  # /with/internal
                self._internalDatasetName = os.path.split(self.internalPath)[1]  # dataset
        else:
            # For non-hdf5 files, use normal path/extension (no internal path)
            (self._externalPath, self._extension) = os.path.splitext(totalPath)
            self._externalPath += self._extension
            self._internalPath = None
            self._internalDatasetName = None
            self._internalDirectory = None

        self._externalDirectory = os.path.split(self._externalPath)[0]  # /some/path/to
        self._filename = os.path.split(self._externalPath)[1]  # file.h5
        self._filenameBase = os.path.splitext(self._filename)[0]  # file

    def __setattr__(self, attr, value):
        """
        This prevents us from accidentally writing to a non-existant attribute.
        e.g. if the user tries to say components.fIlEnAmE = 'newfile.h5', raise an error.
        """
        if hasattr(self, "_initialized"):
            # Attempt to get the old attribute first
            oldval = getattr(self, attr)
        object.__setattr__(self, attr, value)

    def totalPath(self):
        """
        Return the (reconstructed) totalPath to the dataset.
        """
        total = self.externalPath
        if self.internalPath:
            total += self.internalPath
        return total

    #
    # Getters
    #

    @property
    def externalPath(self):
        """
        Example: ``/some/path/to/file.h5``
        """
        return self._externalPath

    @property
    def externalDirectory(self):
        """
        Example: ``/some/path/to``
        """
        return self._externalDirectory

    @property
    def filename(self):
        """
        Example: ``file.h5``
        """
        return self._filename

    @property
    def filenameBase(self):
        """
        Example: ``file``
        """
        return self._filenameBase

    @property
    def extension(self):
        """
        Example: ``.h5``
        """
        return self._extension

    @property
    def internalPath(self):
        """
        Example: ``/with/internal/dataset``
        """
        return self._internalPath

    @property
    def internalDatasetName(self):
        """
        Example: ``/dataset``
        """
        return self._internalDatasetName

    @property
    def internalDirectory(self):
        """
        Example: ``/with/internal``
        """
        return self._internalDirectory

    #
    # Setters
    #

    @externalPath.setter
    def externalPath(self, new):
        assert new[-1] != "/"
        if self._internalPath:
            self._init(new + self._internalPath, self._cwd)
        else:
            self._init(new, self._cwd)

    @externalDirectory.setter
    def externalDirectory(self, new):
        new_external = os.path.join(new, self._filename)
        self.externalPath = new_external

    @filename.setter
    def filename(self, new):
        new_external = os.path.join(self._externalDirectory, new)
        self.externalPath = new_external

    @filenameBase.setter
    def filenameBase(self, new):
        new_external = os.path.join(self._externalDirectory, new + self._extension)
        self.externalPath = new_external

    @extension.setter
    def extension(self, new):
        assert (not self._internalPath) or (new in self.HDF5_EXTS), (
            "This PathComponents has an internal path ({}), but you are "
            "attempting to assign a non-hdf5 extension to it ({})".format(self._internalPath, new)
        )
        new_external = os.path.join(self._externalDirectory, self._filenameBase + new)
        self.externalPath = new_external

    @internalPath.setter
    def internalPath(self, new):
        assert self._extension in self.HDF5_EXTS, "Can't set an internal path on a filename with extension {}".format(
            self._extension
        )
        if new:
            self._init(self._externalPath + new, self._cwd)
        else:
            self._init(self._externalPath, self._cwd)

    @internalDatasetName.setter
    def internalDatasetName(self, new):
        new_internal = os.path.join(self._internalDirectory, new)
        self.internalPath = new_internal

    @internalDirectory.setter
    def internalDirectory(self, new):
        if new and new[0] != "/":
            new = "/" + new
        new_internal = os.path.join(new, self._internalDatasetName)
        self.internalPath = new_internal


def areOnSameDrive(path1, path2):
    # if one path is relative, assume they are on same drive
    if isUrl(path1) or isUrl(path2):
        return False
    if not os.path.isabs(path1) or not os.path.isabs(path2):
        return True
    drive1, path1 = os.path.splitdrive(path1)
    drive2, path2 = os.path.splitdrive(path2)
    return drive1 == drive2


def compressPathForDisplay(pathstr, maxlength):
    """Add alternatingly parts of the start and the end of the path
    until maxlength is exceeded. Result: Drive/Dir1/.../Dirn/file"""
    if len(pathstr) <= maxlength:
        return pathstr
    dots = "..."
    component_list = pathstr.split("/")
    prefix = ""
    suffix = "/" + component_list.pop(-1)
    while component_list:
        restlength = maxlength - len(prefix) - len(dots)
        suffix = "/" + component_list.pop(-1) + suffix
        if len(suffix) > restlength:
            suffix = suffix[-restlength:]
            break
        if not component_list:
            break
        c = prefix + component_list.pop(0) + "/"
        if len(c) + len(dots) + len(suffix) > maxlength:
            break
        prefix = c
    return prefix + dots + suffix


def isUrl(path):
    # For now, the simplest rule will work.
    return "://" in path


def isRelative(path: str) -> bool:
    return not isUrl(path) and not os.path.isabs(path)


def splitPath(path: str) -> List[str]:
    """Splits a string using path separator (e.g.: ':' in unix) without clobbering
    protocol URLs like http://example.com"""

    NOT_FOLLOWED_BY_DOUBLE_SLASH = r"(?!//)"
    return re.split(os.path.pathsep + NOT_FOLLOWED_BY_DOUBLE_SLASH, path)


def make_absolute(path, cwd=os.getcwd()):
    return PathComponents(path, cwd).totalPath()


def getPathVariants(originalPath, workingDirectory):
    """
    Take the given filePath (which can be absolute or relative, and may include an internal path suffix),
    and return a tuple of the absolute and relative paths to the file.
    """
    # urls are considered absolute
    if isUrl(originalPath):
        return originalPath, None

    if len(originalPath) > 0 and originalPath[0] == "~":
        originalPath = os.path.expanduser(originalPath)

    relPath = originalPath

    if os.path.isabs(originalPath):
        absPath = originalPath
        if areOnSameDrive(originalPath, workingDirectory):
            relPath = os.path.relpath(absPath, workingDirectory)
        else:
            # Relative path does not always exist.  Caller must check for None.
            relPath = None
    else:
        relPath = originalPath
        absPath = os.path.normpath(os.path.join(workingDirectory, relPath))

    return (absPath.replace("\\", "/"), relPath and relPath.replace("\\", "/"))


def mkdir_p(path):
    """
    Like the bash command 'mkdir -p'
    """
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def lsH5N5(h5N5FileObject, minShape=2, maxShape=5):
    """Generates dataset list of given h5py or z5py file object

    Args:
        h5N5FileObject (h5py.FIle): Opened hdf5 file
        minShape (int, optional): minimum shape of data

    Returns:
        list of datasets inside the given file object
    """
    listOfDatasets = []

    def addObjectNames(objectName, obj):
        if not isinstance(obj, (h5py._hl.dataset.Dataset, z5py.dataset.Dataset)):
            return
        if len(obj.shape) not in range(minShape, maxShape + 1):
            return
        if isinstance(h5N5FileObject, z5py.N5File):
            # make sure we get a path with forward slashes on windows
            objectName = pathlib.Path(objectName).as_posix()
        listOfDatasets.append({"name": objectName, "object": obj})

    h5N5FileObject.visititems(addObjectNames)

    return listOfDatasets


def globH5N5(fileObject, globString):
    """
    globs a hdf5/n5 file like a file system for datasets

    Note: does not glob Attributes, only data sets.

    Recurses through the hdf5/n5 tree using .visititems and matches the provided
    globstring to the respective object names using the fnmatch standard module.


    Args:
        fileObject: h5py.File/z5py.N5File object
        globString: String describing the internal path of the dataset(s) with
            glob-like placeholders

    Returns
        - A sorted list of matched object names. This list is empty if no
          matches occurred.
        - None if fileObject is not a h5 or n5 file object
    """
    if isinstance(fileObject, (h5py.File, z5py.N5File)):
        pathlist = [x["name"] for x in lsH5N5(fileObject)]
    else:
        return None
    matches = globList(pathlist, globString)
    return sorted(matches)


def globNpz(path: str, globString: str):
    with numpy.load(path, mmap_mode="r") as f:
        return sorted(globList(f.files, globString))


def globList(listOfPaths, globString):
    matches = [x for x in listOfPaths if fnmatch.fnmatch(x, globString)]
    return matches
