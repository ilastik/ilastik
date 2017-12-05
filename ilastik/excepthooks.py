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
from future import standard_library
standard_library.install_aliases()
import sys
import traceback
import threading
import io
import logging
logger = logging.getLogger(__name__)
logger.setLevel( logging.INFO )

from ilastik.ilastik_logging import get_logfile_path

def init_early_exit_excepthook():
    """
    This excepthook is used during automated testing.
    If an unhandled exception occurs, it is logged and the app exits immediately.
    """
    from PyQt5.QtWidgets import QApplication
    def print_exc_and_exit(*exc_info):
        _log_exception( *exc_info )
        logger.error("Exiting early due to an unhandled exception.  See error output above.\n")
        QApplication.exit(1)
    sys.excepthook = print_exc_and_exit
    _install_thread_excepthook()

def init_user_mode_excepthook():
    """
    This excepthook is used when the application in "user-friendly" mode.
    - Show the exception error message to the user in a message dialog
    - Also log the exception as an error
    - Special case: Don't show the user errors from the volumina tiling render threads (but still log them)
    """
    def display_and_log(*exc_info):
        # Slot-not-ready errors in the render thread are logged, but not shown to the user.
        from volumina.pixelpipeline.asyncabcs import IndeterminateRequestError
        if isinstance(exc_info[1], IndeterminateRequestError):
            logger.warning( "Caught unhandled IndeterminateRequestError from volumina." )
            sio = io.StringIO()
            traceback.print_exception( exc_info[0], exc_info[1], exc_info[2], file=sio )
            logger.warning( sio.getvalue() )
            return
        
        # All other exceptions are treated as true errors
        _log_exception( *exc_info )
        try:
            from ilastik.shell.gui.startShellGui import shell
            msg = str(exc_info[1]) + "\n"
            logfile_path = get_logfile_path()
            if logfile_path:
                msg += "\n (Advanced information about this error may be found in the log file: {})\n"\
                       "".format( logfile_path )
            if shell:
                shell.postErrorMessage( exc_info[0].__name__, msg )
        except:
            logger.error( "UNHANDLED EXCEPTION WHILE DISPLAYING AN ERROR TO THE USER:" )
            sio = io.StringIO()
            traceback.print_exception( exc_info[0], exc_info[1], exc_info[2], file=sio )
            logger.error( sio.getvalue() )
            raise
    
    sys.excepthook = display_and_log
    _install_thread_excepthook()

def init_developer_mode_excepthook():
    """
    This excepthook is used in debug mode (for developers).  It simply logs the exception.
    """
    sys.excepthook = _log_exception
    _install_thread_excepthook()

def _log_exception(*exc_info):
    thread_name = threading.current_thread().name
    logger.error( "Unhandled exception in thread: '{}'".format(thread_name) )
    if sys.version_info.major == 2:
        sio = io.BytesIO()
    else:
        sio = io.StringIO()

    traceback.print_exception( exc_info[0], exc_info[1], exc_info[2], file=sio )
    logger.error( sio.getvalue() )

def _install_thread_excepthook():
    # This function was copied from: http://bugs.python.org/issue1230540
    # It is necessary because sys.excepthook doesn't work for unhandled exceptions in other threads.
    """
    Workaround for sys.excepthook thread bug
    (https://sourceforge.net/tracker/?func=detail&atid=105470&aid=1230540&group_id=5470).
    Call once from __main__ before creating any threads.
    If using psyco, call psycho.cannotcompile(threading.Thread.run)
    since this replaces a new-style class method.
    """
    run_old = threading.Thread.run
    def run(*args, **kwargs):
        try:
            run_old(*args, **kwargs)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            sys.excepthook(*sys.exc_info())
    threading.Thread.run = run
