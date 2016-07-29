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

def _init_threading_h5py_monkeypatch():
    """
    Due to an h5py bug [1], spurious error messages aren't properly 
    hidden if they occur in any thread other than the main thread.
    As a workaround, here we monkeypatch threading.Thread.run() to 
    make sure all threads silence errors from h5py.
    
    [1]: https://github.com/h5py/h5py/issues/580
    See also: https://github.com/ilastik/ilastik/issues/1120
    """
    import h5py
    if map(int, h5py.__version__.split('.')) <= [2,5,0]:
        import threading
        run_old = threading.Thread.run
        def run(*args, **kwargs):
            h5py._errors.silence_errors()
            run_old(*args, **kwargs)
        threading.Thread.run = run

_init_threading_h5py_monkeypatch()

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
