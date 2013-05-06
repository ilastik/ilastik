from ilastik.applets.base.appletSerializer import AppletSerializer, SerialBlockSlot

class LabelingSerializer(AppletSerializer):
    """Encapsulate the serialization scheme for pixel classification
    workflow parameters and datasets.

    """
    def __init__(self, operator, projectFileGroupName):
        slots = [SerialBlockSlot(operator.LabelImages,
                                 operator.LabelInputs,
                                 operator.NonzeroLabelBlocks,
                                 name='LabelSets',
                                 subname='labels{:03d}',)
        ]
        super(LabelingSerializer, self).__init__(projectFileGroupName, slots=slots)
