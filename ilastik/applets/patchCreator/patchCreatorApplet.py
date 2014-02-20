# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Copyright 2011-2014, the ilastik developers

from ilastik.applets.base.standardApplet import StandardApplet
from opPatchCreator import OpPatchCreator
from patchCreatorSerializer import PatchCreatorSerializer
from lazyflow.graph import OperatorWrapper

class PatchCreatorApplet( StandardApplet ):
    def __init__( self, workflow, projectFileGroupName ):
        super(PatchCreatorApplet, self).__init__("Patch Creator", workflow)
        self._serializableItems = [PatchCreatorSerializer(self.topLevelOperator,
                                                          projectFileGroupName)]

    @property
    def singleLaneOperatorClass(self):
        return OpPatchCreator

    @property
    def broadcastingSlots(self):
        return ["PatchWidth", "PatchHeight",
                "PatchOverlapVertical", "PatchOverlapHorizontal",
                "GridStartVertical", "GridStartHorizontal",
                "GridWidth", "GridHeight"]

    @property
    def singleLaneGuiClass(self):
        from patchCreatorGui import PatchCreatorGui
        return PatchCreatorGui

    @property
    def dataSerializers(self):
        return self._serializableItems
