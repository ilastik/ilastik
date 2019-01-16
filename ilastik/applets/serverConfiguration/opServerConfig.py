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
#		   http://ilastik.org/license.html
###############################################################################
from ilastik.utility.operatorSubView import OperatorSubView
from lazyflow.graph import Operator, InputSlot

DEFAULT_CONFIG = {'username': None, 'password': None,
                  'address': '127.0.0.1', 'port': '29500',
                  'meta_port': '29501'}

class OpServerConfig(Operator):
    name = "OpServerConfig"
    category = "top-level"

    ServerConfigIn = InputSlot()

    def __init__(self, *args, **kwargs):
        super(OpServerConfig, self).__init__(*args, **kwargs)
        self.ServerConfigIn.setValue(DEFAULT_CONFIG)

    def setServerConfig(self, config: dict = DEFAULT_CONFIG):
        self.ServerConfigIn.setValue(config)

    def setupOutputs(self):
        pass

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
