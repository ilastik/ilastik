from __future__ import absolute_import
from __future__ import division
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
from builtins import range
from past.utils import old_div
import sys
import os
import threading
import traceback
import atexit
import platform
from functools import partial

import pytest

from PyQt5.QtCore import Qt, QEvent, QPoint, QTimer
from PyQt5.QtGui import QPixmap, QMouseEvent
from PyQt5.QtWidgets import QApplication, qApp

import ilastik.config
from ilastik.shell.gui.startShellGui import launchShell
from ilastik.utility.gui.threadRouter import ThreadRouter
from .mainThreadHelpers import wait_for_main_func, run_in_main_thread

from ilastik.ilastik_logging import default_config
default_config.init(output_mode=default_config.OutputMode.CONSOLE)

@atexit.register
def quitApp():
    if qApp is not None:
        qApp.quit()


class MainThreadException(Exception):
    """Raised if GUI tests are run from main thread. Can't start QT app."""
    pass


def run_shell_test(filename):
    # This only works from the main thread.
    assert threading.current_thread().getName() == "MainThread"
    import pytest

    def run_test():
        pytest.main([filename, '--capture=no'])

    testThread = threading.Thread(target=run_test)
    testThread.start()
    wait_for_main_func()
    testThread.join()


def is_main_thread():
    return threading.current_thread().getName() == "MainThread"


