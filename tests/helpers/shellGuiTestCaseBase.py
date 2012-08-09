import threading
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

        # Start the gui in a separate thread.  Workflow is provided by our subclass.
        cls.guiThread = threading.Thread( target=partial(startShellGui, cls.workflowClass(), initTest) )
        cls.guiThread.start()
        init_complete.wait()

    @classmethod
    def teardownClass(cls):
        """
        Force the shell to quit (without a save prompt), and wait for the app to exit.
        """
        def teardown_impl():
            cls.shell.onQuitActionTriggered(True)
        cls.shell.thunkEventHandler.post(teardown_impl)
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

