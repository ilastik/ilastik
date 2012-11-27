from ilastik.applets.base.appletSerializer import \
    AppletSerializer, stringToSlicing, slicingToString, \
    deleteIfPresent, SerialBlockSlot

class LabelingSerializer(AppletSerializer):
    """Encapsulate the serialization scheme for pixel classification
    workflow parameters and datasets.

    """
    SerializerVersion = 0.1
    
    def __init__(self, operator, projectFileGroupName):
        slots = [SerialBlockSlot(operator.LabelInputs,
                                 operator.LabelImages,
                                 operator.NonzeroLabelBlocks,
                                 name=('LabelSets', 'labels{:03d}'))
        ]
        super(LabelingSerializer, self).__init__(projectFileGroupName,
                                                 self.SerializerVersion)
