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

import logging
logger = logging.getLogger(__name__)

import pixelClassification

try:
    import objectClassification
except ImportError as e:
    logger.warn("Failed to import object workflow; check dependencies: " + str(e))

try:
    import carving 
except ImportError as e:
    logger.warn( "Failed to import carving workflow; check cylemon dependency: " + str(e) )

try:
    import tracking
except ImportError as e:
    logger.warn( "Failed to import tracking workflow; check pgmlink dependency: " + str(e) )
    
try:
    import counting
except ImportError as e:
    logger.warn("Failed to import counting workflow; check dependencies: " + str(e))


# Examples
import ilastik.config

if ilastik.config.cfg.getboolean('ilastik', 'debug'):
    import vigraWatershed
    import examples.layerViewer
    import examples.thresholdMasking
    import examples.deviationFromMean
    import examples.labeling
    import examples.dataConversion
