###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2026, the ilastik developers
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

from contextlib import contextmanager
from typing import Callable

from qtpy.QtCore import Signal
from qtpy.QtWidgets import QCheckBox, QGroupBox, QVBoxLayout

from lazyflow.slot import Slot


class ChannelSelectionWidget(QGroupBox):

    def __init__(self, raw_slot: Slot, selection_slot: Slot, parent=None):
        super().__init__("Input channels", parent)
        self.__cleanup_fns: list[Callable[[], None]] = []
        self._currently_updating = False
        self.setObjectName("channelSelectionWidget")
        self.setToolTip("Raw data channels used for feature computation")
        self._raw_slot = raw_slot
        self._selection_slot = selection_slot
        self._checkboxes: list[QCheckBox] = []
        self.setLayout(QVBoxLayout())

        self.__cleanup_fns.append(raw_slot.notifyReady(self._ensure_selection_value, defer=True))
        self.__cleanup_fns.append(raw_slot.notifyReady(self.update_gui_from_operator, defer=True))
        self.__cleanup_fns.append(raw_slot.notifyMetaChanged(self._ensure_selection_value, defer=True))
        self.__cleanup_fns.append(raw_slot.notifyMetaChanged(self.update_gui_from_operator, defer=True))
        self.__cleanup_fns.append(selection_slot.notifyDirty(self.update_gui_from_operator, defer=True))

        self._ensure_selection_value()
        self.update_gui_from_operator()

    @contextmanager
    def _updating(self):
        assert not self._currently_updating
        self._currently_updating = True
        try:
            yield
        finally:
            self._currently_updating = False

    def cleanUp(self):
        for fn in self.__cleanup_fns:
            fn()

    def update_gui_from_operator(self, *_):
        if self._currently_updating:
            return
        with self._updating():
            n_channels = self._raw_slot.meta.getTaggedShape().get("c", 1) if self._raw_slot.ready() else 0
            self._ensure_checkboxes(n_channels)

            selected = self._selection_slot.value if self._selection_slot.ready() else list(range(n_channels))

            for channel, checkbox in enumerate(self._checkboxes):
                checkbox.setChecked(channel in selected)

    def update_operator_from_gui(self, *_):
        if self._currently_updating:
            return
        with self._updating():
            selected = tuple([i for i, checkbox in enumerate(self._checkboxes) if checkbox.isChecked()])
            self._selection_slot.setValue(selected)

    def _ensure_checkboxes(self, n_channels: int):
        self.setVisible(n_channels > 1)

        if len(self._checkboxes) != n_channels:
            for checkbox in self._checkboxes:
                self.layout().removeWidget(checkbox)
                checkbox.deleteLater()
            self._checkboxes = []
            for channel in range(n_channels):
                checkbox = QCheckBox(f"Channel {channel}", self)
                checkbox.clicked.connect(self.update_operator_from_gui)
                self.layout().addWidget(checkbox)
                self._checkboxes.append(checkbox)

    def _ensure_selection_value(self, *_):
        if not self._raw_slot.ready():
            self._selection_slot.disconnect()
            return
        n_channels = self._raw_slot.meta.getTaggedShape().get("c", 1) if self._raw_slot.ready() else 0
        if not self._selection_slot.ready():
            self._selection_slot.setValue(tuple(range(n_channels)))
        else:
            selection = self._selection_slot.value
            if selection == ():
                return
            selection = tuple((s for s in selection if s < n_channels))
            self._selection_slot.setValue(selection)
