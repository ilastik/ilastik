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
# 		   http://ilastik.org/license.html
###############################################################################

import atexit
import contextlib
import numbers
import threading
from typing import Iterable, Sequence, Union

import pytest
from ilastik.ilastik_logging import default_config
from volumina.imageView2D import ImageView2D
from qtpy.QtCore import QEvent, QPoint, QPointF, Qt
from qtpy.QtGui import (
    QMouseEvent,
    QImage,
    QPainter,
    QOpenGLFramebufferObjectFormat,
    QOpenGLFramebufferObject,
    QOpenGLPaintDevice,
)
from qtpy.QtWidgets import QAbstractScrollArea, QApplication, QOpenGLWidget

from .mainThreadHelpers import wait_for_main_func

default_config.init(output_mode=default_config.OutputMode.CONSOLE)


@atexit.register
def quitApp():
    qapp = QApplication.instance()
    if qapp is not None:
        qapp.quit()


class MainThreadException(Exception):
    """Raised if GUI tests are run from main thread. Can't start QT app."""

    pass


def run_shell_test(filename):
    # This only works from the main thread.
    assert threading.current_thread().getName() == "MainThread"
    import pytest

    def run_test():
        pytest.main([filename, "--capture=no"])

    testThread = threading.Thread(target=run_test)
    testThread.start()
    wait_for_main_func()
    testThread.join()


def is_main_thread():
    return threading.current_thread().getName() == "MainThread"


