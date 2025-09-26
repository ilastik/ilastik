###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2025, the ilastik developers
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
#          http://ilastik.org/license.html
###############################################################################
from typing import Optional, Union

from qtpy.QtCore import Qt, QSize
from qtpy.QtGui import QColor, QMouseEvent, QPaintEvent, QPalette, QResizeEvent
from qtpy.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QSplitterHandle,
    QStackedWidget,
    QStyle,
    QStyleOptionButton,
    QStylePainter,
    QVBoxLayout,
    QWidget,
)

from ilastik.widgets.appletDrawerToolBox import AppletDrawerToolBox


class VerticalButton(QPushButton):

    def sizeHint(self) -> QSize:
        return super().sizeHint().transposed()

    def paintEvent(self, a0: QPaintEvent) -> None:
        painter = QStylePainter(self)
        options = QStyleOptionButton()
        options.initFrom(self)
        options.text = self.text()
        painter.rotate(-90)
        painter.translate(-1 * self.height(), 0)
        options.rect = options.rect.transposed()
        painter.drawControl(QStyle.CE_PushButton, options)


class LabeledHandle(QSplitterHandle):

    def __init__(self, orientation, parent: "HorizontalMainSplitter"):
        super().__init__(orientation, parent)
        self.is_collapsed: bool
        self.toggle_button = VerticalButton("Secondary controls", self)
        self.toggle_button.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.toggle_button.setFocusPolicy(Qt.NoFocus)
        self.setToolTip("Secondary controls. Double click to show/hide, click and drag to resize.")

    def resizeEvent(self, a0: QResizeEvent) -> None:
        super().resizeEvent(a0)
        # sync up button position
        if self.orientation() == Qt.Horizontal:
            self.toggle_button.setMaximumWidth(self.width())
            self.toggle_button.move(
                self.width() // 2 - self.toggle_button.width() // 2,
                self.height() // 2 - self.toggle_button.height() // 2,
            )

    def sizeHint(self) -> QSize:
        assert self.orientation() == Qt.Horizontal
        return QSize(20, super().sizeHint().height())

    def mouseDoubleClickEvent(self, a0: QMouseEvent) -> None:
        self.parent().toggle_secondary_contents()
        a0.accept()

    def setButtonText(self, text: str) -> None:
        self.toggle_button.setText(text)


class CentralWidgetStack(QStackedWidget):
    """Stacked widget that will contain/show the various central widgets

    usually volumina, sometimes also additional elements, e.g. in DataSelection
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        policy.setHorizontalStretch(2)
        policy.setVerticalStretch(2)
        self.setSizePolicy(policy)

        self.setMinimumSize(500, 100)
        self.setBaseSize(500, 100)

        self.setFrameShape(QFrame.NoFrame)
        self.setFrameShadow(QFrame.Plain)
        self.setLineWidth(0)


class MainControls(QSplitter):
    """The widget home to the applet drawer and viewer control stack"""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(Qt.Vertical, parent)
        self.appletBar = AppletDrawerToolBox()
        appletbar_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        appletbar_policy.setHorizontalStretch(0)
        appletbar_policy.setVerticalStretch(6)
        self.appletBar.setSizePolicy(appletbar_policy)

        appletBar_pallette = QPalette()
        appletBar_pallette.setColor(QPalette.Active, QPalette.Highlight, QColor(62, 62, 62, 255))
        appletBar_pallette.setColor(QPalette.Inactive, QPalette.Highlight, QColor(62, 62, 62, 255))
        appletBar_pallette.setColor(QPalette.Disabled, QPalette.Highlight, QColor(240, 240, 240, 255))
        self.appletBar.setPalette(appletBar_pallette)
        self.appletBar.setLineWidth(2)
        self.appletBar.setMidLineWidth(2)

        self.imageSelectionGroup = QWidget()
        imageSelectionGroup_layout = QHBoxLayout()
        imageSelectionGroup_layout.addWidget(QLabel("Current View:"))
        self.imageSelectionCombo = QComboBox()
        imageSelectionCombo_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        imageSelectionCombo_policy.setHorizontalStretch(0)
        imageSelectionCombo_policy.setVerticalStretch(0)
        self.imageSelectionCombo.setSizePolicy(imageSelectionCombo_policy)
        imageSelectionGroup_layout.addWidget(self.imageSelectionCombo)
        self.imageSelectionGroup.setLayout(imageSelectionGroup_layout)

        self.viewerControlStack = QStackedWidget()
        viewerControlStackpolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        viewerControlStackpolicy.setHorizontalStretch(2)
        viewerControlStackpolicy.setVerticalStretch(2)
        self.viewerControlStack.setSizePolicy(viewerControlStackpolicy)
        self.viewerControlStack.setMinimumSize(310, 200)
        self.viewerControlStack.setBaseSize(0, 0)
        self.viewerControlStack.setFrameShape(QFrame.NoFrame)
        self.viewerControlStack.setFrameShadow(QFrame.Plain)
        self.viewerControlStack.setLineWidth(0)

        verticalLayout = QVBoxLayout()
        verticalLayout.setSpacing(0)
        verticalLayout.setContentsMargins(0, 0, 0, 0)
        verticalLayout.addWidget(self.imageSelectionGroup)
        verticalLayout.addWidget(self.viewerControlStack)
        layoutWidget = QWidget()
        layoutWidget.setLayout(verticalLayout)
        layout_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout_policy.setHorizontalStretch(2)
        layout_policy.setVerticalStretch(5)
        layoutWidget.setSizePolicy(layout_policy)

        self.addWidget(self.appletBar)
        self.addWidget(layoutWidget)


class SecondaryControlsStack(QStackedWidget):
    """Stacked widget that will contain/show the secondary controls

    currently LabelExplorerWidget for anything that does labeling
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        policy.setHorizontalStretch(2)
        policy.setVerticalStretch(2)
        self.setSizePolicy(policy)

        self.setMinimumSize(100, 100)
        self.setBaseSize(100, 100)

        self.setFrameShape(QFrame.NoFrame)
        self.setFrameShadow(QFrame.Plain)
        self.setLineWidth(0)


