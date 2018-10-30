# ##############################################################################
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
from __future__ import division
from __future__ import absolute_import
# Standard
from future import standard_library
standard_library.install_aliases()
from builtins import range
from queue import Queue
import re
import os
import time
from functools import partial
import weakref
import logging
import platform
import threading

# SciPy
import numpy

# PyQt
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal, QObject, Qt, QUrl, QTimer
from PyQt5.QtGui import QKeySequence, QIcon, QFont, QDesktopServices, QPixmap
from PyQt5.QtWidgets import QMainWindow, QWidget, QMenu, QApplication, \
                            QStackedWidget, qApp, QFileDialog, QMessageBox, \
                            QProgressBar, QInputDialog, QToolButton, QVBoxLayout, \
                            QHBoxLayout, QSizePolicy, QLabel, QDialog, QSpinBox, \
                            QDialogButtonBox

# lazyflow
from ilastik.widgets.ipcserver.tcpServerInfoWidget import TCPServerInfoWidget
from ilastik.widgets.ipcserver.zmqPubSubInfoWidget import ZMQPublisherInfoWidget
from lazyflow.roi import TinyVector
from lazyflow.graph import Operator
import lazyflow.tools.schematic
from lazyflow.operators.cacheMemoryManager import CacheMemoryManager
from lazyflow.utility import timeLogged, isUrl
from lazyflow.request import Request

# volumina
from volumina.utility import PreferencesManager, ShortcutManagerDlg, ShortcutManager

# ilastik
from ilastik.workflow import getAvailableWorkflows, getWorkflowFromName
from ilastik.utility import bind, log_exception
from ilastik.utility.gui import ThunkEventHandler, ThreadRouter, threadRouted
from ilastik.applets.base.applet import Applet, ShellRequest
from ilastik.applets.base.appletGuiInterface import AppletGuiInterface, VolumeViewerGui
from ilastik.applets.base.singleToMultiGuiAdapter import SingleToMultiGuiAdapter
from ilastik.shell.projectManager import ProjectManager
from ilastik.config import cfg as ilastik_config
from .iconMgr import ilastikIcons
from ilastik.shell.gui.errorMessageFilter import ErrorMessageFilter
from ilastik.shell.gui.memUsageDialog import MemUsageDialog
from ilastik.shell.shellAbc import ShellABC
from ilastik.shell.headless.headlessShell import HeadlessShell

from ilastik.shell.gui.splashScreen import showSplashScreen
from ilastik.shell.gui.licenseDialog import LicenseDialog

from ilastik.widgets.appletDrawerToolBox import AppletDrawerToolBox
from ilastik.widgets.filePathButton import FilePathButton

from ilastik.shell.gui.ipcManager import IPCFacade, TCPServer, TCPClient, ZMQPublisher, ZMQSubscriber, ZMQBase
import os

# Import all known workflows now to make sure they are all registered with getWorkflowFromName()
import ilastik.workflows

try:
    import libdvid
    _has_dvid_support = True
except:
    _has_dvid_support = False

ILASTIKFont = QFont("Helvetica", 12, QFont.Bold)

logger = logging.getLogger(__name__)

#===----------------------------------------------------------------------------------------------------------------===
#=== ShellActions                                                                                                   ===
#===----------------------------------------------------------------------------------------------------------------===

class ShellActions(object):
    """
    The shell provides the applet constructors with access to his GUI actions.
    They are provided in this class.
    """

    def __init__(self):
        self.openProjectAction = None
        self.saveProjectAction = None
        self.saveProjectAsAction = None
        self.saveProjectSnapshotAction = None
        self.importProjectAction = None
        self.closeAction = None
        self.quitAction = None


#===----------------------------------------------------------------------------------------------------------------===
#=== MemoryWidget                                                                                                   ===
#===----------------------------------------------------------------------------------------------------------------===

class MemoryWidget(QWidget):
    """Displays the current memory consumption and a button to open
       a detailed memory consumption / usage dialog.
    """

    def __init__(self, parent=None):
        super(MemoryWidget, self).__init__(parent)
        self.label = QLabel()
        h = QHBoxLayout()
        h.setContentsMargins(0, 0, 0, 0)
        w = QWidget()
        h.addWidget(self.label)
        self.showDialogButton = QToolButton()
        self.showDialogButton.setText("...")
        h.addWidget(self.showDialogButton)
        self.cleanUp()
        self.setLayout(h)

    def cleanUp(self):
        self.setMemoryBytes(0)

    def setMemoryBytes(self, bytes):
        self.label.setText("Cached Data: %1.1f MB" % (bytes / (1024.0 ** 2.0)))


#===----------------------------------------------------------------------------------------------------------------===
#=== ProgressDisplayManager                                                                                         ===
#===----------------------------------------------------------------------------------------------------------------===

class ProgressDisplayManager(QObject):
    """
    Manages progress signals from applets and displays them in the status bar.
    """
    # Instead of connecting to applet progress signals directly,
    # we forward them through this qt signal.
    # This way we get the benefits of a queued connection without
    #  requiring the applet interface to be dependent on qt.
    dispatchSignal = pyqtSignal(int, int, "bool")

    def __init__(self, statusBar):
        """
        """
        super(ProgressDisplayManager, self).__init__(parent=statusBar.parent())
        self.statusBar = statusBar
        self.appletPercentages = {}  # applet_index : percent_progress
        self.workflow = None

        self.progressBar = QProgressBar()
        self.statusBar.addWidget(self.progressBar)
        self.progressBar.setHidden(True)

        self.requestStatus = QLabel()
        self.requestTimer = QTimer()
        self.requestTimer.setInterval(1000)
        def update_request_count():
            msg = "Active Requests: {}".format( Request.active_count )
            self.requestStatus.setText(msg)
        self.requestTimer.timeout.connect( update_request_count )
        self.requestTimer.start()

        self.statusBar.addPermanentWidget(self.requestStatus)
        
        self.memoryWidget = MemoryWidget()
        self.memoryWidget.showDialogButton.clicked.connect(self.parent().showMemUsageDialog)
        self.statusBar.addPermanentWidget(self.memoryWidget)

        mgr = CacheMemoryManager()

        def printIt(msg):
            self.memoryWidget.setMemoryBytes(msg)

        mgr.totalCacheMemory.subscribe(printIt)

        # Route all signals we get through a queued connection, 
        #  to ensure that they are handled in the GUI thread
        # Important: AutoConnection (the default type) is not okay here: that would cause 
        #            progress signals coming from the main thread to "cut in line"  
        #            in front of progress notifications that were previously sent, 
        #            but from other threads.
        self.dispatchSignal.connect(self.handleAppletProgressImpl, Qt.QueuedConnection)

    def initializeForWorkflow(self, workflow):
        """When a workflow is available, call this method to connect the workflows' progress signals
        """
        for index, app in enumerate(workflow.applets):
            self._addApplet(index, app)

    def cleanUp(self):
        # Disconnect everything
        if self.workflow is not None:
            for index, app in enumerate(self.workflow.applets):
                self._removeApplet(index, app)
        self.memoryWidget.cleanUp()
        self.progressBar.hide()

    def _removeApplet(self, index, app):
        app.progressSignal.clean()
        for serializer in app.dataSerializers:
            serializer.progressSignal.clean()

    def _addApplet(self, index, app):
        # Subscribe to progress updates from this applet,
        # and include the applet index in the signal parameters.
        app.progressSignal.subscribe(bind(self.handleAppletProgress, index))

        # Also subscribe to this applet's serializer progress updates.
        # (Progress will always come from either the serializer or the applet itself; not both at once.)
        for serializer in app.dataSerializers:
            serializer.progressSignal.subscribe(bind(self.handleAppletProgress, index))

    def handleAppletProgress(self, index, percentage, cancelled=False):
        # Forward the signal to the handler via our qt signal, which provides a queued connection.
        self.dispatchSignal.emit(index, percentage, cancelled)

    def handleAppletProgressImpl(self, index, percentage, cancelled):
        # No need for locking; this function is always run from the GUI thread
        if cancelled:
            if index in list(self.appletPercentages.keys()):
                del self.appletPercentages[index]
        else:
            # Take max (never go back down)
            if index in self.appletPercentages:
                oldPercentage = self.appletPercentages[index]
                self.appletPercentages[index] = max(percentage, oldPercentage)
            # First percentage we get MUST be 0 or -1.
            # Other notifications are ignored.
            if index in self.appletPercentages or percentage == 0 or percentage == -1:
                self.appletPercentages[index] = percentage

        numActive = len(self.appletPercentages)
        if numActive > 0:
            totalPercentage = numpy.sum(list(self.appletPercentages.values())) // numActive

        # If any applet gave -1, put progress bar in "busy indicator" mode
        if (TinyVector(list(self.appletPercentages.values())) == -1).any():
            self.progressBar.setMaximum(0)
        else:
            self.progressBar.setMaximum(100)

        if numActive == 0 or totalPercentage == 100:
            self.progressBar.setHidden(True)
            self.appletPercentages.clear()
        else:
            self.progressBar.setHidden(False)
            self.progressBar.setValue(totalPercentage)


#===----------------------------------------------------------------------------------------------------------------===
#=== IlastikShell                                                                                                   ===
#===----------------------------------------------------------------------------------------------------------------===

