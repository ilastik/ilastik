import sys
import nose
import threading
import traceback
import atexit
import platform
from functools import partial

from PyQt4.QtCore import Qt, QEvent, QPoint, QTimer
from PyQt4.QtGui import QMouseEvent, QApplication, QPixmap, qApp

import ilastik.config
from ilastik.shell.gui.startShellGui import launchShell
from ilastik.utility.gui.threadRouter import ThreadRouter
from tests.helpers.mainThreadHelpers import wait_for_main_func, run_in_main_thread

@atexit.register
def quitApp():
    if qApp is not None:
        qApp.quit()

def run_shell_nosetest(filename):
    """
    Launch nosetests from a separate thread, and pause this thread while the test runs the GUI in it.
    """
    # This only works from the main thread.
    assert threading.current_thread() == threading.enumerate()[0]

    def run_nose():
        sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
        sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
        nose.run(defaultTest=filename)

    noseThread = threading.Thread(target=run_nose)
    noseThread.start()

    wait_for_main_func()
    noseThread.join()

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
    def setupClass(cls):
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
            assert threading.current_thread() == threading.enumerate()[0], "Error: app must be created in the main thread."
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
        
        # If nose was run from the main thread, exit now.
        # If nose is running in a non-main thread, we assume the main thread is available to launch the gui.
        if threading.current_thread() == threading.enumerate()[0]:
            # Don't run GUI tests in the main thread.
            sys.stderr.write( "NOSE WAS RUN FROM THE MAIN THREAD.  SKIPPING GUI TEST\n" )
            raise nose.SkipTest
        else:
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
        ShellGuiTestCaseBase.threadRouter.routeToParent.emit( partial(launchShell, None, initTest ) )
        init_complete.wait()

    @classmethod
    def teardownClass(cls):
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
        finished.wait()

    @classmethod
    def exec_in_shell(cls, func):
        """
        Execute the given function within the shell event loop.
        Block until the function completes.
        If there were exceptions, assert so that nose marks this test as failed.
        """
        testFinished = threading.Event()
        errors = []
        
        def impl():
            try:
                func()
            except AssertionError, e:
                traceback.print_exc()
                errors.append(e)
            except Exception, e:
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
        img = QPixmap.grabWidget(imgView).toImage()
        
        if debugFileName is not None:
            img.save(debugFileName)

        point = QPoint(*coordinates)
        if relativeToCenter:
            centerPoint = imgView.rect().bottomRight() / 2
            point += centerPoint
        
        return img.pixel(point)

    def moveMouseFromCenter(self, imgView, coords):
        centerPoint = imgView.rect().bottomRight() / 2
        point = QPoint(*coords) + centerPoint
        move = QMouseEvent( QEvent.MouseMove, point, Qt.NoButton, Qt.NoButton, Qt.NoModifier )
        QApplication.postEvent(imgView, move )
        QApplication.processEvents()

    def strokeMouseFromCenter(self, imgView, start, end):
        """
        Drag the mouse between two coordinates.
        """
        centerPoint = imgView.rect().bottomRight() / 2

        startPoint = QPoint(*start) + centerPoint
        endPoint = QPoint(*end) + centerPoint

        # Note: Due to the implementation of volumina.EventSwitch.eventFilter(), 
        #       mouse events intended for the ImageView MUST go through the viewport.

        # Move to start
        move = QMouseEvent( QEvent.MouseMove, startPoint, Qt.NoButton, Qt.NoButton, Qt.NoModifier )
        QApplication.postEvent(imgView.viewport(), move )

        # Press left button
        press = QMouseEvent( QEvent.MouseButtonPress, startPoint, Qt.LeftButton, Qt.NoButton, Qt.NoModifier )
        QApplication.postEvent(imgView.viewport(), press )

        # Move to end in several steps
        numSteps = 10
        for i in range(numSteps):
            nextPoint = startPoint + (endPoint - startPoint) * ( float(i) / numSteps )
            move = QMouseEvent( QEvent.MouseMove, nextPoint, Qt.NoButton, Qt.NoButton, Qt.NoModifier )
            QApplication.postEvent(imgView.viewport(), move )

        # Move to end
        move = QMouseEvent( QEvent.MouseMove, endPoint, Qt.NoButton, Qt.NoButton, Qt.NoModifier )
        QApplication.postEvent(imgView.viewport(), move )

        # Release left button
        release = QMouseEvent( QEvent.MouseButtonRelease, endPoint, Qt.LeftButton, Qt.NoButton, Qt.NoModifier )
        QApplication.postEvent(imgView.viewport(), release )

        # Wait for the gui to catch up
        QApplication.processEvents()
        self.waitForViews([imgView])
