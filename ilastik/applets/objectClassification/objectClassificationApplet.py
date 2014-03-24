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

from opObjectClassification import OpObjectClassification
from objectClassificationSerializer import ObjectClassificationSerializer


class ObjectClassificationApplet(StandardApplet):
    """An applet for labeling and classifying objects."""
    def __init__(self,
                 name="Object Classification",
                 workflow=None,
                 projectFileGroupName="ObjectClassification"):
        self._topLevelOperator = OpObjectClassification(parent=workflow)
        self.predict_enabled = False
        super(ObjectClassificationApplet, self).__init__(name=name, workflow=workflow)

        self._serializableItems = [
            ObjectClassificationSerializer(projectFileGroupName,
                                           self.topLevelOperator)]


    @property
    def topLevelOperator(self):
        return self._topLevelOperator

    @property
    def dataSerializers(self):
        return self._serializableItems

    @property
    def singleLaneGuiClass(self):
        from objectClassificationGui import ObjectClassificationGui
        return ObjectClassificationGui