def styleStartScreenButton(button, icon):
    assert isinstance(button, QToolButton)
    button.setAutoRaise(True)
    button.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
    button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
    button.setIcon(QIcon(icon))


class IlastikShell(QMainWindow):
    """
    The GUI's main window.  Simply a standard 'container' GUI for one or more applets.
    """
    currentAppletChanged = pyqtSignal(int, int) # prev, current

    def __init__(self, parent=None, workflow_cmdline_args=None, flags=Qt.WindowFlags(0)):
        QMainWindow.__init__(self, parent=parent, flags=flags)
        #self.setFixedSize(1680,1050) #ilastik manuscript resolution
        # Register for thunk events (easy UI calls from non-GUI threads)
        self.thunkEventHandler = ThunkEventHandler(self)

        # Server/client for inter process communication for receiving remote commands (e.g. from KNIME)
        # For now, this is a developer-only feature, activated by a debug menu item.
        if ilastik_config.getboolean("ilastik", "debug"):
            facade = IPCFacade()
            facade.register_shell(self)
            facade.register_widget(TCPServerInfoWidget(), "TCP Connection", "raw tcp")
            interface = ilastik_config.get("ipc raw tcp", "interface")
            port = ilastik_config.getint("ipc raw tcp", "port")
            start = ilastik_config.getboolean("ipc raw tcp", "autostart")
            facade.register_module(TCPServer(interface, port), "receiver", "raw tcp server", "raw tcp", start=start)
            facade.register_module(TCPClient(), "sender", "raw tcp client", "raw tcp", "tcp")

            if ZMQBase.available("tcp"):
                facade.register_widget(ZMQPublisherInfoWidget(), "ZeroMQ Pub Sub TCP", "zmq tcp")
                start = ilastik_config.getboolean("ipc zmq tcp publisher", "autostart")
                address = ilastik_config.get("ipc zmq tcp publisher", "address")
                facade.register_module(ZMQPublisher("tcp", address), "sender", "zmq tcp pub", "zmq tcp", start=start)
                start = ilastik_config.getboolean("ipc zmq tcp subscriber", "autostart")
                address = ilastik_config.get("ipc zmq tcp subscriber", "address")
                facade.register_module(ZMQSubscriber("tcp", address), "receiver", "zmq tcp sub", "zmq tcp",
                                       start=start)

                if ZMQBase.available("ipc"):
                    base_dir = ilastik_config.get("ipc zmq ipc", "basedir")
                    can_start = True
                    try:
                        os.mkdir(base_dir)
                    except OSError as e:
                        if e.errno != 17:  # exists
                            can_start = False
                    if can_start:
                        facade.register_widget(ZMQPublisherInfoWidget(), "ZeroMQ Pub Sub IPC", "zmq ipc")
                        start = ilastik_config.getboolean("ipc zmq ipc publisher", "autostart")
                        filename = ilastik_config.get("ipc zmq ipc publisher", "filename")
                        path = os.path.join(base_dir, filename)
                        facade.register_module(ZMQPublisher("ipc", path), "sender", "zmq ipc pub",
                                               "zmq ipc", start=start)
                        start = ilastik_config.getboolean("ipc zmq ipc subscriber", "autostart")
                        filename = ilastik_config.get("ipc zmq ipc subscriber", "filename")
                        path = os.path.join(base_dir, filename)
                        facade.register_module(ZMQSubscriber("ipc", path), "receiver", "zmq ipc sub",
                                               "zmq ipc", start=start)

        self.openFileButtons = []
        self.cleanupFunctions = []

        self._workflow_cmdline_args = workflow_cmdline_args

        self.projectManager = None
        self.projectDisplayManager = None

        self._loaduifile()

        assert isinstance(self.appletBar, AppletDrawerToolBox)

        # show a nice window icon
        self.setWindowIcon(QIcon(ilastikIcons.Ilastik))

        self.progressDisplayManager = ProgressDisplayManager(self.statusBar)

        #self.appletBar.setExpandsOnDoubleClick(False) #bug 193.
        #self.appletBar.setSelectionMode(QAbstractItemView.NoSelection)

        self._memDlg = None  #this will hold the memory usage dialog once created

        self.imageSelectionGroup.setHidden(True)

        self.setAttribute(Qt.WA_AlwaysShowToolTips)

        if ilastik_config.getboolean("ilastik", "debug") or 'Ubuntu' in platform.platform():
            # Native menus are prettier, but aren't working on Ubuntu at this time (Qt 4.7, Ubuntu 11)
            # Navive menus also required for event-recorded tests
            self.menuBar().setNativeMenuBar(False)

        (self._projectMenu, self._shellActions) = self._createProjectMenu()
        self._settingsMenu = self._createSettingsMenu()
        if ilastik_config.getboolean("ilastik", "debug"):
            self._debugMenu = self._createDebugMenu()
        self._helpMenu = self._createHelpMenu()
        self.menuBar().addMenu(self._projectMenu)
        if self._settingsMenu is not None:
            self.menuBar().addMenu(self._settingsMenu)
        if ilastik_config.getboolean("ilastik", "debug"):
            self.menuBar().addMenu(self._debugMenu)
        self.menuBar().addMenu(self._helpMenu)

        assert self.thread() == QApplication.instance().thread()
        assert self.menuBar().thread() == self.thread()
        assert self._projectMenu.thread() == self.thread()
        if self._settingsMenu is not None:
            assert self._settingsMenu.thread() == self.thread()

        self.appletBar.currentChanged.connect(self.handleAppletBarItemExpanded)
        #self.appletBar.setVerticalScrollMode( QAbstractItemView.ScrollPerPixel )

        self.currentAppletIndex = 0

        self._currentImageIndex = -1
        self.populatingImageSelectionCombo = False
        self.imageSelectionCombo.currentIndexChanged.connect(self.changeCurrentInputImageIndex)

        self.enableWorkflow = False  # Global mask applied to all applets
        self._controlCmds = []  # Track the control commands that have been issued by each applet so they can be popped.
        self._disableCounts = []  # Controls for each applet can be disabled by his peers.
        # No applet can be enabled unless his disableCount == 0

        self._refreshDrawerRecursionGuard = False
        
        self._applet_enabled_states = {}

        self.setupOpenFileButtons()
        self.updateShellProjectDisplay()

        self.threadRouter = ThreadRouter(self)  # Enable @threadRouted

        self.errorMessageFilter = ErrorMessageFilter(self)

        frame_geometry = PreferencesManager().get("shell", "startscreenGeometry")
        if frame_geometry is not None:
            x, y, w, h = frame_geometry
            self.move(x, y)

            # The frameGeometry() function doesn't actually include the
            #  window frame padding until the window has been shown at least once.
            # Hence, show it now before doing our calculations.
            self.show()

            # Qt offers no function for setting the size of the entire frame, 
            # so instead we have to calculate the target size of the internal geometry.            
            frame_padding_width = self.frameGeometry().width() - self.geometry().size().width()
            frame_padding_height = self.frameGeometry().height() - self.geometry().size().height()
            self.resize(w - frame_padding_width, h - frame_padding_height)

        self._initShortcuts()

    def _initShortcuts(self):
        mgr = ShortcutManager()
        ActionInfo = ShortcutManager.ActionInfo
        shortcutGroupName = "Ilastik Shell"

        mgr.register("PgDown", ActionInfo(shortcutGroupName,
                                          "shell next image",
                                          "Switch to next image",
                                          self._nextImage,
                                          self,
                                          self.imageSelectionCombo))

        mgr.register("PgUp", ActionInfo(shortcutGroupName,
                                        "shell previous image",
                                        "Switch to previous image",
                                        self._prevImage,
                                        self,
                                        None))

    def _nextImage(self):
        newIndex = min(self.imageSelectionCombo.count() - 1, self.imageSelectionCombo.currentIndex() + 1)
        self.imageSelectionCombo.setCurrentIndex(newIndex)

    def _prevImage(self):
        newIndex = max(0, self.imageSelectionCombo.currentIndex() - 1)
        self.imageSelectionCombo.setCurrentIndex(newIndex)

    @property
    def _applets(self):
        if self.projectManager is None or self.projectManager.workflow is None:
            return []
        else:
            return self.projectManager.workflow.applets

    @property
    def workflow(self):
        return self.projectManager and self.projectManager.workflow

    def loadWorkflow(self, workflow_class):
        self.onNewProjectActionTriggered(workflow_class)

    def getWorkflow(self, w=None):

        listOfItems = [workflowDisplayName for _, __, workflowDisplayName in getAvailableWorkflows()]
        if w is not None and w in listOfItems:
            cur = listOfItems.index(w)
        else:
            cur = 0

        res, ok = QInputDialog.getItem(self,
                                       "Workflow Selection",
                                       "Select a workflow which should open the file.",
                                       listOfItems,
                                       cur,
                                       False)

        if ok:
            return getWorkflowFromName(str(res))

    def _createProjectMenu(self):
        # Create a menu for "General" (non-applet) actions
        menu = QMenu("&Project", self)
        menu.setObjectName("project_menu")

        shellActions = ShellActions()

        # Menu item: Open Project
        shellActions.openProjectAction = menu.addAction("&Open Project...")
        shellActions.openProjectAction.setIcon(QIcon(ilastikIcons.Open))
        shellActions.openProjectAction.setShortcuts(QKeySequence.Open)
        shellActions.openProjectAction.triggered.connect(self.onOpenProjectActionTriggered)

        # Menu item: Save Project
        shellActions.saveProjectAction = menu.addAction("&Save Project")
        shellActions.saveProjectAction.setIcon(QIcon(ilastikIcons.Save))
        shellActions.saveProjectAction.setShortcuts(QKeySequence.Save)
        shellActions.saveProjectAction.triggered.connect(self.onSaveProjectActionTriggered)

        # Menu item: Save Project As
        shellActions.saveProjectAsAction = menu.addAction("&Save Project As...")
        shellActions.saveProjectAsAction.setIcon(QIcon(ilastikIcons.SaveAs))
        shellActions.saveProjectAsAction.setShortcuts(QKeySequence.SaveAs)
        shellActions.saveProjectAsAction.triggered.connect(self.onSaveProjectAsActionTriggered)

        # Menu item: Save Project Snapshot
        shellActions.saveProjectSnapshotAction = menu.addAction("Save Copy as...")
        shellActions.saveProjectSnapshotAction.setIcon(QIcon(ilastikIcons.SaveAs))
        shellActions.saveProjectSnapshotAction.triggered.connect(self.onSaveProjectSnapshotActionTriggered)

        # Menu item: Import Project
        shellActions.importProjectAction = menu.addAction("&Import Project...")
        shellActions.importProjectAction.setIcon(QIcon(ilastikIcons.Open))
        shellActions.importProjectAction.triggered.connect(self.onImportProjectActionTriggered)

        # Menu item: Download from DVID
        if _has_dvid_support:
            shellActions.downloadProjectFromDvidAction = menu.addAction("&Download Project from DVID...")
            shellActions.downloadProjectFromDvidAction.setIcon(QIcon(ilastikIcons.Open))
            shellActions.downloadProjectFromDvidAction.triggered.connect(self.onDownloadProjectFromDvidActionTriggered)    

        shellActions.closeAction = menu.addAction("&Close")
        shellActions.closeAction.setIcon(QIcon(ilastikIcons.ProcessStop))
        shellActions.closeAction.setShortcuts(QKeySequence.Close)
        shellActions.closeAction.triggered.connect(self.onCloseActionTriggered)

        # Menu item: Quit
        shellActions.quitAction = menu.addAction("&Quit")
        shellActions.quitAction.setShortcuts(QKeySequence.Quit)
        shellActions.quitAction.setIcon(QIcon(ilastikIcons.ProcessStop))
        shellActions.quitAction.triggered.connect(self.onQuitActionTriggered)
        shellActions.quitAction.setShortcut(QKeySequence.Quit)

        return (menu, shellActions)

    def setupOpenFileButtons(self):

        for b in self.openFileButtons:
            b.close()
            b.deleteLater()
        self.openFileButtons = []

        projects = PreferencesManager().get("shell", "recently opened list")

        if projects is not None:
            # (projects is already sorted from most-recent to least-recent.)
            for path, workflow in projects:
                if not os.path.exists(path):
                    continue
                b = FilePathButton(path, " ({})".format(workflow), parent=self.startscreen)
                styleStartScreenButton(b, ilastikIcons.Open)

                b.clicked.connect(partial(self.openFileAndCloseStartscreen, path))

                # Insert the new button after all the other controls, 
                #  but before the vertical spacer at the end of the list.
                insertion_index = self.startscreen.VL1.count() - 1
                self.startscreen.VL1.insertWidget(insertion_index, b)
                self.openFileButtons.append(b)

    def _replaceLogo(self, localDir):
        '''
        Replaces the ilastik logo with fun alternatives on special days
        '''
        from datetime import date
        d = date.today()
        if (d.month == 10 and d.day > 29) or (d.month == 11 and d.day < 2):
            import codecs
            enc = codecs.getencoder( "rot-13" )
            key = 'vynfgvxunyybjrra'
            clearkey = enc( key )[0].encode()

            import zipfile
            import tempfile
            
            with tempfile.TemporaryDirectory() as tmp_dir:
                with zipfile.ZipFile(os.path.join(localDir, 'ilastik-logo-alternative.zip'), 'r') as z:
                    z.setpassword(clearkey)
                    filename = z.namelist()[0]
                    z.extract(filename, tmp_dir)

                    fullPath = os.path.join(tmp_dir, filename)
                    self.startscreen.label.setPixmap(QPixmap(fullPath))
                    os.remove(fullPath)

    def _loaduifile(self):
        localDir = os.path.split(__file__)[0]
        if localDir == "": localDir = os.getcwd()

        self.startscreen = uic.loadUi(localDir + "/ui/ilastikShell.ui", self)

        self.startscreen.CreateList.setWidget(self.startscreen.VL1.widget())
        self.startscreen.CreateList.setWidgetResizable(True)

        self.startscreen.openRecentProject.setFont(ILASTIKFont)
        self.startscreen.openProject.setFont(ILASTIKFont)
        self._replaceLogo(localDir)
        self.startscreen.createNewProject.setFont(ILASTIKFont)

        self.openFileButtons = []

        styleStartScreenButton(self.startscreen.browseFilesButton, ilastikIcons.OpenFolder)
        self.startscreen.browseFilesButton.clicked.connect(self.onOpenProjectActionTriggered)

        pos = 1
        for workflow, _name, displayName in getAvailableWorkflows():
            b = QToolButton(self.startscreen, objectName="NewProjectButton_" + workflow.__name__)
            styleStartScreenButton(b, ilastikIcons.GoNext)
            b.setText(displayName)
            b.clicked.connect(partial(self.loadWorkflow, workflow))
            self.startscreen.VL1.insertWidget(pos, b)
            pos += 1

    def openFileAndCloseStartscreen(self, path):
        if self.projectManager is not None:
            # If the user double-clicked a "recent project" button,
            #  then this handler function might get called twice.
            # In that case, just ignore the second click.
            return
        #self.startscreen.setParent(None)
        #del self.startscreen
        self.openProjectFile(path)

    def _createHelpMenu(self):
        menu = QMenu("&Help", self)
        menu.setObjectName("help_menu")
        aboutIlastikAction = menu.addAction("&About ilastik")
        aboutIlastikAction.triggered.connect(showSplashScreen)
        licenseAction = menu.addAction("License")
        licenseAction.triggered.connect(partial(LicenseDialog, self))
        return menu

    def _createDebugMenu(self):
        menu = QMenu("&Debug", self)
        menu.setObjectName("debug_menu")

        detail_levels = [('Lowest', 0), ('Some', 1), ('More', 2), ('Even More', 3), ('Unlimited', 100)]
        exportDebugSubmenu = menu.addMenu("Export Operator Diagram")
        exportWorkflowSubmenu = menu.addMenu("Export Workflow Diagram")
        for name, level in detail_levels:
            exportDebugSubmenu.addAction(name).triggered.connect(partial(self.exportCurrentOperatorDiagram, level))
            exportWorkflowSubmenu.addAction(name).triggered.connect(partial(self.exportWorkflowDiagram, level))

        menu.addAction("&Memory usage").triggered.connect(self.showMemUsageDialog)
        menu.addMenu(self._createProfilingSubmenu())

        menu.addMenu(self._createAllocationTrackingSubmenu())

        menu.addAction("Show IPC Server Info", IPCFacade().show_info)

        def hideApplets(hideThem):
            self.mainSplitter.setVisible(not hideThem)
        hide = menu.addAction("Hide applets")
        hide.setCheckable(True)
        hide.toggled.connect(hideApplets)

        return menu

    def _createProfilingSubmenu(self):
        try:
            import yappi

            has_yappi = True
        except ImportError:
            has_yappi = False

        def _updateMenuStatus():
            startAction.setEnabled(not yappi.is_running())
            stopAction.setEnabled(yappi.is_running())
            for action in sortedExportSubmenu.actions():
                action.setEnabled(not yappi.is_running() and not yappi.get_func_stats().empty())
            for action in sortedThreadExportSubmenu.actions():
                action.setEnabled(not yappi.is_running() and not yappi.get_func_stats().empty())

        def _startProfiling():
            logger.info("Activating new profiler")
            yappi.clear_stats()
            yappi.start()
            _updateMenuStatus()

        def _stopProfiling():
            logger.info("Dectivating profiler...")
            yappi.stop()
            logger.info("...profiler deactivated")
            _updateMenuStatus()

        def _exportSortedStats(sortby):
            assert not yappi.is_running()

            filename = 'ilastik_profile_sortedby_{}.txt'.format(sortby)
            recentPath = PreferencesManager().get('shell', 'recent sorted profile stats')
            if recentPath is None:
                defaultPath = os.path.join(os.path.expanduser('~'), filename)
            else:
                defaultPath = os.path.join(os.path.split(recentPath)[0], filename)
            stats_path, _filter = QFileDialog.getSaveFileName(
                self, "Export sorted stats text", defaultPath, "Text files (*.txt)",
                options=QFileDialog.Options(QFileDialog.DontUseNativeDialog))

            if stats_path:
                pstats_path = os.path.splitext(stats_path)[0] + '.pstats'
                PreferencesManager().set('shell', 'recent sorted profile stats', stats_path)

                # Export the yappi stats to builtin pstats format, 
                #  since pstats provides nicer printing IMHO
                stats = yappi.get_func_stats()
                stats.save(pstats_path, type='pstat')
                with open(stats_path, 'w') as f:
                    import pstats

                    ps = pstats.Stats(pstats_path, stream=f)
                    ps.sort_stats(sortby)
                    ps.print_stats()
                logger.info("Printed stats to file: {}".format(stats_path))
                # As a convenience, go ahead and open it.
                QDesktopServices.openUrl(QUrl.fromLocalFile(stats_path))

        def _exportSortedThreadStats(sortby):
            assert not yappi.is_running()

            filename = 'ilastik_threadstats_sortedby_{}.txt'.format(sortby)

            recentPath = PreferencesManager().get('shell', 'recent sorted profile stats')
            if recentPath is None:
                defaultPath = os.path.join(os.path.expanduser('~'), filename)
            else:
                defaultPath = os.path.join(os.path.split(recentPath)[0], filename)
            stats_path, _filter = QFileDialog.getSaveFileName(
                self, "Export sorted stats text", defaultPath, "Text files (*.txt)",
                options=QFileDialog.Options(QFileDialog.DontUseNativeDialog))

            if stats_path:
                PreferencesManager().set('shell', 'recent sorted profile stats', stats_path)

                # Export the yappi stats to builtin pstats format, 
                #  since pstats provides nicer printing IMHO
                stats = yappi.get_thread_stats()
                stats.sort(sortby)
                with open(stats_path, 'w') as f:
                    stats.print_all(f)
                logger.info("Printed thread stats to file: {}".format(stats_path))
                # As a convenience, go ahead and open it.
                QDesktopServices.openUrl(QUrl.fromLocalFile(stats_path))

        profilingSubmenu = QMenu("Profiling")
        if not has_yappi:
            self._profilingSubmenu = profilingSubmenu
            errorMsgAction = self._profilingSubmenu.addAction("<yappi module not installed>")
            errorMsgAction.setEnabled(False)
            return self._profilingSubmenu

        startAction = profilingSubmenu.addAction("Start (reset)")
        startAction.triggered.connect(_startProfiling)
        startAction.setIcon(QIcon(ilastikIcons.Record))

        stopAction = profilingSubmenu.addAction("Stop")
        stopAction.triggered.connect(_stopProfiling)
        stopAction.setIcon(QIcon(ilastikIcons.Stop))

        sortedExportSubmenu = profilingSubmenu.addMenu("Save Sorted Stats...")
        for sortby in ['calls', 'cumulative', 'filename', 'pcalls', 'line', 'name', 'nfl', 'stdname', 'time']:
            action = sortedExportSubmenu.addAction(sortby)
            action.triggered.connect(partial(_exportSortedStats, sortby))

        sortedThreadExportSubmenu = profilingSubmenu.addMenu("Save Sorted Thread Stats...")
        for sortby in ['name', 'id', 'totaltime', 'schedcount']:
            action = sortedThreadExportSubmenu.addAction(sortby)
            action.triggered.connect(partial(_exportSortedThreadStats, sortby))

        _updateMenuStatus()

        # Must retain this reference, otherwise the menu gets automatically removed
        self._profilingSubmenu = profilingSubmenu
        return profilingSubmenu

    def _createAllocationTrackingSubmenu(self):
        self._allocation_threshold = PreferencesManager().get('shell', 'allocation tracking threshold')
        if self._allocation_threshold is None:
            self._allocation_threshold = 1000000 # 1 MB by default
        
        self._traceback_depth = PreferencesManager().get('shell', 'allocation tracking traceback depth')
        if self._traceback_depth is None:
            self._traceback_depth = 3 # default

        # Must retain this reference, otherwise the menu gets automatically removed
        allocationTrackingSubmenu = QMenu("Numpy Allocation Tracking")
        self._allocationTrackingSubmenu = allocationTrackingSubmenu

        try:
            from numpy_allocation_tracking import PrettyAllocationTracker
        except ImportError:
            errMsgAction = allocationTrackingSubmenu.addAction("Not installed. Please try:"
                                                               "  conda install -c ilastik numpy-allocation-tracking")
            errMsgAction.setEnabled(False)
            return allocationTrackingSubmenu

        def _configureSettings():
            dlg = QDialog(windowTitle="Allocation Tracking Settings")

            threshold_box = QSpinBox(minimum=1, maximum=1000000000, suffix=' bytes')
            threshold_box.setValue(self._allocation_threshold)

            threshold_layout = QHBoxLayout()
            threshold_layout.addWidget(QLabel("Allocation Threshold"))
            threshold_layout.addWidget(threshold_box)

            traceback_depth_box = QSpinBox(minimum=1, maximum=100, suffix=' frames')
            traceback_depth_box.setValue(self._traceback_depth)

            traceback_layout = QHBoxLayout()
            traceback_layout.addWidget(QLabel("Displayed Stack Frames"))
            traceback_layout.addWidget(traceback_depth_box)

            buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            buttons.accepted.connect( dlg.accept )
            buttons.rejected.connect( dlg.reject )

            layout = QVBoxLayout()
            layout.addLayout(threshold_layout)
            layout.addLayout(traceback_layout)
            layout.addWidget( buttons )

            dlg.setLayout(layout)
            if dlg.exec_() == QDialog.Accepted:
                self._allocation_threshold = threshold_box.value()
                PreferencesManager().set('shell', 'allocation tracking threshold', self._allocation_threshold)

                self._traceback_depth = traceback_depth_box.value()
                PreferencesManager().set('shell', 'allocation tracking traceback depth', self._traceback_depth)

        def _startAllocationTracking():
            self._allocation_tracker = PrettyAllocationTracker(self._allocation_threshold, self._traceback_depth)
            self._allocation_tracker.__enter__()
            startAction.setEnabled(False)
            stopAction.setEnabled(True)

        def _stopAllocationTracking():
            self._allocation_tracker.__exit__(None, None, None)
            startAction.setEnabled(True)
            stopAction.setEnabled(False)

            filename = 'ilastik-tracked-numpy-allocations.html'
            recentPath = PreferencesManager().get('shell', 'allocation tracking output html')
            if recentPath is None:
                defaultPath = os.path.join(os.path.expanduser('~'), filename)
            else:
                defaultPath = os.path.join(os.path.split(recentPath)[0], filename)
            
            html_path, _filter = QFileDialog.getSaveFileName(
                self, "Export allocation tracking table", defaultPath, "HTML files (*.html)",
                options=QFileDialog.Options(QFileDialog.DontUseNativeDialog))

            if html_path:
                PreferencesManager().set('shell', 'allocation tracking output html', html_path)
                self._allocation_tracker.write_html(html_path)

                # As a convenience, go ahead and open it.
                QDesktopServices.openUrl(QUrl.fromLocalFile(html_path))
        
        startAction = allocationTrackingSubmenu.addAction("Start")
        startAction.triggered.connect(_startAllocationTracking)
        startAction.setIcon(QIcon(ilastikIcons.Record))

        stopAction = allocationTrackingSubmenu.addAction("Stop")
        stopAction.triggered.connect(_stopAllocationTracking)
        stopAction.setEnabled(False)
        stopAction.setIcon(QIcon(ilastikIcons.Stop))

        configureAction = allocationTrackingSubmenu.addAction("Configure...")
        configureAction.triggered.connect(_configureSettings)
        
        return allocationTrackingSubmenu

    def showMemUsageDialog(self):
        if self._memDlg is None:
            self._memDlg = MemUsageDialog()
            self._memDlg.setWindowTitle("Memory Usage")
            self._memDlg.show()
        else:
            self._memDlg.show()
            self._memDlg.raise_()

    def _createSettingsMenu(self):
        menu = QMenu("Settings", self)
        menu.setObjectName("settings_menu")
        # Menu item: Keyboard Shortcuts

        def editShortcuts():
            mgrDlg = ShortcutManagerDlg(self)

        menu.addAction("&Keyboard Shortcuts").triggered.connect(editShortcuts)

        return menu

    def exportCurrentOperatorDiagram(self, detail):
        if len(self._applets) == 0:
            QMessageBox.critical(self, "Export Error", "There are no operators to export.")
            return
        elif len(self._applets) <= self.currentAppletIndex:
            QMessageBox.critical(self, "Export Error", "The current applet does not exist.")
            return
        op = self._applets[self.currentAppletIndex].topLevelOperator
        assert isinstance(op,
                          Operator), "Top-level operator of your applet must be a lazyflow.Operator if you want to export it!"
        self.exportOperatorDiagram(op, detail)

    def exportWorkflowDiagram(self, detail):
        if self.projectManager is None:
            QMessageBox.critical(self, "Export Error",
                                 "You have to start a project before you can export workflow diagrams.")
            return
        assert isinstance(self.projectManager.workflow,
                          Operator), "Workflow must be an operator if you want to export it!"
        self.exportOperatorDiagram(self.projectManager.workflow, detail)

    def exportOperatorDiagram(self, op, detail):
        recentPath = PreferencesManager().get('shell', 'recent debug diagram')
        if recentPath is None:
            defaultPath = os.path.join(os.path.expanduser('~'), op.name + '.svg')
        else:
            defaultPath = os.path.join(os.path.split(recentPath)[0], op.name + '.svg')

        svgPath, _filter = QFileDialog.getSaveFileName(
            self, "Save operator diagram", defaultPath, "Inkscape Files (*.svg)",
            options=QFileDialog.Options(QFileDialog.DontUseNativeDialog))

        if svgPath:
            PreferencesManager().set('shell', 'recent debug diagram', svgPath)
            lazyflow.tools.schematic.generateSvgFileForOperator(svgPath, op, detail)
            QDesktopServices.openUrl(QUrl.fromLocalFile(svgPath))

    def show(self):
        """
        Show the window, and enable/disable controls depending on whether or not a project file present.
        """
        super(IlastikShell, self).show()
        self.enableWorkflow = (self.projectManager is not None)
        self.updateShellProjectDisplay()
        # Default to a 50-50 split
        totalSplitterHeight = sum(self.sideSplitter.sizes())
        self.sideSplitter.setSizes([totalSplitterHeight / 2, totalSplitterHeight / 2])

    def updateShellProjectDisplay(self):
        """
        Update the title bar and allowable shell actions based on the state of the currently loaded project.
        """
        windowTitle = "ilastik - "
        if self.projectManager is None or self.projectManager.closed:
            windowTitle += "No Project Loaded"
        else:
            windowTitle += self.projectManager.currentProjectPath + " - "
            if self.projectManager.workflow.workflowDisplayName is not None:
                windowTitle += self.projectManager.workflow.workflowDisplayName
            else:
                windowTitle += self.projectManager.workflow.workflowName

            readOnly = self.projectManager.currentProjectIsReadOnly
            if readOnly:
                windowTitle += " [Read Only]"

        self.setWindowTitle(windowTitle)

        # Enable/Disable menu items
        projectIsOpen = self.projectManager is not None and not self.projectManager.closed
        self._shellActions.saveProjectAction.setEnabled(
            projectIsOpen and not readOnly)  # Can't save a read-only project
        self._shellActions.saveProjectAsAction.setEnabled(projectIsOpen)
        self._shellActions.saveProjectSnapshotAction.setEnabled(projectIsOpen)
        if self._shellActions.closeAction is not None:
            self._shellActions.closeAction.setEnabled(projectIsOpen)

    def setImageNameListSlot(self, multiSlot):
        assert multiSlot.level == 1
        self.imageNamesSlot = multiSlot
        self.cleanupFunctions = []

        insertedCallback = bind(self.handleImageNameSlotInsertion)
        self.cleanupFunctions.append(partial(multiSlot.unregisterInserted, insertedCallback))
        multiSlot.notifyInserted(insertedCallback)

        removeCallback = bind(self.handleImageNameSlotRemoval)
        self.cleanupFunctions.append(partial(multiSlot.unregisterRemove, removeCallback))
        multiSlot.notifyRemove(bind(self.handleImageNameSlotRemoval))

        # Update for the slots that already exist
        for index, slot in enumerate(multiSlot):
            self.handleImageNameSlotInsertion(multiSlot, index)
            self.insertImageName(index, slot)

    @threadRouted
    def insertImageName(self, index, slot):
        assert threading.current_thread().name == "MainThread"
        if slot.ready():
            self.imageSelectionCombo.setItemText(index, slot.value)
            if self.currentImageIndex == -1:
                self.changeCurrentInputImageIndex(index)

    @threadRouted
    def handleImageNameSlotInsertion(self, multislot, index):
        assert threading.current_thread().name == "MainThread"
        assert multislot == self.imageNamesSlot
        self.populatingImageSelectionCombo = True
        self.imageSelectionCombo.insertItem(index, "uninitialized")
        self.populatingImageSelectionCombo = False
        multislot[index].notifyDirty(bind(self.insertImageName, index))

    @threadRouted
    def handleImageNameSlotRemoval(self, multislot, index):
        assert threading.current_thread().name == "MainThread"
        # Simply remove the combo entry, which causes the currentIndexChanged signal to fire if necessary.
        self.imageSelectionCombo.removeItem(index)
        if len(multislot) == 0:
            self.changeCurrentInputImageIndex(-1)

    @timeLogged(logger, logging.DEBUG)
    def changeCurrentInputImageIndex(self, newImageIndex):
        if newImageIndex != self.currentImageIndex \
                and self.populatingImageSelectionCombo == False:
            if newImageIndex != -1:
                try:
                    # Accessing the image name value will throw if it isn't properly initialized
                    self.imageNamesSlot[newImageIndex].value
                except:
                    # Revert to the original image index.
                    if self.currentImageIndex != -1:
                        assert threading.current_thread().name == "MainThread"
                        self.imageSelectionCombo.setCurrentIndex(self.currentImageIndex)
                    return

            # Alert each central widget and viewer control widget that the image selection changed
            for i in range(len(self._applets)):
                if newImageIndex == -1:
                    self._applets[i].getMultiLaneGui().setImageIndex(None)
                else:
                    self._applets[i].getMultiLaneGui().setImageIndex(newImageIndex)

            self._currentImageIndex = newImageIndex

            if self.currentImageIndex != -1:
                # Force the applet drawer to be redrawn
                self.setSelectedAppletDrawer(self.currentAppletIndex)

                # Update all other applet drawer titles
                for applet_index, app in enumerate(self._applets):
                    updatedDrawerTitle = app.name
                    self.appletBar.setItemText(applet_index, updatedDrawerTitle)

    @property
    def currentImageIndex(self):
        return self._currentImageIndex
    
    def handleAppletBarItemExpanded(self, modelIndex):
        """
        The user wants to view a different applet bar item.
        """
        drawerIndex = modelIndex
        if drawerIndex != -1:
            self.setSelectedAppletDrawer(drawerIndex)

    def setSelectedAppletDrawer(self, applet_index):
        """
        Show the correct applet central widget, viewer control widget, and applet drawer widget for this drawer index.
        """
        if self._refreshDrawerRecursionGuard is False:
            assert threading.current_thread().name == "MainThread"
            self._refreshDrawerRecursionGuard = True
            
            prev_applet_index = self.currentAppletIndex
            self.currentAppletIndex = applet_index
            self.currentAppletChanged.emit(prev_applet_index, self.currentAppletIndex)
            
            # Collapse all drawers in the applet bar...
            # ...except for the newly selected item.
            drawerModelIndex = self.getModelIndexFromDrawerIndex(applet_index)
            #self.appletBar.expand( drawerModelIndex )
            self.appletBar.setCurrentIndex(drawerModelIndex)

            # Select the appropriate central widget, menu widget, and viewer control widget for this applet
            self.showCentralWidget(applet_index)
            self.showViewerControlWidget(applet_index)
            self.showMenus(applet_index)
            self.refreshAppletDrawer(applet_index)

            self._refreshDrawerRecursionGuard = False

            applet = self._applets[applet_index]
            # Only show the combo if the applet is lane-aware and there is more than one lane loaded.
            self.imageSelectionGroup.setVisible(applet.syncWithImageIndex
                                                and self.imageSelectionCombo.count() > 1
                                                and self._applets[applet_index].getMultiLaneGui().allowLaneSelectionChange())

    def showCentralWidget(self, applet_index):
        if applet_index < len(self._applets):
            centralWidget = self._applets[applet_index].getMultiLaneGui().centralWidget()
            # Replace the placeholder widget, if possible
            if centralWidget is not None:
                if self.appletStack.indexOf(centralWidget) == -1:
                    self.appletStack.removeWidget(self.appletStack.widget(applet_index))
                    self.appletStack.insertWidget(applet_index, centralWidget)
                    # For test recording purposes, every gui we add MUST have a unique name
                    centralWidget.setObjectName(
                        "centralWidget_applet_{}_lane_{}".format(applet_index, self.currentImageIndex))

            self.appletStack.setCurrentIndex(applet_index)

    def showViewerControlWidget(self, applet_index):
        if applet_index < len(self._applets):
            viewerControlWidget = self._applets[applet_index].getMultiLaneGui().viewerControlWidget()
            # Replace the placeholder widget, if possible
            if viewerControlWidget is not None:
                if self.viewerControlStack.indexOf(viewerControlWidget) == -1:
                    self.viewerControlStack.addWidget(viewerControlWidget)
                self.viewerControlStack.setCurrentWidget(viewerControlWidget)
                # For test recording purposes, every gui we add MUST have a unique name
                viewerControlWidget.setObjectName(
                    "viewerControls_applet_{}_lane_{}".format(applet_index, self.currentImageIndex))

    def refreshAppletDrawer(self, applet_index):
        if applet_index < len(self._applets) and applet_index < self.appletBar.count():
            updatedDrawerTitle = self._applets[applet_index].name
            updatedDrawerWidget = self._applets[applet_index].getMultiLaneGui().appletDrawer()
            self.appletBar.setItemText(applet_index, updatedDrawerTitle)
            appletDrawerStackedWidget = self.appletBar.widget(applet_index)
            if appletDrawerStackedWidget.indexOf(updatedDrawerWidget) == -1:
                appletDrawerStackedWidget.addWidget(updatedDrawerWidget)
                # For test recording purposes, every gui we add MUST have a unique name
                appletDrawerStackedWidget.setObjectName(
                    "appletDrawer_applet_{}_lane_{}".format(applet_index, self.currentImageIndex))

            appletDrawerStackedWidget.setCurrentWidget(updatedDrawerWidget)

    def onCloseActionTriggered(self):
        if not self.ensureNoCurrentProject():
            return
        self.closeCurrentProject()

        self.setupOpenFileButtons()
        self.mainStackedWidget.setCurrentIndex(0)

    def postErrorMessage(self, caption, text):
        '''Thread-safe function to have the GUI display an error dialog with
           the given caption and text.
        '''
        self.thunkEventHandler.post(self.errorMessageFilter.showErrorMessage, caption, text)

    def showMenus(self, applet_index):
        self.menuBar().clear()
        self.menuBar().addMenu(self._projectMenu)
        if self._settingsMenu is not None:
            self.menuBar().addMenu(self._settingsMenu)

        workflowMenus = self.workflow.menus()
        if workflowMenus is not None:
            for m in workflowMenus:
                self.menuBar().addMenu(m)

        if applet_index < len(self._applets):
            appletMenus = self._applets[applet_index].getMultiLaneGui().menus()
            if appletMenus is not None:
                for m in appletMenus:
                    self.menuBar().addMenu(m)
        if ilastik_config.getboolean("ilastik", "debug"):
            self.menuBar().addMenu(self._debugMenu)
        self.menuBar().addMenu(self._helpMenu)

    def getModelIndexFromDrawerIndex(self, drawerIndex):
        drawerTitleItem = self.appletBar.widget(drawerIndex)
        return self.appletBar.indexOf(drawerTitleItem)

    def addApplet(self, applet_index, app):
        assert isinstance(app, Applet), "Applets must inherit from Applet base class."
        assert app.base_initialized, "Applets must call Applet.__init__ upon construction."

        assert isinstance(app.getMultiLaneGui(), AppletGuiInterface), \
            "Applet GUIs must conform to the Applet GUI interface."

        # Add placeholder widget, since the applet's central widget may not exist yet.
        self.appletStack.addWidget(QWidget(parent=self))

        # Add a placeholder widget
        self.viewerControlStack.addWidget(QWidget(parent=self))

        # Add rows to the applet bar model

        # Add all of the applet bar's items to the toolbox widget
        controlName = app.name
        controlGuiWidget = app.getMultiLaneGui().appletDrawer()
        assert isinstance(controlGuiWidget, QWidget), "Not a widget: {}".format( controlGuiWidget )

        stackedWidget = QStackedWidget()
        stackedWidget.addWidget(controlGuiWidget)

        self.appletBar.addItem(stackedWidget, controlName)
        if not app.interactive:
            # Some applets don't really need a GUI, but they still have a top-level operator and serializer.
            # In that case, we don't show it in the applet drawer
            self.appletBar.hideIndexItem(applet_index)

        # Set up handling of GUI commands from this applet
        self._disableCounts.append(0)
        self._controlCmds.append([])

        # Set up handling of shell requests from this applet
        app.shellRequestSignal.subscribe(partial(self.handleShellRequest, applet_index))

        return applet_index

    def removeAllAppletWidgets(self):
        for app in self._applets:
            app.shellRequestSignal.clean()
            app.progressSignal.clean()

        self._clearStackedWidget(self.appletStack)
        self._clearStackedWidget(self.viewerControlStack)

        # Remove all drawers
        for i in reversed(list(range(self.appletBar.count()))):
            widget = self.appletBar.widget(i)
            widget.hide()
            widget.setParent(None)
            self.appletBar.removeItem(i)

    def _clearStackedWidget(self, stackedWidget):
        for i in reversed(list(range(stackedWidget.count()))):
            lastWidget = stackedWidget.widget(i)
            stackedWidget.removeWidget(lastWidget)

    def handleShellRequest(self, applet_index, requestAction):
        """
        An applet is asking us to do something.  Handle the request.
        """
        if requestAction == ShellRequest.RequestSave:
            # Call the handler directly to ensure this is a synchronous call (not queued to the GUI thread)
            self.projectManager.saveProject()

    def __len__(self):
        return self.appletBar.count()

    def __getitem__(self, index):
        return self._applets[index]

    def onNewProjectActionTriggered(self, workflow_class=None):
        logger.debug("New Project action triggered")
        newProjectFilePath = self.getProjectPathToCreate()
        if newProjectFilePath is not None:
            # Make sure the user is finished with the currently open project
            if not self.ensureNoCurrentProject():
                return

            self.createAndLoadNewProject(newProjectFilePath, workflow_class)

    def createAndLoadNewProject(self, newProjectFilePath, workflow_class, h5_file_kwargs={}):
        '''Create a new project file for the given workflow and open the workflow in the shell.

        To create an in-memory project file call it as follows (the filename is irrelevant in this case):
        createAndLoadNewProject( "tmp.ilp", MyWorkflowClass, h5_file_kwargs={'driver': 'core', 'backing_store': False})

        :param h5_file_kwargs: Passed directly to h5py.File.__init__() of the project file; all standard params except 'mode' are allowed.
        '''

        newProjectFile = ProjectManager.createBlankProjectFile(newProjectFilePath, workflow_class,
                                                               self._workflow_cmdline_args, h5_file_kwargs)
        self._loadProject(newProjectFile, newProjectFilePath, workflow_class, readOnly=False)
        
        # If load failed, projectManager is None 
        if self.projectManager:
            self.projectManager.saveProject()

    def getProjectPathToCreate(self, defaultPath=None, caption="Create Ilastik Project"):
        """
        Ask the user where he would like to create a project file.
        """
        if defaultPath is None:
            defaultPath = os.path.expanduser("~/MyProject.ilp")

        fileSelected = False
        while not fileSelected:
            options = QFileDialog.Options()
            if ilastik_config.getboolean("ilastik", "debug"):
                options |= QFileDialog.DontUseNativeDialog
                # For testing, it's easier if we don't record the overwrite confirmation
                options |= QFileDialog.DontConfirmOverwrite

            projectFilePath, _filter = QFileDialog.getSaveFileName(self, caption, defaultPath,
                                                          "Ilastik project files (*.ilp)", options=options)
            # If the user cancelled, stop now
            if not projectFilePath:
                return None
            fileSelected = True

            # Add extension if necessary
            fileExtension = os.path.splitext(projectFilePath)[1].lower()
            if fileExtension != '.ilp':
                projectFilePath += ".ilp"
                if os.path.exists(projectFilePath):
                    # Since we changed the file path, we need to re-check if we're overwriting an existing file.
                    message = "A file named '" + projectFilePath + "' already exists in this location.\n"
                    message += "Are you sure you want to overwrite it?"
                    buttons = QMessageBox.Yes | QMessageBox.Cancel
                    response = QMessageBox.warning(self, "Overwrite existing project?", message, buttons,
                                                   defaultButton=QMessageBox.Cancel)
                    if response == QMessageBox.Cancel:
                        # Try again...
                        fileSelected = False

        return projectFilePath

    def onImportProjectActionTriggered(self):
        """
        Import an existing project into a new file.
        This involves opening the old file, saving it to a new file, and then opening the new file.
        """
        logger.debug("Import Project Action")

        # Find the directory of the most recently *imported* project
        mostRecentImportPath = PreferencesManager().get('shell', 'recently imported')
        if mostRecentImportPath is not None:
            defaultDirectory = os.path.split(mostRecentImportPath)[0]
        else:
            defaultDirectory = os.path.expanduser('~')

        # Select the paths to the ilp to import and the name of the new one we'll create
        importedFilePath = self.getProjectPathToOpen(defaultDirectory)
        if importedFilePath is not None:
            PreferencesManager().set('shell', 'recently imported', importedFilePath)
            defaultFile, ext = os.path.splitext(importedFilePath)
            defaultFile += "_imported"
            defaultFile += ext
            newProjectFilePath = self.getProjectPathToCreate(defaultFile)

        # If the user didn't cancel
        if importedFilePath is not None and newProjectFilePath is not None:
            if not self.ensureNoCurrentProject():
                return
            newProjectFile = ProjectManager.createBlankProjectFile(newProjectFilePath)
            self._loadProject(newProjectFile, newProjectFilePath, workflow_class=None, readOnly=False,
                              importFromPath=importedFilePath)

    def onDownloadProjectFromDvidActionTriggered(self):
        logger.debug("Download Project From DVID")
        
        recent_hosts_pref = PreferencesManager.Setting("DataSelection", "Recent DVID Hosts")
        recent_hosts = recent_hosts_pref.get()
        if not recent_hosts:
            recent_hosts = ["localhost:8000"]
        recent_hosts = [h for h in recent_hosts if h] # There used to be a bug where empty strings could be saved. Filter those out.

        recent_nodes_pref = PreferencesManager.Setting("DataSelection", "Recent DVID Nodes")
        recent_nodes = recent_nodes_pref.get() or {}

        # Ask for a selection.
        from libdvid.gui import ContentsBrowser
        browser = ContentsBrowser(recent_hosts, recent_nodes, mode='select_existing', selectable_type='keyvalue', parent=self)
        if browser.exec_() == ContentsBrowser.Rejected:
            return

        if None in browser.get_selection():
            QMessageBox.critical("Couldn't use your selection.")
            return

        hostname, repo_uuid, data_name, node_uuid, typename = browser.get_selection()
        dvid_url = 'http://{hostname}/api/node/{node_uuid}/{data_name}'.format( **locals() )

        # Relocate host to top of 'recent' list, and limit list to 10 items.
        try:
            i = recent_hosts.index(hostname)
            del recent_hosts[i]
        except ValueError:
            pass
        finally:
            recent_hosts.insert(0, hostname)        
            recent_hosts = recent_hosts[:10]

        # Save pref
        recent_nodes[str(hostname)] = str(node_uuid)
        recent_nodes_pref.set(recent_nodes)
        recent_hosts_pref.set(recent_hosts)

        # Open
        self.openProjectFile(dvid_url)

    def getProjectPathToOpen(self, defaultDirectory):
        """
        Return the path of the project the user wants to open (or None if he cancels).
        """
        options = QFileDialog.Options()
        if ilastik_config.getboolean("ilastik", "debug"):
            options = QFileDialog.Options(QFileDialog.DontUseNativeDialog)

        projectFilePath, _filter = QFileDialog.getOpenFileName(
            self, "Open Ilastik Project", defaultDirectory, "Ilastik project files (*.ilp)", options=options)

        # If the user canceled, stop now
        if not projectFilePath:
            return None

        return projectFilePath

    def onOpenProjectActionTriggered(self):
        logger.debug("Open Project action triggered")

        # Find the directory of the most recently opened project
        mostRecentProjectPath = PreferencesManager().get('shell', 'recently opened')
        if mostRecentProjectPath:
            defaultDirectory = os.path.split(mostRecentProjectPath)[0]
        else:
            defaultDirectory = os.path.expanduser('~')

        projectFilePath = self.getProjectPathToOpen(defaultDirectory)
        if projectFilePath is not None:
            # Make sure the user is finished with the currently open project
            if not self.ensureNoCurrentProject():
                return

            self.openProjectFile(projectFilePath)

    def openProjectFile(self, projectFilePath, force_readonly=False):
        """
        Explicitly required by ShellABC
        """
        # If the user gives us a URL to a DVID key,
        # then download the project file from dvid first.
        # (So far, DVID is the only type of URL access we support for project files.)
        if isUrl(projectFilePath):
            projectFilePath = HeadlessShell.downloadProjectFromDvid(projectFilePath)
            force_readonly=True

        try:
            hdf5File, workflow_class, readOnly = ProjectManager.openProjectFile(projectFilePath, force_readonly)
        except ProjectManager.ProjectVersionError as e:
            QMessageBox.warning(self, "Old Project",
                                "Could not load old project file: " + projectFilePath + ".\nPlease try 'Import Project' instead.")
        except ProjectManager.FileMissingError:
            QMessageBox.warning(self, "Missing File", "Could not find project file: " + projectFilePath)
        except:
            msg = "Unable to open project file: " + projectFilePath
            log_exception(logger, msg)
            QMessageBox.warning(self, "Corrupted Project", msg)
        else:
            #as load project can take a while, show a wait cursor
            QApplication.setOverrideCursor(Qt.WaitCursor)
            self.statusBar.showMessage("Loading project %s ..." % projectFilePath)
            self._loadProject(hdf5File, projectFilePath, workflow_class, readOnly)
            QApplication.restoreOverrideCursor()
            self.statusBar.clearMessage()

    def _loadProject(self, hdf5File, projectFilePath, workflow_class, readOnly, importFromPath=None):
        """
        Load the data from the given hdf5File (which should already be open).
        Populate the shell with widgets from all the applets in the new workflow.
        """

        if workflow_class is None:
            #ask the user to name a workflow
            workflow_class = self.getWorkflow()

        # If the user cancelled, give up.
        if workflow_class is None:
            return

        # If there are any "creation-time" command-line args saved to the project file,
        #  load them so that the workflow can be instantiated with the same settings 
        #  that were used when the project was first created. 
        project_creation_args = []
        if "workflow_cmdline_args" in list(hdf5File.keys()):
            if len(hdf5File["workflow_cmdline_args"]) > 0:
                project_creation_args = list(map(str, hdf5File["workflow_cmdline_args"][...]))

        try:
            assert self.projectManager is None, "Expected projectManager to be None."
            self.projectManager = ProjectManager(self,
                                                 workflow_class,
                                                 workflow_cmdline_args=self._workflow_cmdline_args,
                                                 project_creation_args=project_creation_args)

        except Exception as e:
            msg = "Could not load project file.\n" + str(e)
            log_exception(logger, msg)
            QMessageBox.warning(self, "Failed to Load", msg)

            # no project will be loaded, free the file resource
            hdf5File.close()
        else:

            try:
                # Add all the applets from the workflow
                for index, app in enumerate(self.projectManager.workflow.applets):
                    self.addApplet(index, app)

                start = time.time()
                #load the project data from file
                if importFromPath is None:
                    #FIXME: load the project asynchronously
                    self.projectManager._loadProject(hdf5File, projectFilePath, readOnly)
                else:
                    assert not readOnly, "Can't import into a read-only file."
                    self.projectManager._importProject(importFromPath, hdf5File, projectFilePath)
            except Exception as ex:
                log_exception(logger)
                self.closeCurrentProject()

                # _loadProject failed, so we cannot expect it to clean up
                # the hdf5 file (but it might have cleaned it up, so we catch 
                # the error)
                try:
                    hdf5File.close()
                except:
                    pass
                QMessageBox.warning(self, "Failed to Load", "Could not load project file.\n" + str(ex))

            else:
                stop = time.time()
                logger.debug("Loading the project took {:.2f} sec.".format(stop - start))

                #add file and workflow to users preferences
                mostRecentProjectPaths = PreferencesManager().get('shell', 'recently opened list')
                if mostRecentProjectPaths is None:
                    mostRecentProjectPaths = []

                workflowName = self.projectManager.workflow.workflowName
                workflowDisplayName = self.projectManager.workflow.workflowDisplayName

                for proj, work in mostRecentProjectPaths[:]:
                    if proj == projectFilePath and (proj, work) in mostRecentProjectPaths:
                        mostRecentProjectPaths.remove((proj, work))

                mostRecentProjectPaths.insert(0, (projectFilePath, workflowDisplayName))

                #cut list of stored files at randomly chosen number of 5
                if len(mostRecentProjectPaths) > 5:
                    mostRecentProjectPaths = mostRecentProjectPaths[:5]

                PreferencesManager().set('shell', 'recently opened list', mostRecentProjectPaths)
                PreferencesManager().set('shell', 'recently opened', projectFilePath)

                #be friendly to user: if this file has not specified a default workflow, do it now
                if not "workflowName" in list(hdf5File.keys()) and not readOnly:
                    hdf5File.create_dataset("workflowName", data=workflowName.encode('utf-8'))

                #switch away from the startup screen to show the loaded project
                self.mainStackedWidget.setCurrentIndex(1)
                # By default, make the splitter control expose a reasonable width of the applet bar
                self.mainSplitter.setSizes([300, 1])

                self.progressDisplayManager.cleanUp()
                self.progressDisplayManager.initializeForWorkflow(self.projectManager.workflow)

                self.setImageNameListSlot(self.projectManager.workflow.imageNameListSlot)
                self.updateShellProjectDisplay()

                # Enable all the applet controls
                self.enableWorkflow = True

                if "currentApplet" in list(hdf5File.keys()):
                    appletName = hdf5File["currentApplet"].value
                    self.setSelectedAppletDrawer(appletName)
                else:
                    self.setSelectedAppletDrawer(self.projectManager.workflow.defaultAppletIndex)

    def closeCurrentProject(self):
        """
        Undo everything that was done in loadProject()
        """
        assert threading.current_thread().name == "MainThread"
        if self.projectManager is not None:

            projectFile = self.projectManager.currentProjectFile
            if not self.projectManager.closed and projectFile is not None and not self.projectManager.currentProjectIsReadOnly:
                if "currentApplet" in list(projectFile.keys()):
                    del projectFile["currentApplet"]
                self.projectManager.currentProjectFile.create_dataset("currentApplet", data=self.currentAppletIndex)

            self.removeAllAppletWidgets()
            for f in self.cleanupFunctions:
                f()

            self.imageSelectionCombo.clear()
            self.changeCurrentInputImageIndex(-1)

            if self.projectDisplayManager is not None:
                old = weakref.ref(self.projectDisplayManager)
                self.projectDisplayManager.cleanUp()
                self.projectDisplayManager = None  # Destroy display manager
                # Ensure that it was really destroyed
                assert old() is None, "There shouldn't be extraneous references to the project display manager!"

            self.projectManager.cleanUp()
            self.projectManager = None  # Destroy project manager

        self.enableWorkflow = False
        self._controlCmds = []
        self._disableCounts = []
        self.updateShellProjectDisplay()

    def ensureNoCurrentProject(self, assertClean=False):
        """
        Close the current project.  If it's dirty, we ask the user for confirmation.

        The ``assertClean`` parameter is for tests.  Setting it to True will raise an assertion if the project was dirty.
        """
        closeProject = True
        if self.projectManager:
            dirtyApplets = self.projectManager.getDirtyAppletNames()
            if len(dirtyApplets) > 0:
                # Testing assertion
                assert not assertClean, "Expected a clean project but found it to be dirty!"

                message = "Your current project is about to be closed, but it has unsaved changes which will be lost.\n"
                message += "Are you sure you want to proceed?\n"
                message += "(Unsaved changes in: {})".format(', '.join(dirtyApplets))
                buttons = QMessageBox.Yes | QMessageBox.Cancel
                response = QMessageBox.warning(self, "Discard unsaved changes?", message, buttons,
                                               defaultButton=QMessageBox.Cancel)
                closeProject = (response == QMessageBox.Yes)

        if closeProject:
            self.closeCurrentProject()

        return closeProject

    def onSaveProjectActionTriggered(self):
        logger.debug("Save Project action triggered")

        def save():
            self.setAllAppletsEnabled(False)
            try:
                self.projectManager.saveProject()
            except ProjectManager.SaveError as err:
                self.thunkEventHandler.post(partial(QMessageBox.warning, self, "Error Attempting Save", str(err)))

            # First, re-enable all applets
            # (If the workflow doesn't provide a handleAppletStateUpdateRequested implementation,
            #  then everything is re-enabled.)
            self.setAllAppletsEnabled(True)
            # Next, tell the workflow to re-disable any applets that aren't really ready.
            self.workflow.handleAppletStateUpdateRequested()

        saveThread = threading.Thread(target=save)
        saveThread.start()

        return saveThread  # Return the thread so non-gui users (e.g. unit tests) can join it if they want to.

    def onSaveProjectAsActionTriggered(self):
        logger.debug("SaveAs Project action triggered")

        # Try to guess a good default project name, e.g. MyProject2.ilp
        currentPath, ext = os.path.splitext(self.projectManager.currentProjectPath)
        m = re.match("(.*)_(\d+)", currentPath)
        if m:
            baseName = m.groups()[0]
            projectNum = int(m.groups()[1]) + 1
        else:
            baseName = currentPath
            projectNum = 2

        defaultNewPath = "{}_{}{}".format(baseName, projectNum, ext)

        newPath = self.getProjectPathToCreate(defaultNewPath, caption="Select New Project Name")
        if newPath == self.projectManager.currentProjectPath:
            # If the new path is the same as the old one, then just do a regular save
            self.onSaveProjectActionTriggered()
        elif newPath is not None:
            def saveAs():
                self.setAllAppletsEnabled(False)

                try:
                    self.projectManager.saveProjectAs(newPath)
                except ProjectManager.SaveError as err:
                    self.thunkEventHandler.post(partial(QMessageBox.warning, self, "Error Attempting Save", str(err)))
                self.updateShellProjectDisplay()

                # First, re-enable all applets
                # (If the workflow doesn't provide a handleAppletStateUpdateRequested implementation,
                #  then everything is re-enabled.)
                self.setAllAppletsEnabled(True)
                # Next, tell the workflow to re-disable any applets that aren't really ready.
                self.workflow.handleAppletStateUpdateRequested()

            saveThread = threading.Thread(target=saveAs)
            saveThread.start()

    def onSaveProjectSnapshotActionTriggered(self):
        logger.debug("Saving Snapshot")
        currentPath, ext = os.path.splitext(self.projectManager.currentProjectPath)
        defaultSnapshot = currentPath + "_snapshot" + ext

        snapshotPath = self.getProjectPathToCreate(defaultSnapshot, caption="Create Project Snapshot")
        if snapshotPath is not None:
            try:
                self.projectManager.saveProjectSnapshot(snapshotPath)
            except ProjectManager.SaveError as err:
                QMessageBox.warning(self, "Error Attempting Save Snapshot", str(err))

    def closeEvent(self, closeEvent):
        """
        Reimplemented from QWidget.  Ignore the close event if the user has unsaved data and changes his mind.
        """
        if self.confirmQuit():
            # Since we're shutting down the app, we don't want to process any more gui events.
            # (We may encounter segfaults at this point if we try.)
            ThreadRouter.app_is_shutting_down = True

            # Quit.
            self.closeAndQuit()
        else:
            closeEvent.ignore()

    def onQuitActionTriggered(self, force=False, quitApp=True):
        """
        The user wants to quit the application.
        Check his project for unsaved data and ask if he really means it.
        Args:
            force - Don't check the project for unsaved data.
            quitApp - For testing purposes, set this to False if you just want to close the main window without quitting the app.
        """
        if force or self.confirmQuit():
            # disable gui events
            ThreadRouter.app_is_shutting_down = True

            self.closeAndQuit(quitApp)

    def confirmQuit(self):
        if self.projectManager:
            dirtyApplets = self.projectManager.getDirtyAppletNames()
            if len(dirtyApplets) > 0:
                message = "Your project has unsaved data.  Are you sure you want to discard your changes and quit?\n"
                message += "(Unsaved changes in: {})".format(', '.join(dirtyApplets))
                buttons = QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
                response = QMessageBox.warning(self, "Discard unsaved changes?", message, buttons,
                                               defaultButton=QMessageBox.Save)
                if response == QMessageBox.Cancel:
                    return False
                elif response == QMessageBox.Save:
                    saveThread = self.onSaveProjectActionTriggered()
                    # The save action is performed in a different thread,
                    # But we're shutting down right now.
                    # Just block here for the save to complete before we continue to shut down.
                    saveThread.join()
        return True

    def closeAndQuit(self, quitApp=True):
        geom = self.frameGeometry()
        x, y, width, height = geom.x(), geom.y(), geom.width(), geom.height()
        PreferencesManager().set('shell', 'startscreenGeometry', ( x, y, width, height ))

        if self.projectManager is not None:
            self.closeCurrentProject()

        # Stop the thread that checks for log config changes.
        ilastik.ilastik_logging.stopUpdates()

        # Close the window first, so applets can reimplement hideEvent() and such.
        self.close()

        # For testing purposes, sometimes this function is called even though we don't want to really quit.
        if quitApp:
            qApp.quit()

    def setAllAppletsEnabled(self, enabled):
        for applet in self._applets:
            self.setAppletEnabled(applet, enabled)

    def setAppletEnabled(self, applet, enabled):
        # We immediately track the enabled status in a member dict instead 
        #  of checking with the applet gui itself, in case isAppletEnabled() 
        #  gets called before _setAppletEnabled gets a chance to execute.
        self._applet_enabled_states[applet] = enabled

        # Post this to the gui thread
        self.thunkEventHandler.post(self._setAppletEnabled, applet, enabled)

    def isAppletEnabled(self, applet):
        return self._applet_enabled_states[applet]

    def newServerConnected(self, name):
        # iterate over all other applets and inform about new connection if relevant
        for applet in self._applets:
            if name == "knime":
                if hasattr(applet, "connected_to_knime"):
                    applet.connected_to_knime = True

    def setAllViewersPosition(self, pos):
        # operate on currently displayed applet first
        self._setViewerPosition(self._applets[self.currentAppletIndex], pos)

        # now iterate over all other applets and change the viewer focus
        for applet in self._applets:
            if not applet is self._applets[self.currentAppletIndex]:
                self._setViewerPosition(applet, pos)

    @threadRouted
    def _setViewerPosition(self, applet, pos):
        gui = applet.getMultiLaneGui()
        # test if gui is a Gui on its own or just created by a SingleToMultiGuiAdapter
        if isinstance(gui, SingleToMultiGuiAdapter):
            gui = gui.currentGui()
        # test if gui implements "setViewerPos()" method
        if issubclass(type(gui), VolumeViewerGui):
            gui.setViewerPos(pos, setTime=True, setChannel=True)

    def enableProjectChanges(self, enabled):
        # Post this to the gui thread
        self.thunkEventHandler.post(self._enableProjectChanges, enabled)

    def _enableProjectChanges(self, enabled):
        """
        Enable or disable the shell actions that could affect the project state.
        (Basically anything that would cause the project to be closed.)
        """
        self._shellActions.openProjectAction.setEnabled(enabled)
        self._shellActions.importProjectAction.setEnabled(enabled)
        self._shellActions.quitAction.setEnabled(enabled)
        if self._shellActions.closeAction is not None:
            self._shellActions.closeAction.setEnabled(enabled)

    def _setAppletEnabled(self, applet, enabled):
        try:
            # This can fail if the applet was recently removed (e.g. if the project was closed)
            applet_index = self._applets.index(applet)
        except ValueError:
            pass
        else:
            applet.getMultiLaneGui().setEnabled(enabled)

            # Apply to the applet bar drawer heading, too.
            if applet_index < self.appletBar.count():
                # Unfortunately, Qt will auto-select a different drawer if
                #  we try to disable the currently selected drawer.
                # That can cause lots of problems for us (e.g. it trigger's the
                #  creation of applet guis that haven't been created yet.)
                # Therefore, only disable the title button of a drawer if it isn't already selected.
                if self.appletBar.currentIndex() != applet_index:
                    self.appletBar.setItemEnabled(applet_index, enabled)


assert issubclass(IlastikShell, ShellABC), "IlastikShell does not satisfy the generic shell interface!"
