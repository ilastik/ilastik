###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2019, the ilastik team
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
#           http://ilastik.org/license.html
###############################################################################
from ilastik.utility.operatorSubView import OperatorSubView
from lazyflow.graph import Operator, InputSlot, OutputSlot

from typing import Optional, Dict

DEFAULT_LOCAL_SERVER_CONFIG = {'username': '', 'password': '',
                         'address': 'localhost', 'port1': '5556', 'port2': '5557', 'devices': []}
# use remote defaults as user hints
DEFAULT_REMOTE_SERVER_CONFIG = {'username': 'SSH user name', 'password': 'SSH password (no encrytpion!)', 'ssh_key': 'SSH key',
                                'address': 'remote host or IP address', 'port1': '5556', 'port2': '5557', 'devices': []}


class OpServerConfig(Operator):
    name = "OpServerConfig"
    category = "top-level"

    LocalServerConfig = InputSlot(value=dict(DEFAULT_LOCAL_SERVER_CONFIG))
    RemoteServerConfig = InputSlot(value=dict(DEFAULT_REMOTE_SERVER_CONFIG))
    UseLocalServer = InputSlot()

    ServerConfig = OutputSlot()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def setLocalServerConfig(self, config: Optional[Dict] = None):
        if config is None:
            config = dict(DEFAULT_LOCAL_SERVER_CONFIG)
        self.LocalServerConfig.setValue(config)

    def setRemoteServerConfig(self, config: Optional[Dict] = None):
        if config is None:
            config = dict(DEFAULT_REMOTE_SERVER_CONFIG)
        self.RemoteServerConfig.setValue(config)


    def setupOutputs(self):
        if self.UseLocalServer.value:
            chosen_slot = self.LocalServerConfig
        else:
            chosen_slot = self.RemoteServerConfig

        if chosen_slot.value["devices"]:
            self.ServerConfig.connect(chosen_slot)
        else:
            self.ServerConfig.disconnect()
            self.ServerConfig.meta.NOTREADY = True

    def propagateDirty(self, slot, subindex, roi):
        pass

    def execute(self, slot, subindex, roi, result):
        pass

    def addLane(self, laneIndex):
        pass

    def removeLane(self, laneIndex, finalLength):
        pass

    def getLane(self, laneIndex):
        return OperatorSubView(self, laneIndex)
