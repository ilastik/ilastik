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

from ilastik.applets.base.appletSerializer import AppletSerializer, SerialSlot

class PatchCreatorSerializer(AppletSerializer):
    """Serializes the user's settings in the "Steerable Pyramid"
    applet to an ilastik v0.6 project file.

    """
    def __init__(self, topLevelOperator, projectFileGroupName):
        slots = [SerialSlot(topLevelOperator.PatchWidth, selfdepends=True),
                 SerialSlot(topLevelOperator.PatchHeight, selfdepends=True),
                 SerialSlot(topLevelOperator.PatchOverlapVertical, selfdepends=True),
                 SerialSlot(topLevelOperator.PatchOverlapHorizontal, selfdepends=True),
                 SerialSlot(topLevelOperator.GridStartVertical, selfdepends=True),
                 SerialSlot(topLevelOperator.GridStartHorizontal, selfdepends=True),
                 SerialSlot(topLevelOperator.GridWidth, selfdepends=True),
                 SerialSlot(topLevelOperator.GridHeight, selfdepends=True)]

        super(PatchCreatorSerializer, self).__init__(projectFileGroupName,
                                                         slots=slots)
        self.topLevelOperator = topLevelOperator
