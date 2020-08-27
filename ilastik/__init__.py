from __future__ import absolute_import

###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
#      http://ilastik.org/license.html
###############################################################################
import re

################################
# # Add Submodules to sys.path ##
################################
import os
import h5py
import time
from typing import Optional, Iterable, List
from pkg_resources import parse_version

##################
# # Version info ##
##################


def _format_version(t):
    """converts a tuple to a string"""
    return ".".join(str(i) for i in t)


__version_info__ = (1, 4, "0b8")

__version__ = _format_version(__version_info__)


class Project:
    ILASTIK_VERSION = "/ilastikVersion"
    WORKFLOW_NAME = "/workflowName"
    UPDATED_TIME = "/time"

    BASE_KEYS = [ILASTIK_VERSION, WORKFLOW_NAME, UPDATED_TIME]

    def __init__(self, project_file: h5py.File):
        self.file = project_file

    @property
    def local_data_group(self) -> h5py.Group:
        return self.file.require_group("Input Data/local_data")

    def close(self):
        self.file.close()

    def flush(self):
        self.file.flush()

    def populateFrom(self, importedFile: h5py.File, topGroupKeys: List[str]):
        # We copy ilastikVersion as well as workflowName because that can influence the way in which the deserializers
        # interpret the imported data
        for key in topGroupKeys + self.BASE_KEYS:
            if key in importedFile.keys():
                self.clearValue(key)
                importedFile.copy(key, self.file["/"])

    def clearValue(self, key: str):
        if key in self.file.keys():
            del self.file[key]

    def _updateValue(self, key: str, value):
        if key in self.file:
            del self.file[key]
        self.file.create_dataset(key, data=value)

    def _getString(self, key: str) -> Optional[str]:
        if key not in self.file:
            return None
        return self.file[key][()].decode("utf-8")

    @property
    def ilastikVersion(self) -> Optional["Version"]:
        version_string = self._getString(self.ILASTIK_VERSION)
        return version_string if version_string is None else parse_version(version_string)

    @property
    def workflowName(self) -> Optional[str]:
        return self._getString(self.WORKFLOW_NAME)

    def updateWorkflowName(self, workflowName: str):
        self._updateValue(self.WORKFLOW_NAME, workflowName.encode("utf-8"))

    def updateVersion(self, value=__version__):
        self._updateValue(self.ILASTIK_VERSION, str(value).encode("utf-8"))


def convertVersion(vstring):
    if not isinstance(vstring, str):
        raise Exception(f"tried to convert non-string version: {vstring}")

    # We permit versions like '1.0.5b', in which case '5b'
    #  is simply converted to the integer 5 for compatibility purposes.
    int_tuple = ()
    for i in vstring.split("."):
        m = re.search("(\d+)", i)
        assert bool(m), "Don't understand version component: {}".format(i)
        next_int = int(m.groups()[0])
        int_tuple = int_tuple + (next_int,)

    return int_tuple


def isVersionCompatible(version):
    """Return True if the current project file format is
    backwards-compatible with the format used in this version of
    ilastik.
    """
    if isinstance(version, float):
        version = str(version)

    # Only consider major and minor rev
    v1 = convertVersion(version)[0:2]
    v2 = __version_info__[0:2]

    # Version 1.0 is compatible in all respects with version 0.6
    compatible_set = [(0, 6), (1, 0), (1, 1), (1, 2), (1, 3), (1, 4)]
    if v1 in compatible_set and v2 in compatible_set:
        return True

    # Otherwise, we need an exact match (for now)
    return v1 == v2


#######################
# # Dependency checks ##
#######################


def _do_check(fnd, rqd, msg):
    if fnd < rqd:
        fstr = _format_version(fnd)
        rstr = _format_version(rqd)
        raise Exception(msg.format(fstr, rstr))


def _check_depends():
    import h5py

    _do_check(
        h5py.version.version_tuple,
        (2, 1, 0),
        "h5py version {0} too old; versions of h5py before {1} are not " "threadsafe.",
    )


_check_depends()
