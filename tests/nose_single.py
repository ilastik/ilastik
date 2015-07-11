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
#		   http://ilastik.org/license.html
###############################################################################
import sys
import nose
import threading

# Copied from ilastik_main.py
def _monkey_patch_h5py():
    """
    This workaround avoids error messages from HDF5 when accessing non-existing
    files, datasets, and dataset attributes from non-main threads.

    See also:
    - https://github.com/h5py/h5py/issues/580
    - https://github.com/h5py/h5py/issues/582
    """
    import os
    import h5py

    old_dataset_getitem = h5py.Group.__getitem__
    def new_dataset_getitem(group, key):
        if key not in group:
            raise KeyError("Unable to open object (Object '{}' doesn't exist)".format( key ))
        return old_dataset_getitem(group, key)
    h5py.Group.__getitem__ = new_dataset_getitem

    old_file_init = h5py.File.__init__
    def new_file_init(f, name, mode=None, driver=None, libver=None, userblock_size=None, swmr=False, **kwds):
        if isinstance(name, (str, buffer)) and (mode is None or mode == 'a'):
            if not os.path.exists(name):
                mode = 'w'
        old_file_init(f, name, mode, driver, libver, userblock_size, swmr, **kwds)
    h5py.File.__init__ = new_file_init

    old_attr_getitem = h5py._hl.attrs.AttributeManager.__getitem__
    def new_attr_getitem(attrs, key):
        if key not in attrs:
            raise KeyError("Can't open attribute (Can't locate attribute: '{}')".format(key))
        return old_attr_getitem(attrs, key)
    h5py._hl.attrs.AttributeManager.__getitem__ = new_attr_getitem

_monkey_patch_h5py()

from helpers import mainThreadHelpers

# For some mysterious reason, we need to make sure that volumina.api gets imported 
#  from the main thread before nose imports it from a separate thread.
# If we don't, QT gets confused about which thread is really the main thread.
# This must be because the "main" thread is determined by some QT class or module 
#  that first becomes active somewhere in volumina, but I can't figure out which one it is.
#  Otherwise, I would just go ahead and import it now.
import volumina.api

if __name__ == "__main__":
#    sys.argv.append("test_applets/pixelClassification/testPixelClassificationGui.py")
#    sys.argv.append("--nocapture")
#    sys.argv.append("--nologcapture")
    if len(sys.argv) < 2:
        sys.stderr.write( "Usage: python {} FILE [--nocapture] [--nologcapture]\n".format(sys.argv[0]) )
        sys.exit(1)

    #
    # Run a SINGLE test file using nosetests, which is launched in a separate thread.
    # The main thread (i.e. this one) is left available for launching other tasks (e.g. the GUI).
    #    
    filename = sys.argv.pop(1)
    sys.exit(mainThreadHelpers.run_nosetests_in_separate_thread(filename))
