import nose
import threading
import platform
from functools import partial
from ilastik.shell.gui.startShellGui import startShellGui


class ShellGuiTestCaseBase(object):
    """
    This is a base class for test cases that need to run their tests from within the ilastik shell.

    - The shell is only started once.  All tests are run using the same shell.
    - Subclasses call exec_in_shell to run their test case from within the ilastikshell event loop.
    - Subclasses must specify the workflow they are testing by overriding the workflowClass() classmethod. 
    - Subclasses may access the shell and workflow via the shell and workflow class members.
    """
    
    @classmethod
    def setupClass(cls):
        """
        Start the shell and wait until it is finished initializing.
        """
        init_complete = threading.Event()
        
        def initTest(shell, workflow):
            cls.shell = shell
            cls.workflow = workflow
            init_complete.set()

        # This partial starts up the gui.
        startGui = partial(startShellGui, cls.workflowClass(), initTest)

        # If nose was run from the main thread, start the gui in a separate thread.
        # If nose is running in a non-main thread, we assume the main thread is available to launch the gui.
        # This is a workaround for Mac OS, in which the gui MUST be started from the main thread 
        #  (which means we've got to run nose from a separate thread.)
        if threading.current_thread() == threading.enumerate()[0]:
            if "Darwin" in platform.platform():
                # On Mac, we can't run the gui in a non-main thread.
                raise nose.SkipTest
            else:
                # Start the gui in a separate thread.  Workflow is provided by our subclass.
                cls.guiThread = threading.Thread( target=startGui )
                cls.guiThread.start()
        else:
                # We're currently running in a non-main thread.
                # Start the gui IN THE MAIN THREAD.  Workflow is provided by our subclass.
                from tests.helpers.mainThreadHelpers import run_in_main_thread
                run_in_main_thread( startGui )
                cls.guiThread = None

        init_complete.wait()

    @classmethod
    def teardownClass(cls):
        """
        Force the shell to quit (without a save prompt), and wait for the app to exit.
        """
        def teardown_impl():
            cls.shell.onQuitActionTriggered(True)
        cls.shell.thunkEventHandler.post(teardown_impl)
        
        if cls.guiThread is not None:
            cls.guiThread.join()
        

    @classmethod
    def exec_in_shell(cls, func):
        """
        Execute the given function within the shell event loop.
        Block until the function completes.
        """
        e = threading.Event()
        def impl():
            func()
            e.set()            
        cls.shell.thunkEventHandler.post(impl)
        e.wait()

    @classmethod
    def workflowClass(cls):
        """
        Override this to specify which workflow to start the shell with (e.g. PixelClassificationWorkflow)
        """
        raise NotImplementedError    

def run_shell_nosetest(filename):
    def run_nose():
        import sys
        import nose
        sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
        sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
        nose.run(defaultTest=filename)

    import platform
    # On darwin, we must run nose in a separate thread and let the gui run in the main thread.
    # (This means we can't run this test using the nose command line tool.)
    if "Darwin" in platform.platform():
        import threading
        noseThread = threading.Thread(target=run_nose)
        noseThread.start()

        from tests.helpers.mainThreadHelpers import wait_for_main_func
        wait_for_main_func()
        noseThread.join()
    else:
        # Linux: Run this test like usual (as if we're running from the command line)
        run_nose()
