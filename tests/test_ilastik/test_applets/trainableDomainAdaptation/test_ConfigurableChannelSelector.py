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
import pytest

from ilastik.applets.trainableDomainAdaptation.trainableDomainAdaptationGui import ConfigurableChannelSelector


@pytest.fixture
def widget(qtbot):
    widget = ConfigurableChannelSelector(["Ch 1", "Ch 2", "Ch 3", "Ch 4"])
    qtbot.addWidget(widget)
    return widget


def test_initial_text(widget):
    assert widget.text() == "Select a channel..."


def test_single_channel_selection(widget):
    action = widget._channel_menu.actions()[2]
    action.trigger()
    assert widget.text() == "Ch 3"


def test_no_channel_selection(widget):
    for action in widget._channel_menu.actions():
        action.setChecked(False)

    widget.onChannelSelectionClicked(None)

    assert widget.text() == "Select a channel..."


def test_emit_updated_signal(widget, qtbot):

    with qtbot.waitSignal(widget.channelSelectionFinalized, timeout=100) as sig_receiver:
        action = widget._channel_menu.actions()[1]
        action.trigger()

    assert sig_receiver.args == [[1]]


def test_update_options(widget):
    # check "init" state from fixture
    assert len(widget._channel_menu.actions()) == 4
    assert widget._n_options == 1

    widget.update_options(["A", "B", "C"], n_options=2)
    assert len(widget._channel_menu.actions()) == 3
    assert widget._n_options == 2


def test_update_options_resets_selection(widget, qtbot):
    assert widget.text() == "Select a channel..."
    widget._channel_menu.actions()[3].trigger()
    assert widget.text() == "Ch 4"

    with qtbot.waitSignal(widget.channelSelectionFinalized, timeout=100) as sig_receiver:
        widget.update_options(["A"], n_options=1)

    assert sig_receiver.args == [[]]
    assert widget.text() == "Select a channel..."


def test_multiple_options(qtbot):
    widget = ConfigurableChannelSelector(["Ch 1", "Ch 2", "Ch 3", "Ch 4"], n_options=3)
    qtbot.addWidget(widget)

    with qtbot.assertNotEmitted(widget.channelSelectionFinalized):
        widget._channel_menu.actions()[0].trigger()
        widget._channel_menu.actions()[3].trigger()

    with qtbot.waitSignal(widget.channelSelectionFinalized, timeout=100) as sig_receiver:
        widget._channel_menu.actions()[1].trigger()

    assert sig_receiver.args == [[0, 1, 3]]
    assert widget.text() == "Ch 1, Ch 2, Ch 4"
