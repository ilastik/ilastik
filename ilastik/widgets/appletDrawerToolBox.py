from typing import List, Tuple, Union
from qtpy.QtCore import Signal, QObject
from qtpy.QtGui import QIcon
from qtpy.QtWidgets import QToolBox, QWidget, QStackedWidget

from ilastik.shell.gui.iconMgr import ilastikIcons


class AppletDrawerToolBox(QToolBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ICON_CLOSED = QIcon(ilastikIcons.ChevronRight)
        self.ICON_OPEN = QIcon(ilastikIcons.ChevronDown)

        self._prevActive = None
        self.currentChanged.connect(self._toggleCollapsedMarker)

    def _toggleCollapsedMarker(self, newActiveIdx: int) -> None:
        if self._prevActive is not None:
            self._refreshCollapsedMarker(self._prevActive)

        self._refreshCollapsedMarker(newActiveIdx)
        self._prevActive = newActiveIdx

    def _refreshCollapsedMarker(self, idx: int) -> None:
        if self.currentIndex() == idx:
            self.setItemIcon(idx, self.ICON_OPEN)
        else:
            self.setItemIcon(idx, self.ICON_CLOSED)

    def setItemText(self, idx: int, text: str) -> None:
        """
        Override to set human readable number in tab title
        """
        super().setItemText(idx, f"{idx + 1}. {text}")

    def addItem(self, widget: QStackedWidget, text: str) -> int:
        idx = super().addItem(widget, text)
        self.setItemText(idx, text)
        self._refreshCollapsedMarker(idx)
        return idx

    def items(self) -> List[Tuple[int, QStackedWidget]]:
        return [(i, self.widget(i)) for i in range(self.count())]


class AppletBarManager(QObject):
    """
    This class controls interaction between IlastikShell and AppletDrawerToolBox
    Some items are not meant to be displayed for user (interactive attribute),
    but they still need to be tracked, to provide convenient interface
    """

    appletActivated = Signal(int)

    def __init__(self, appletBar: AppletDrawerToolBox) -> None:
        super().__init__()

        self._toolbarIdByAppletId: dict[int, Union[int, None]] = {}
        self._appletIdByToolbarId: dict[int, int] = {}
        self._toolbox = appletBar
        self._toolbox.currentChanged.connect(self._handleCurrentChanged)

    def _handleCurrentChanged(self, toolboxId: int) -> None:
        """
        Emit applet activated signal on toolbox switch
        """
        if toolboxId == -1:
            return

        appletId = self._appletIdByToolbarId[toolboxId]
        self.appletActivated.emit(appletId)

    def addApplet(self, appletId: int, applet) -> None:
        """
        Adds applet to toolbox if it is available in interactive mode
        """
        if applet.interactive:
            # We need new id before we added item, to handle currentChangedSignal
            newToolbarId = self._toolbox.count()
            self._toolbarIdByAppletId[appletId] = newToolbarId
            self._appletIdByToolbarId[newToolbarId] = appletId

            widget = applet.getMultiLaneGui().appletDrawer()
            assert isinstance(widget, QWidget), f"Not a widget: {widget}"

            stackedWidget = QStackedWidget()
            stackedWidget.addWidget(widget)

            self._toolbox.addItem(stackedWidget, applet.name)
        else:
            self._toolbarIdByAppletId[appletId] = None

    def focusApplet(self, appletId: int) -> None:
        toolboxId = self._toolbarIdByAppletId.get(appletId)

        if toolboxId is None:
            return

        self._toolbox.setCurrentIndex(toolboxId)

    def updateAppletTitle(self, appletId: int, newTitle: str) -> None:
        toolboxId = self._toolbarIdByAppletId.get(appletId)

        if toolboxId is None:
            return

        self._toolbox.setItemText(toolboxId, newTitle)

    def updateAppletWidget(self, appletId: int, newWidget: QWidget) -> None:
        toolboxId = self._toolbarIdByAppletId.get(appletId)

        if toolboxId is None:
            return

        stackedWidget = self._toolbox.widget(toolboxId)
        if stackedWidget.indexOf(newWidget) == -1:
            stackedWidget.addWidget(newWidget)

        stackedWidget.setCurrentWidget(newWidget)

    def setEnabled(self, appletId: int, value: bool) -> None:
        toolboxId = self._toolbarIdByAppletId.get(appletId)

        if toolboxId is None:
            return

        # Unfortunately, Qt will auto-select a different drawer if
        # we try to disable the currently selected drawer.
        # That can cause lots of problems for us (e.g. it trigger's the
        # creation of applet guis that haven't been created yet.)
        # Therefore, only disable the title button of a drawer if it isn't already selected.
        if self._toolbox.currentIndex() != toolboxId:
            self._toolbox.setItemEnabled(toolboxId, value)

    def removeAll(self) -> None:
        # Removing starting from the end to avoid index changes
        for idx, w in reversed(self._toolbox.items()):
            w.hide()
            w.setParent(None)
            self._toolbox.removeItem(idx)
            appletId = self._appletIdByToolbarId.pop(idx, None)
            if appletId:
                self._toolbarIdByAppletId.pop(appletId, None)
