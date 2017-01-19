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

class WatershedSegmentationSerializer(AppletSerializer):
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
                #Seeds supplied is delivered from applet Seeds, therefore don't save it
                #SerialSlot(operator.SeedsExist), 

                # WSMethod will be delivered (also on restart) by Applet Seeds and needn't to be cached 

                # neighbors
                SerialSlot(operator.WSNeighbors), 

                # serialize the slots for the LabelListModel
                # because we use a list, we have to transform it to something, the 
                # SerialListSlot can work with. 
                SerialListSlot(operator.LabelNames, transform=str),
                SerialListSlot(operator.LabelColors, transform=lambda x: tuple(x.flat)),
                SerialListSlot(operator.PmapColors, transform=lambda x: tuple(x.flat)),

                # serialize the Labels of the user, so that the data (not the Labels)
                # are shown after project restart
                SerialBlockSlot(operator.CorrectedSeedsOut,
                    operator.CorrectedSeedsIn,
                    operator.NonZeroBlocks,
                    name='LabelSets',
                    subname='labels{:03d}',
                    selfdepends=False,
                    shrink_to_bb=True),
                # used to remember to show the watershed result layer 
                SerialSlot(operator.ShowWatershedLayer), 
                #SerialSlot(operator.UseCachedLabels), 

                # serialize the output of the watershed algorithm, 
                # so it won't be lost after restarting the project
                SerialHdf5BlockSlot(operator.WSCCOOutputHdf5,
                    operator.WSCCOInputHdf5,
                    operator.WSCCOCleanBlocks,
                    name="CachedWatershedOutput")
                ]
        super(WatershedSegmentationSerializer, self).__init__(projectFileGroupName, slots=slots, operator=operator)