@pytest.mark.guitest
class ShellGuiTestCaseBase(object):
    """
    This is a base class for test cases that need to run their tests from within the ilastik shell.

    - The shell is only started once.  All tests are run using the same shell.
    - Subclasses call exec_in_shell to run their test case from within the ilastikshell event loop.
    - Subclasses must specify the workflow they are testing by overriding the workflowClass() classmethod.
    - Subclasses may access the shell and workflow via the shell and workflow class members.
    """

    mainThreadEvent = threading.Event()
    app = None

    @classmethod
    def setup_class(cls):
        pass

    @classmethod
    def teardown_class(cls):
        pass

    @classmethod
    def exec_in_shell(cls, func, *args, **kwargs):
        """
        Execute the given function within the shell event loop.
        Block until the function completes.
        If there were exceptions, assert so that this test marked as failed.
        """
        testFinished = threading.Event()

        def impl():
            try:
                func(*args, **kwargs)
            finally:
                testFinished.set()

        cls.shell.thunkEventHandler.post(impl)
        QApplication.processEvents()
        testFinished.wait()

    @classmethod
    def workflowClass(cls):
        """
        Override this to specify which workflow to start the shell with (e.g. PixelClassificationWorkflow)
        """
        raise NotImplementedError

    ###
    ### Convenience functions for subclasses to use during testing.
    ###

    def waitForViews(self, views: Sequence[ImageView2D]):
        """
        Wait for the given image views to complete their rendering and repainting.
        """
        for imgView in views:
            # Wait for the image to be rendered into the view.
            imgView.scene().joinRenderingAllTiles()
            imgView.viewport().repaint()

        # Let the GUI catch up: Process all events
        QApplication.processEvents()

    @contextlib.contextmanager
    def hiddenCursor(self, imgView: ImageView2D):
        """Context manager that hides the given image view's cursor

        Useful, e.g. when accessing the viewport's rendered image - where
        sampling the cursor would be unwanted.
        """
        wasVisible = imgView._crossHairCursor.isVisible()
        try:
            imgView._crossHairCursor.setVisible(False)
            # Wait for the gui to catch up
            QApplication.processEvents()
            self.waitForViews([imgView])

            yield
        finally:
            imgView._crossHairCursor.setVisible(wasVisible)
            # Wait for the gui to catch up
            QApplication.processEvents()
            self.waitForViews([imgView])

    def getPixelColor(self, imgView, coordinates, debugFileName=None, relativeToCenter=True):
        """
        Sample the color of the pixel at the given coordinates.
        If debugFileName is provided, export the view for debugging purposes.

        Cursor is hidden while sampling the image.

        Example:
            self.getPixelColor(myview, (10,10), 'myview.png')
        """
        with self.hiddenCursor(imgView):
            viewport = imgView.viewport()
            if isinstance(viewport, QOpenGLWidget):
                # adapted from https://stackoverflow.com/a/31382768
                viewport.makeCurrent()
                buffer_format = QOpenGLFramebufferObjectFormat()
                buffer_format.setAttachment(QOpenGLFramebufferObject.CombinedDepthStencil)
                frame_buffer = QOpenGLFramebufferObject(imgView.width(), imgView.height(), buffer_format)
                frame_buffer.bind()
                paint_device = QOpenGLPaintDevice(imgView.width(), imgView.height())
                painter = QPainter(paint_device)
                # captures mixed OpenGL and non-OpenGL QGraphicsitems
                imgView.render(painter)
                painter.end()
                img = QImage(frame_buffer.toImage())
            else:
                img = imgView.grab().toImage()

        if debugFileName is not None:
            img.save(debugFileName)

        point = QPoint(*coordinates)
        if relativeToCenter:
            centerPoint = QPoint(img.size().width(), img.size().height()) / 2
            point += centerPoint

        return img.pixel(point)

    def moveMouseFromCenter(
        self,
        imgView: QAbstractScrollArea,
        point: Union[QPointF, QPoint, Iterable[numbers.Real]],
        modifier: int = Qt.NoModifier,
    ):
        """Move the mouse to a specific point.

        Args:
            imgView: View that will receive mouse events.
            point: Target coordinate in relation to imageView center.
            modifier: This modifier will be active when pressing, moving and releasing.

        """
        centerPoint = imgView.rect().bottomRight() / 2
        point = _asQPointF(point) + centerPoint
        move = QMouseEvent(QEvent.MouseMove, point, Qt.NoButton, Qt.NoButton, modifier)
        QApplication.sendEvent(imgView.viewport(), move)
        QApplication.processEvents()
        self.waitForViews([imgView])

    def strokeMouse(
        self,
        imgView: QAbstractScrollArea,
        startPoint: Union[QPointF, QPoint, Iterable[numbers.Real]],
        endPoint: Union[QPointF, QPoint, Iterable[numbers.Real]],
        modifier: int = Qt.NoModifier,
        numSteps: int = 10,
    ) -> None:
        """Drag the mouse between 2 points.

        Args:
            imgView: View that will receive mouse events.
            startPoint: Start coordinates, inclusive.
            endPoint:  End coordinates, also inclusive.
            modifier: This modifier will be active when pressing, moving and releasing.
            numSteps: The number of mouse move events.

        See Also:
            :func:`strokeMouseFromCenter`.
        """
        startPoint = _asQPointF(startPoint)
        endPoint = _asQPointF(endPoint)

        # Note: Due to the implementation of volumina.EventSwitch.eventFilter(),
        #       mouse events intended for the ImageView MUST go through the viewport.

        # Move to start
        move = QMouseEvent(QEvent.MouseMove, startPoint, Qt.NoButton, Qt.NoButton, modifier)
        QApplication.sendEvent(imgView.viewport(), move)

        # Press left button
        press = QMouseEvent(QEvent.MouseButtonPress, startPoint, Qt.LeftButton, Qt.NoButton, modifier)
        QApplication.sendEvent(imgView.viewport(), press)

        # Move to end in several steps
        for i in range(1, numSteps + 1):
            a = i / numSteps
            nextPoint = (1 - a) * startPoint + a * endPoint
            move = QMouseEvent(QEvent.MouseMove, nextPoint, Qt.NoButton, Qt.NoButton, modifier)
            QApplication.sendEvent(imgView.viewport(), move)

        # Release left button
        release = QMouseEvent(QEvent.MouseButtonRelease, endPoint, Qt.LeftButton, Qt.NoButton, modifier)
        QApplication.sendEvent(imgView.viewport(), release)

        # Wait for the gui to catch up
        QApplication.processEvents()
        self.waitForViews([imgView])

    def strokeMouseFromCenter(
        self,
        imgView: QAbstractScrollArea,
        startPoint: Union[QPointF, QPoint, Iterable[numbers.Real]],
        endPoint: Union[QPointF, QPoint, Iterable[numbers.Real]],
        modifier: int = Qt.NoModifier,
        numSteps: int = 10,
    ) -> None:
        """Drag the mouse between 2 points, relative to the view's center.

        Args:
            imgView: View that will receive mouse events.
            startPoint: Start offset from the `imgView` center, inclusive.
            endPoint:  End offset from the `imgView` center, also inclusive.
            modifier: This modifier will be active when pressing, moving and releasing.
            numSteps: The number of mouse move events.

        See Also:
            :func:`strokeMouse`.
        """
        # FIXME: The simpler "center" calculation below breaks tests on CI.
        # center = imgView.rect().center()
        center = imgView.rect().bottomRight() / 2
        self.strokeMouse(imgView, _asQPointF(startPoint) + center, _asQPointF(endPoint) + center, modifier, numSteps)


def _asQPointF(x: Union[QPointF, QPoint, Iterable[numbers.Real]]) -> QPointF:
    if isinstance(x, QPointF):
        return x
    if isinstance(x, QPoint):
        return QPointF(x)
    return QPointF(*x)
