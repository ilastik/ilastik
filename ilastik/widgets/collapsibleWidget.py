###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2022, the ilastik developers
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
from PyQt5.QtCore import QAbstractAnimation, QParallelAnimationGroup, QPropertyAnimation, Qt
from PyQt5.QtWidgets import QToolButton, QVBoxLayout, QWidget


# derived from https://stackoverflow.com/a/37119983
class CollapsibleWidget(QWidget):
    """Wraps a widget to expand/collapse on button press"""

    def __init__(
        self,
        widget: QWidget,
        header: str = "Details",
        animation_duration: int = 100,
        parent=None,
    ):
        """
        Args:
          widget: QWidget to be wrapped in a collapsible container. Multiple widgets
            can be given as content by e.g. wrapping them in a QScrollArea. Widget
            should be configured fully when passing it (to ensure correct sizing).
            No resizing is taken into account.
          header: Text displayed next to the arrow toolbutton
          start_collapsed: Control initial state. Set to False to have widget expanded
            visible upon construction.
        """

        super().__init__(parent)

        toggleButton = QToolButton()
        toggleButton.setStyleSheet("QToolButton {border: none;}")
        toggleButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        toggleButton.setArrowType(Qt.ArrowType.RightArrow)
        toggleButton.setText(header)
        toggleButton.setCheckable(True)
        toggleButton.setChecked(False)

        # for testing:
        self._toggleButton = toggleButton

        # initial state: minimized
        widget.setMaximumHeight(0)
        widget.setMinimumHeight(0)

        animation = QParallelAnimationGroup()
        animation.addAnimation(QPropertyAnimation(self, b"minimumHeight"))
        animation.addAnimation(QPropertyAnimation(self, b"maximumHeight"))
        animation.addAnimation(QPropertyAnimation(widget, b"maximumHeight"))

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(toggleButton)

        contentLayout = QVBoxLayout()
        contentLayout.addWidget(widget)
        layout.addLayout(contentLayout)

        self.setLayout(layout)

        def updateState(checked: bool):
            if checked:
                toggleButton.setArrowType(Qt.ArrowType.DownArrow)
                animation.setDirection(QAbstractAnimation.Forward)
            else:
                toggleButton.setArrowType(Qt.ArrowType.RightArrow)
                animation.setDirection(QAbstractAnimation.Backward)

            animation.start()

        toggleButton.clicked.connect(updateState)

        collapsedHeight = self.sizeHint().height() - widget.maximumHeight()
        contentHeight = widget.sizeHint().height()

        for i in range(animation.animationCount() - 1):
            anim = animation.animationAt(i)
            anim.setDuration(animation_duration)
            anim.setStartValue(collapsedHeight)
            anim.setEndValue(collapsedHeight + contentHeight)

        anim = animation.animationAt(animation.animationCount() - 1)
        anim.setDuration(animation_duration)
        anim.setStartValue(0)
        anim.setEndValue(contentHeight)
