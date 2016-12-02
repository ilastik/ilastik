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

class WatershedSegmentationSerializer(AppletSerializer):
    """
    Add all the slots, you want to use in the gui later, into its __init__
    operator is mainly the topLevelOperator
    """
    
    def __init__(self, operator, projectFileGroupName):
        """
        "param operator: normally the top-level-operator
        the slots list must include at least all broadcasted slots
        from the applet-class

        can include more than these slot: e.g. all slots, that are not viewed in the gui, 
        (means, no input paramters but cached images)
        """
        slots = [ #SerialSlot(operator.ChannelSelection),
                  #SerialSlot(operator.BrushValue),
                  SerialListSlot(operator.LabelNames, transform=str),
                  SerialListSlot(operator.LabelColors, transform=lambda x: tuple(x.flat)),
                  SerialListSlot(operator.PmapColors, transform=lambda x: tuple(x.flat)),
                  #used to remember to show the watershed result layer 
                  SerialSlot(operator.ShowWatershedLayer), 
                  SerialSlot(operator.UseCachedLabels), 
                  SerialHdf5BlockSlot(operator.WSCCOOutputHdf5,
                                      operator.WSCCOInputHdf5,
                                      operator.WSCCOCleanBlocks,
                                      name="CachedWatershedOutput")
                  #SerialHdf5BlockSlot(operator.LabelOutputHdf5,
                                      #operator.LabelInputHdf5,
                                      #operator.LabelCleanBlocks,
                                      #name="CorrectedSeedsOutCached")
                ]
        super(WatershedSegmentationSerializer, self).__init__(projectFileGroupName, slots=slots, operator=operator)


    #TODO copied from pixelclassification. maybe needed, maybe not
    def _deserializeFromHdf5(self, topGroup, groupVersion, hdf5File, projectFilePath):
        """
        Override from AppletSerializer.
        Implement any additional deserialization that wasn't already accomplished by our list of serializable slots.
        """
        # If this is an old project file that didn't save the label names to the project,
        #   create some default names.
        if (not self.operator.LabelNames.ready() or len(self.operator.LabelNames.value) == 0)\
        and 'LabelSets' in topGroup:
            # How many labels are there?
            # We have to count them.  
            # This is slow, but okay for this special backwards-compatibilty scenario.

            # For each image
            all_labels = set()
            for image_index, group in enumerate(topGroup['LabelSets'].values()):
                # For each label block
                for block in group.values():
                    data = block[:]
                    all_labels.update( numpy.unique(data) )

            if all_labels:
                max_label = max(all_labels)
            else:
                max_label = 0
            
            label_names = []
            for i in range(max_label):
                label_names.append( "Label {}".format( i+1 ) )
            
            self.operator.LabelNames.setValue( label_names )
            # Make some default colors, too
            default_colors = [(255,0,0),
                              (0,255,0),
                              (0,0,255),
                              (255,255,0),
                              (255,0,255),
                              (0,255,255),
                              (128,128,128),
                              (255, 105, 180),
                              (255, 165, 0),
                              (240, 230, 140) ]
            colors = []
            for i, _ in enumerate(label_names):
                colors.append( default_colors[i] )
            self.operator.LabelColors.setValue( colors )
            self.operator.PmapColors.setValue( colors )
            
            # Now RE-deserialize the classifier, so it isn't marked dirty
            self._serialClassifierSlot.deserialize(topGroup)

        # SPECIAL CLEANUP for backwards compatibility:
        # Due to a bug, it was possible for a project to be saved with a classifier that was 
        #  trained with more label classes than the project file saved in the end.
        # That can cause a crash.  So here, we inspect the restored classifier and remove it if necessary.
        if not self.operator.classifier_cache._dirty:
            restored_classifier = self.operator.classifier_cache._value
            if hasattr(restored_classifier, 'known_classes'):
                num_classifier_classes = len(restored_classifier.known_classes)
                num_saved_label_classes = len(self.operator.LabelNames.value)
                if num_classifier_classes > num_saved_label_classes:
                    # Delete the classifier from the operator
                    logger.info( "Resetting classifier... will be forced to retrain" )
                    self.operator.classifier_cache.resetValue()
