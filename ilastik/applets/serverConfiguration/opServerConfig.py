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
from lazyflow import stype

from typing import Optional, Dict

from .configStorage import SERVER_CONFIG


class OpServerConfig(Operator):
    name = "OpServerConfig"
    category = "top-level"

    ServerId = InputSlot(stype=stype.Opaque)

    ServerConfig = OutputSlot(stype=stype.Opaque)

    def setupOutputs(self):
        serverId = self.ServerId.value
        srv = SERVER_CONFIG.get_server(serverId)
        if srv:
            self.ServerConfig.meta.NOTREADY = False
            self.ServerConfig.setValue(srv)
        else:
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
