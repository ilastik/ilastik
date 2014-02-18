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

from opCounting import OpCounting
from countingSerializer import CountingSerializer

class CountingApplet(StandardApplet):
    def __init__(self,
                 name="Counting",
                 workflow=None,
                 projectFileGroupName="Counting"):
        self._topLevelOperator = OpCounting(parent=workflow)
        super(CountingApplet, self).__init__(name=name, workflow=workflow)

        #self._serializableItems = [
        #    ObjectClassificationSerializer(projectFileGroupName,
        #                                   self.topLevelOperator)]
        self._serializableItems = [CountingSerializer(self._topLevelOperator, projectFileGroupName)]   # Legacy (v0.5) importer
        self.predictionSerializer = self._serializableItems[0]

        self._topLevelOperator.opTrain.progressSignal.subscribe(self.progressSignal.emit)

    @property
    def topLevelOperator(self):
        return self._topLevelOperator

    @property
    def dataSerializers(self):
        return self._serializableItems

    @property
    def singleLaneGuiClass(self):
        from countingGui import CountingGui
        return CountingGui
