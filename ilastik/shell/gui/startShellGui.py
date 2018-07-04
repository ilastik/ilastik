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
#		   http://ilastik.org/license.html
###############################################################################
import os
import functools
import platform

#make the program quit on Ctrl+C
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QTimer

from . import splashScreen
import ilastik.config
shell = None

def startShellGui(workflow_cmdline_args, preinit_funcs, postinit_funcs):
    """
    Create an application and launch the shell in it.
    """

    """
    The next two lines fix the following xcb error on Ubuntu by calling X11InitThreads before loading the QApplication:
       [xcb] Unknown request in queue while dequeuing
       [xcb] Most likely this is a multi-threaded client and XInitThreads has not been called
       [xcb] Aborting, sorry about that.
       python: ../../src/xcb_io.c:178: dequeue_pending_request: Assertion !xcb_xlib_unknown_req_in_deq failed.
    """
    platform_str = platform.platform().lower()
    if 'ubuntu' in platform_str or 'fedora' in platform_str or 'debian' in platform_str:
        QApplication.setAttribute(Qt.AA_X11InitThreads, True)

    if ilastik.config.cfg.getboolean("ilastik", "debug"):
        QApplication.setAttribute(Qt.AA_DontUseNativeMenuBar, True)

    app = QApplication([])
    _applyStyleSheet(app)

    splashScreen.showSplashScreen()
    app.processEvents()
    QTimer.singleShot( 0, functools.partial(launchShell, workflow_cmdline_args, preinit_funcs, postinit_funcs ) )
    QTimer.singleShot( 0, splashScreen.hideSplashScreen)

    return app.exec_()

def _applyStyleSheet(app):
    """
    Apply application-wide style-sheet rules.
    """
    styleSheetPath = os.path.join( os.path.split(__file__)[0], 'ilastik-style.qss' )
    with open( styleSheetPath, 'r' ) as f:
        styleSheetText = f.read()
        app.setStyleSheet(styleSheetText)


def launchShell(workflow_cmdline_args, preinit_funcs, postinit_funcs):
    """
    Start the ilastik shell GUI with the given workflow type.
    Note: A QApplication must already exist, and you must call this function from its event loop.
    """
    for f in preinit_funcs:
        f()

    # This will import a lot of stuff (essentially the entire program).
    # We use a late import here so the splash screen is shown while this lengthy import happens.
    from ilastik.shell.gui.ilastikShell import IlastikShell
    
    # Create the shell and populate it
    global shell
    shell = IlastikShell(None, workflow_cmdline_args)

    assert QApplication.instance().thread() == shell.thread()

    if ilastik.config.cfg.getboolean("ilastik", "debug"):
        # In debug mode, we always start with the same size window.
        # This is critical for recorded test cases.
        shell.resize(1000, 750)
        # Also, ensure that the window title bar doesn't start off screen, 
        #  which can be an issue when using xvfb or vnc viewers
        shell.move(10,10)
    shell.show()
    
    # FIXME: The workflow_cmdline_args parameter is meant
    #        for arguments to the workflow, not the shell.
    #        This is a bit hacky.
    if workflow_cmdline_args and "--fullscreen" in workflow_cmdline_args:
        workflow_cmdline_args.remove('--fullscreen')
        shell.showMaximized()
    
    # Run post-init funcs
    for f in postinit_funcs:
        QTimer.singleShot(0, functools.partial(f, shell) )
    
    # On Mac, the main window needs to be explicitly raised
    shell.raise_()
    QApplication.instance().processEvents()
    
    return shell
