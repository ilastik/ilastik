import threading
import time
import queue
import sys
import warnings
import platform
import itertools

import pytest

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from _pytest.main import pytest_runtestloop as _pytest_runtestloop

import ilastik.config

from ilastik.utility.gui.threadRouter import ThreadRouter
from ilastik.utility.itertools import pairwise
from ilastik.shell.gui.startShellGui import launchShell

# Every function starting with pytest_ in this module is a pytest hook
# that modifies specific behavior of test life cycle
# Useful links for understanding pytest plugins/conftest.py files.
# Writing Plugins: https://docs.pytest.org/en/3.10.1/writing_plugins.html
# Hookspec Reference: https://docs.pytest.org/en/3.10.1/_modules/_pytest/hookspec.html
# If hookspec hash @hookspec(firstresult=True) in its definition, this means
# that hooks will be executed until first not None result is found.


GUI_TEST_TIMEOUT = 20  # Seconds


def pytest_addoption(parser):
    """Add command-line flags for pytest."""
    parser.addoption("--run-legacy-gui", action="store_true",
                     help="runs legacy gui tests")


def pytest_pyfunc_call(pyfuncitem):
    """
    Defines protocol for legacy GUI test execution
    It should be run in a separate thread
    :param pyfuncitem: wrapper object around test function
    see https://docs.pytest.org/en/3.10.1/reference.html#function
    """
    if not is_gui_test(pyfuncitem):
        return

    bucket = [None]

    def testfunc():
        try:
            # Call actual test function
            return pyfuncitem.obj()
        except Exception:
            bucket[0] = sys.exc_info

    thread = threading.Thread(target=testfunc)
    thread.daemon = True

    start = time.time()
    thread.start()

    while thread.is_alive():
        time.sleep(0.2)
        duration = time.time() - start
        if duration > GUI_TEST_TIMEOUT:
            raise TimeoutException()

    exc_info = bucket[0]

    if exc_info:
        raise exc_info[1].with_traceback(exc_info[2])

    return True


# hookwrapper=True means that this function will wrap all other hook implementation
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Handle reports and chain fails for GUI tests
    """
    outcome = yield  # Retrive result of hook execution (report)
    # How does it work? Internaly it uses generator .send method, yield expressions see
    # https://docs.python.org/2.5/whatsnew/pep-342.html

    if is_gui_test(item):
        rep = outcome.get_result()

        if rep.failed and call.excinfo is not None:
            item.parent._failed = item
            if call.excinfo.errisinstance(TimeoutException):
                rep.wasxfail = "reason: Timeout"
                rep.outcome = "skipped"


def pytest_runtest_setup(item):
    """
    Handle chain fails for GUI tests
    """
    # All legacy GUI tests assume certain order of execution
    # and rely on state changes from previous steps
    # so as soon as one fails, next ones shouldn't be executed
    if is_gui_test(item):
        fail = getattr(item.parent, "_failed", None)
        if fail is not None:
            pytest.xfail("previous test has failed (%s)" % fail.name)


class GuiTestSuite:
    """
    GUI test suite runner
    poll function should be scheduled from timer for periodic updates
    """
    def __init__(self, queue: queue.Queue, shell):
        self._queue = queue
        self._shell = shell

        self._current_thread = None
        self._timeout = True
        self._shutting_down = False

    def _start_new(self):
        item, nextitem = self._queue.get()

        def test():
            item.config.hook.pytest_runtest_protocol(item=item, nextitem=nextitem)

        self._current_thread = threading.Thread(target=test)
        self._current_thread.daemon = True
        self._current_thread.start()

    def _finalize(self):
        self._shell.onQuitActionTriggered(force=True, quitApp=False)

    def poll(self):
        if self._current_thread is None:
            self._start_new()

        if not self._current_thread.is_alive():
            self._queue.task_done()

            if self._queue.empty() and not self._shutting_down:
                self._finalize()
                self._shutting_down = True

            self._current_thread = None


def pytest_runtestloop(session):
    """
    Gui test runner
    """
    if session.testsfailed and not session.config.option.continue_on_collection_errors:
        raise session.Interrupted("%d errors during collection" % session.testsfailed)

    if session.config.option.collectonly:
        return True

    # Modify session leaving only normal tests as session.items
    # Gui test should be run separately
    guitests, session.items = split_guitests(session.items)
    _pytest_runtestloop(session)

    if session.config.getoption('run_legacy_gui'):
        for tstcls, gui_test_bag in itertools.groupby(_sorted_guitests(guitests), get_guitest_cls):
            run_gui_tests(tstcls, gui_test_bag)

    else:
        warnings.warn(
            "Skipping legacy GUI test to enable please use --run-legacy-gui option\n"
        )

    return True


def run_gui_tests(tstcls, gui_test_bag):
    assert tstcls.app is None, "Should only encounter every class once. Check Sorting"
    tst_queue = queue.Queue()
    app = tstcls.app = QApplication([])
    app.setQuitOnLastWindowClosed(False)
    ThreadRouter.app_is_shutting_down = False
    app.thread_router = ThreadRouter(app)
    tstcls.shell = launchShell(None, [], [])

    platform_str = platform.platform().lower()
    if 'ubuntu' in platform_str or 'fedora' in platform_str:
        QApplication.setAttribute(Qt.AA_X11InitThreads, True)

    if ilastik.config.cfg.getboolean("ilastik", "debug"):
        QApplication.setAttribute(Qt.AA_DontUseNativeMenuBar, True)

    # Note on the class test execution lifecycle
    # pytest infers that finalizer teardown_class should be called when
    # nextitem is None
    for item, nextitem in pairwise(gui_test_bag):
        tst_queue.put((item, nextitem))

    # Spawn a suite runner as a interval task
    suite = GuiTestSuite(tst_queue, tstcls.shell)
    timer = QTimer()
    # This timer will fire only after application is started running
    timer.timeout.connect(suite.poll)
    timer.start(100)  # Every 100 ms

    app.exec_()
    timer.stop()

    tst_queue.join()


def is_gui_test(item) -> bool:
    return bool(item.get_marker('guitest'))


def split_guitests(items):
    """
    Separate GUI tests from rest of the test suite
    """
    guitests = []
    rest = []
    for item in items:
        if is_gui_test(item):
            guitests.append(item)
        else:
            rest.append(item)

    return guitests, rest


def get_guitest_cls(item):
    cls = item.getparent(pytest.Class)
    if not cls:
        raise Exception('GUI test should be inherited from ShellGuiTestCaseBase')

    return cls.obj


def _sorted_guitests(iterable):
    def _keyfunc(obj):
        cls = get_guitest_cls(obj)
        return cls.__module__, cls.__name__, obj.name

    return sorted(iterable, key=_keyfunc)


class TimeoutException(Exception):
    pass
