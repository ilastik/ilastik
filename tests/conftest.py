from pathlib import Path
import os
import shutil
import tempfile
import threading
import time
import queue
import sys
import warnings
import platform
import itertools

from concurrent import futures

import pytest
import h5py
import z5py
from PIL import Image as PilImage
import numpy

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer, Qt
from _pytest.main import pytest_runtestloop as _pytest_runtestloop

import ilastik.config

from ilastik.utility.gui.threadRouter import ThreadRouter
from ilastik.utility.itertools import pairwise
from ilastik.shell.gui.startShellGui import launchShell
from lazyflow.graph import Graph

# Every function starting with pytest_ in this module is a pytest hook
# that modifies specific behavior of test life cycle
# Useful links for understanding pytest plugins/conftest.py files.
# Writing Plugins: https://docs.pytest.org/en/3.10.1/writing_plugins.html
# Hookspec Reference: https://docs.pytest.org/en/3.10.1/_modules/_pytest/hookspec.html
# If hookspec hash @hookspec(firstresult=True) in its definition, this means
# that hooks will be executed until first not None result is found.


GUI_TEST_TIMEOUT = 120  # Seconds


@pytest.fixture(scope="session", autouse=True)
def config_app_settings(qapp):
    # Allows to map application to a specific workspace
    # useful when running tests
    qapp.setApplicationName("TestIlastik")


def pytest_addoption(parser):
    """Add command-line flags for pytest."""
    parser.addoption("--run-legacy-gui", action="store_true", help="runs legacy gui tests")


def pytest_pyfunc_call(pyfuncitem):
    """
    Defines protocol for legacy GUI test execution
    It should be run in a separate thread
    :param pyfuncitem: wrapper object around test function
    see https://docs.pytest.org/en/3.10.1/reference.html#function
    """
    if not is_gui_test(pyfuncitem):
        return

    fut = futures.Future()

    def testfunc():
        nonlocal fut
        try:
            result = pyfuncitem.obj()
            fut.set_result(result)
        except Exception as e:
            fut.set_exception(e)

    runner = threading.Thread(target=testfunc)
    runner.daemon = True
    runner.start()

    fut.result(timeout=GUI_TEST_TIMEOUT)

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

    if session.config.getoption("run_legacy_gui"):
        for tstcls, gui_test_bag in itertools.groupby(_sorted_guitests(guitests), get_guitest_cls):
            run_gui_tests(tstcls, gui_test_bag)

    elif guitests:
        warnings.warn("Skipping legacy GUI test to enable please use --run-legacy-gui option\n")

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
    if "ubuntu" in platform_str or "fedora" in platform_str:
        QApplication.setAttribute(Qt.AA_X11InitThreads, True)

    if ilastik.config.cfg.getboolean("ilastik", "debug"):
        QApplication.setAttribute(Qt.AA_DontUseNativeMenuBar, True)

    # Note on the class test execution lifecycle
    # pytest infers that finalizer teardown_class should be called when
    # nextitem is None
    for item, nextitem in pairwise(gui_test_bag, tail=None):
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
    return bool(item.get_marker("guitest"))


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
        raise Exception("GUI test should be inherited from ShellGuiTestCaseBase")

    return cls.obj


def _sorted_guitests(iterable):
    def _keyfunc(obj):
        cls = get_guitest_cls(obj)
        return cls.__module__, cls.__name__, obj.name

    return sorted(iterable, key=_keyfunc)


@pytest.fixture
def tmp_h5_single_dataset(tmp_path: Path) -> Path:
    file_path = tmp_path / "single_dataset.h5"
    with h5py.File(file_path, "w") as f:
        f.create_group("test_group")
        f["/test_group/test_data"] = numpy.random.rand(100, 200)
    return file_path


@pytest.fixture
def tmp_h5_multiple_dataset(tmp_path: Path) -> Path:
    file_path = tmp_path / "multiple_datasets.h5"
    with h5py.File(file_path, "w") as f:
        f.create_group("test_group")
        f["/test_group_2d/test_data_2d"] = numpy.random.rand(20, 30)

        f.create_group("another_test_group")
        f["/test_group_3d/test_data_3d"] = numpy.random.rand(20, 30, 3)

        f.create_group("one_more_test_group")
        f["/test_group_4d/test_data_4d"] = numpy.random.rand(20, 30, 40, 5)
    return file_path


@pytest.fixture
def tmp_n5_file(tmp_path: Path) -> Path:
    n5_dir_path = tmp_path / "my_tmp_file.n5"
    f = z5py.File(str(n5_dir_path))
    ds = f.create_dataset("data", shape=(1000, 1000), chunks=(100, 100), dtype="float32")

    # write array to a roi
    x = numpy.random.random_sample(size=(500, 500)).astype("float32")
    ds[:500, :500] = x

    # broadcast a scalar to a roi
    ds[500:, 500:] = 42.0
    f.close()

    return n5_dir_path


@pytest.fixture
def png_image(tmp_path) -> Path:
    _, filepath = tempfile.mkstemp(prefix=os.path.join(tmp_path, ""), suffix=".png")
    pil_image = PilImage.fromarray((numpy.random.rand(100, 200) * 255).astype(numpy.uint8))
    with open(filepath, "wb") as png_file:
        pil_image.save(png_file, "png")
    return Path(filepath)


@pytest.fixture
def another_png_image(tmp_path) -> Path:
    _, filepath = tempfile.mkstemp(prefix=os.path.join(tmp_path, ""), suffix=".png")
    pil_image = PilImage.fromarray((numpy.random.rand(100, 200) * 255).astype(numpy.uint8))
    with open(filepath, "wb") as png_file:
        pil_image.save(png_file, "png")
    return Path(filepath)


@pytest.fixture
def empty_project_file(tmp_path) -> h5py.File:
    project_path = tmp_path / tempfile.mkstemp(suffix=".ilp")[1]
    with h5py.File(project_path, "r+") as f:
        yield f


@pytest.fixture
def graph():
    return Graph()