class HorizontalMainSplitter(QSplitter):
    """Widget intended for the main GUI elements

    Attrs:
      imageSelectionCombo: combobox for image index switching

    """

    def __init__(self, parent):
        super().__init__(
            orientation=Qt.Horizontal,
            parent=parent,
        )
        self.setChildrenCollapsible(False)
        self._secondary_handle = None
        self._mainControls = MainControls()
        self._viewerControlStack = self._mainControls.viewerControlStack
        self.appletBar = self._mainControls.appletBar
        self._imageSelectionGroup = self._mainControls.imageSelectionGroup
        self.imageSelectionCombo = self._mainControls.imageSelectionCombo

        self._centralStack = CentralWidgetStack()

        self._secondaryStack = SecondaryControlsStack()
        self._secondary_controls_hadle = None
        self._secondaryStackSize = 0

        self._insertWidget(0, self._mainControls)
        self._insertWidget(1, self._centralStack)
        self._insertWidget(2, self._secondaryStack)

        self._viewerControlPlaceholder = QWidget(self)
        self._centralWidgetPlaceholder = QWidget(self)

        self.setActiveViewerControls(self._viewerControlPlaceholder)
        self.setActiveCentralWidget(self._centralWidgetPlaceholder)

        self.splitterMoved.connect(self._save_secondary_size)
        self.setCollapsible(2, True)

    def clearStackedWidgets(self):
        """
        Called by workflow as a cleanup action when closing the project
        """
        self._secondaryStackSize = 0
        sz = self.sizes()
        self.setSizes([sz[0], sz[1] + sz[2], 0])
        for stacked_widget in [self._viewerControlStack, self._centralStack]:
            for i in reversed(list(range(stacked_widget.count()))):
                lastWidget = stacked_widget.widget(i)
                stacked_widget.removeWidget(lastWidget)

        self._clear_secondary_control_stack()

    def _clear_secondary_control_stack(self):

        if self._secondaryStack is not None:
            for i in reversed(list(range(self._secondaryStack.count()))):
                lastWidget = self._secondaryStack.widget(i)
                self._secondaryStack.removeWidget(lastWidget)

    @staticmethod
    def _setActiveStackWidget(stack, widget):
        if stack.indexOf(widget) == -1:
            stack.addWidget(widget)
        stack.setCurrentWidget(widget)

    def setActiveViewerControls(self, viewerControlWidget: Union[QWidget, None]):
        if viewerControlWidget is None:
            viewerControlWidget = self._viewerControlPlaceholder

        self._setActiveStackWidget(self._viewerControlStack, viewerControlWidget)

    def setActiveCentralWidget(self, centralWidget: Union[QWidget, None]):
        if centralWidget is None:
            centralWidget = self._centralWidgetPlaceholder

        self._setActiveStackWidget(self._centralStack, centralWidget)

    def setActiveSecondaryControls(self, secondaryControlsWidget: Union[QWidget, None]):
        if secondaryControlsWidget is not None:

            assert self.count() == 3
            assert self._secondaryStack is not None

            if not self._secondaryStack.isVisible():
                self._secondaryStack.setVisible(True)

            if self._secondaryStack.indexOf(secondaryControlsWidget) == -1:
                self._secondaryStack.addWidget(secondaryControlsWidget)
                if hasattr(secondaryControlsWidget, "sync_state"):
                    secondaryControlsWidget.sync_state()
                    self.splitterMoved.connect(secondaryControlsWidget.sync_state)
            self._secondaryStack.setCurrentWidget(secondaryControlsWidget)
            self._secondary_controls_hadle.setButtonText(secondaryControlsWidget.display_text)

        else:
            self._secondaryStack.setVisible(False)

    def setMainControlsVisible(self, visible: bool):
        self._mainControls.setVisible(visible)

    def setImageSelectionGroupVisible(self, visible: bool):
        self._imageSelectionGroup.setVisible(visible)

    def createHandle(self):
        n_widgets = self.count()

        if n_widgets == 2:
            if self._secondary_controls_hadle is None:
                self._secondary_controls_hadle = LabeledHandle(self.orientation(), self)
            return self._secondary_controls_hadle
        else:
            return QSplitterHandle(self.orientation(), self)

    def _save_secondary_size(self, pos, index):
        if index != 2:
            return

        self._secondaryStackSize = self.sizes()[2]

    def toggle_secondary_contents(self):
        sizes = self.sizes()

        was_collapsed = sizes[2] == 0

        if was_collapsed:
            if self._secondaryStackSize == 0:
                self._secondaryStackSize = 200
            sizes = [sizes[0], sizes[1] - self._secondaryStackSize, self._secondaryStackSize]
        else:
            sizes = [sizes[0], sizes[1] + sizes[2], 0]

        self.setSizes(sizes)
        secondaryControlsWidget = self._secondaryStack.currentWidget()
        if hasattr(secondaryControlsWidget, "sync_state"):
            secondaryControlsWidget.sync_state()

    def insertWidget(self, index: int, widget: QWidget) -> None:
        raise NotImplementedError("MainSideSplitter does not expose insertWidget.")

    def _insertWidget(self, index: int, widget: QWidget) -> None:
        return super().insertWidget(index, widget)
