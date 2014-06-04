###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2014, the ilastik developers
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
import logging
logger = logging.getLogger(__name__)

try:
    from chaingraph.chaingraphTrackingWorkflow import ChaingraphTrackingWorkflow 
except ImportError as e:
    logger.warn( "Failed to import automatic tracking workflow (chaingraph). For this workflow, see the installation"\
                 "instructions on our website ilastik.org; check dependencies: " + str(e) )

try:    
    from manual.manualTrackingWorkflow import ManualTrackingWorkflow
except ImportError as e:
    logger.warn( "Failed to import manual tracking workflow; check dependencies: " + str(e) )
    
try:    
    from conservation.conservationTrackingWorkflow import ConservationTrackingWorkflow
except ImportError as e:
    logger.warn( "Failed to import conservation tracking workflow; check dependencies: " + str(e) )
    
#try:    
#    from conservation.conservationTrackingWorkflow import ConservationTrackingWorkflowWithOptTrans
#except ImportError as e:
#    logger.warn( "Failed to import conservation tracking workflow; check dependencies: " + str(e) )
    
try:    
    from conservation.conservationTrackingWorkflow import ConservationTrackingWorkflowFromBinary
except ImportError as e:
    logger.warn( "Failed to import conservation tracking workflow (from binary); check dependencies: " + str(e) )
    
