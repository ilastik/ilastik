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

from qtpy.QtCore import Qt
from qtpy.QtGui import QColor, QPalette
from qtpy.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ilastik.widgets.appletDrawerToolBox import AppletDrawerToolBox


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


class HorizontalMainSplitter(QSplitter):
    """Widget intended for the main GUI elements

    Attrs:
      mainControls: Contains AppletDrawer and ViewerControlstack
      centralStack: Contains CentralWidget
    """

    def __init__(self, parent):
        super().__init__(
            orientation=Qt.Horizontal,
            parent=parent,
        )
        self.setChildrenCollapsible(False)
        self._mainControls = MainControls()
        self._viewerControlStack = self._mainControls.viewerControlStack
        self.appletBar = self._mainControls.appletBar
        self._imageSelectionGroup = self._mainControls.imageSelectionGroup
        self.imageSelectionCombo = self._mainControls.imageSelectionCombo

        self._centralStack = CentralWidgetStack()

        self.insertWidget(0, self._mainControls)
        self.insertWidget(1, self._centralStack)

        self._viewerControlPlaceholder = QWidget(self)
        self._centralWidgetPlaceholder = QWidget(self)

        self.setActiveViewerControls(self._viewerControlPlaceholder)
        self.setActiveCentralWidget(self._centralWidgetPlaceholder)

    def clearStackedWidgets(self):
        for stacked_widget in [self._viewerControlStack, self._centralStack]:
            for i in reversed(list(range(stacked_widget.count()))):
                lastWidget = stacked_widget.widget(i)
                stacked_widget.removeWidget(lastWidget)

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

    def setMainControlsVisible(self, visible: bool):
        self._mainControls.setVisible(visible)

    def setImageSelectionGroupVisible(self, visible: bool):
        self._imageSelectionGroup.setVisible(visible)
