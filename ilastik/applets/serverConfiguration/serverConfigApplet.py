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
from ilastik.applets.base.standardApplet import StandardApplet
from .opServerConfig import OpServerConfig
from .serverConfigSerializer import ServerConfigSerializer

class ServerConfigApplet(StandardApplet):
    def __init__(self, workflow):
        self._topLevelOperator = OpServerConfig(parent=workflow)
        super().__init__("Server configuration", workflow)
        self._serializableItems = [ServerConfigSerializer('ServerConfiguration', operator=self._topLevelOperator)]

    @property
    def topLevelOperator(self):
        return self._topLevelOperator

    @property
    def singleLaneGuiClass(self):
        from .serverConfigGui import ServerConfigGui
        return ServerConfigGui

    @property
    def broadcastingSlots(self):
        return []

    @property
    def dataSerializers(self):
        return self._serializableItems
