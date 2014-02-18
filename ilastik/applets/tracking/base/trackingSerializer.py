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

from ilastik.applets.base.appletSerializer import AppletSerializer,\
    SerialDictSlot, SerialSlot, SerialHdf5BlockSlot

class TrackingSerializer(AppletSerializer):
    
    def __init__(self, mainOperator, projectFileGroupName):
        slots = [SerialDictSlot(mainOperator.Parameters, selfdepends=True),
#                  SerialSlot(mainOperator.Output, selfdepends=True),
                 SerialHdf5BlockSlot(mainOperator.OutputHdf5,
                                     mainOperator.InputHdf5,
                                     mainOperator.CleanBlocks,
                                     name="CachedOutput"),
                 SerialDictSlot(mainOperator.EventsVector, transform=str, selfdepends=True),
                 SerialDictSlot(mainOperator.FilteredLabels, transform=str, selfdepends=True),
                 ]
        super( TrackingSerializer, self ).__init__( projectFileGroupName, slots=slots )
        