class ShellGuiTestCaseBase(object):
    """
    This is a base class for test cases that need to run their tests from within the ilastik shell.

    - The shell is only started once.  All tests are run using the same shell.
    - Subclasses call exec_in_shell to run their test case from within the ilastikshell event loop.
    - Subclasses must specify the workflow they are testing by overriding the workflowClass() classmethod.
    - Subclasses may access the shell and workflow via the shell and workflow class members.
    """
    mainThreadEvent = threading.Event()

    @classmethod
    def setup_class(cls):
        """
        Start the shell and wait until it is finished initializing.
        """
        init_complete = threading.Event()

        def initTest(shell):
            cls.shell = shell
            init_complete.set()

        appCreationEvent = threading.Event()
        def createApp():
            # Create the application in the current thread.
            # The current thread is now the application main thread.
            assert threading.current_thread().getName() == "MainThread", "Error: app must be created in the main thread."
            ShellGuiTestCaseBase.app = QApplication([])
            app = ShellGuiTestCaseBase.app

            # Don't auto-quit the app when the window closes.  We want to re-use it for the next test.
            app.setQuitOnLastWindowClosed(False)

            # Create a threadRouter object that allows us to send work to the app from other threads.
            ShellGuiTestCaseBase.threadRouter = ThreadRouter(app)

            # Set the appCreationEvent so the tests can proceed after the app's event loop has started
            QTimer.singleShot(0, appCreationEvent.set )

            # Start the event loop
            app.exec_()

        # If test was run from the main thread, exit now.
        # If test is running in a non-main thread, we assume the main thread is available to launch the gui.
        if is_main_thread():
            pytest.xfail("Launched GUI test from MainThread. Skipping test.")
        # We're currently running in a non-main thread.
        # Start the gui IN THE MAIN THREAD.  Workflow is provided by our subclass.
        run_in_main_thread( createApp )
        appCreationEvent.wait()

        platform_str = platform.platform().lower()
        if 'ubuntu' in platform_str or 'fedora' in platform_str:
            QApplication.setAttribute(Qt.AA_X11InitThreads, True)

        if ilastik.config.cfg.getboolean("ilastik", "debug"):
            QApplication.setAttribute(Qt.AA_DontUseNativeMenuBar, True)

        # Use the thread router to launch the shell in the app thread
        ShellGuiTestCaseBase.threadRouter.routeToParent.emit( partial(launchShell, None, [], [initTest] ) )
        init_complete.wait()

    @classmethod
    def teardown_class(cls):
        """
        Force the shell to quit (without a save prompt), and wait for the app to exit.
        """
        # Make sure the app has finished quitting before continuing
        def teardown_impl():
            cls.shell.onQuitActionTriggered(force=True, quitApp=False)

        # Wait for the shell to really be finish shutting down before we finish the test
        finished = threading.Event()
        cls.shell.thunkEventHandler.post(teardown_impl)
        cls.shell.thunkEventHandler.post(finished.set)
        # Sometimes the GUI tests halt, which is an open problem
        # in order not to block the CI we give here a super generous timeout
        # (usually this takes no time at all) of 10 seconds
        finished.wait(timeout=10.0)
        if not finished.is_set():
            pytest.xfail("GUI test timeout")

    @classmethod
    def exec_in_shell(cls, func):
        """
        Execute the given function within the shell event loop.
        Block until the function completes.
        If there were exceptions, assert so that this test marked as failed.
        """
        testFinished = threading.Event()
        errors = []

        def impl():
            try:
                func()
            except AssertionError as e:
                traceback.print_exc()
                errors.append(e)
            except Exception as e:
                traceback.print_exc()
                errors.append(e)
            testFinished.set()

        cls.shell.thunkEventHandler.post(impl)
        QApplication.processEvents()
        testFinished.wait()

        if len(errors) > 0:
            if isinstance(errors[0], AssertionError):
                raise AssertionError("Failed a GUI test.  See output above.")
            else:
                raise RuntimeError("Errors during a GUI test.  See output above.")

    @classmethod
    def workflowClass(cls):
        """
        Override this to specify which workflow to start the shell with (e.g. PixelClassificationWorkflow)
        """
        raise NotImplementedError

    ###
    ### Convenience functions for subclasses to use during testing.
    ###

    def waitForViews(self, views):
        """
        Wait for the given image views to complete their rendering and repainting.
        """
        for imgView in views:
            # Wait for the image to be rendered into the view.
            imgView.scene().joinRenderingAllTiles()
            imgView.viewport().repaint()

        # Let the GUI catch up: Process all events
        QApplication.processEvents()

    def getPixelColor(self, imgView, coordinates, debugFileName=None, relativeToCenter=True):
        """
        Sample the color of the pixel at the given coordinates.
        If debugFileName is provided, export the view for debugging purposes.

        Example:
            self.getPixelColor(myview, (10,10), 'myview.png')
        """
        img = imgView.grab().toImage()

        if debugFileName is not None:
            img.save(debugFileName)

        point = QPoint(*coordinates)
        if relativeToCenter:
            centerPoint = QPoint(img.size().width(), img.size().height()) / 2
            point += centerPoint

        return img.pixel(point)

    def moveMouseFromCenter(self, imgView, coords ,modifier =Qt.NoModifier ):
        centerPoint = old_div(imgView.rect().bottomRight(), 2)
        point = QPoint(*coords) + centerPoint
        move = QMouseEvent( QEvent.MouseMove, point, Qt.NoButton, Qt.NoButton, modifier  )
        QApplication.sendEvent(imgView, move )
        QApplication.processEvents()

    def strokeMouseFromCenter(self, imgView, start, end, modifier = Qt.NoModifier,numSteps = 10):
        """
        Drag the mouse between two coordinates.
        A modifier can be specified that will be keep pressed
        default no modifier
        """



        centerPoint = old_div(imgView.rect().bottomRight(), 2)

        startPoint = QPoint(*start) + centerPoint
        endPoint = QPoint(*end) + centerPoint

        # Note: Due to the implementation of volumina.EventSwitch.eventFilter(),
        #       mouse events intended for the ImageView MUST go through the viewport.

        # Move to start
        move = QMouseEvent( QEvent.MouseMove, startPoint, Qt.NoButton, Qt.NoButton, modifier )
        QApplication.sendEvent(imgView.viewport(), move )

        # Press left button
        press = QMouseEvent( QEvent.MouseButtonPress, startPoint, Qt.LeftButton, Qt.NoButton, modifier)
        QApplication.sendEvent(imgView.viewport(), press )

        # Move to end in several steps
        #numSteps = numSteps
        for i in range(numSteps):
            nextPoint = startPoint + (endPoint - startPoint) * ( old_div(float(i), numSteps) )
            move = QMouseEvent( QEvent.MouseMove, nextPoint, Qt.NoButton, Qt.NoButton, modifier )
            QApplication.sendEvent(imgView.viewport(), move )

        # Move to end
        move = QMouseEvent( QEvent.MouseMove, endPoint, Qt.NoButton, Qt.NoButton, modifier )
        QApplication.sendEvent(imgView.viewport(), move )

        # Release left button
        release = QMouseEvent( QEvent.MouseButtonRelease, endPoint, Qt.LeftButton, Qt.NoButton, modifier )
        QApplication.sendEvent(imgView.viewport(), release )

        # Wait for the gui to catch up
        QApplication.processEvents()
        self.waitForViews([imgView])
