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

import helpers
import jsonConfig
import slicingtools
from singleton import Singleton
from orderedSignal import OrderedSignal
from fileLock import FileLock
from tracer import Tracer, traceLogged
from pathHelpers import PathComponents, getPathVariants, isUrl
from roiRequestBatch import RoiRequestBatch
from bigRequestStreamer import BigRequestStreamer
import io
from lazyflow.utility.fastWhere import fastWhere
from format_known_keys import format_known_keys
from timer import Timer, timeLogged