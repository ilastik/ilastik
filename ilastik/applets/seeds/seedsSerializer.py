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
#           http://ilastik.org/license.html
###############################################################################
from ilastik.applets.base.appletSerializer import AppletSerializer, SerialSlot, \
                                             SerialBlockSlot, SerialHdf5BlockSlot, SerialListSlot
import logging
logger = logging.getLogger(__name__)

class SeedsSerializer(AppletSerializer):
    """
    Add all the slots, you want to use in the gui later, into its __init__
    These slots are stored/cached, so that they can be used after project restart. 

    e.g. the result of a calculation can be stored in cache, so that it can be 
    reviewed after a project restart without calculating once more.
    """
    
    def __init__(self, operator, projectFileGroupName):
        """
        the slots list must include at least all broadcasted slots
        from the applet-class

        can include more than these slot: e.g. all slots, that are not viewed in the gui, 
        (means, no input paramters but cached images)

        :param operator: normally the top-level-operator
        """

        slots = [ 
                ]
        super(SeedsSerializer, self).__init__(projectFileGroupName, slots=slots, operator=operator)

