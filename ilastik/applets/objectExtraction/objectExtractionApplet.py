from ilastik.applets.base.standardApplet import StandardApplet
from ilastik.applets.objectExtraction.opObjectExtraction import OpObjectExtraction
from ilastik.applets.objectExtraction.objectExtractionSerializer import ObjectExtractionSerializer

class ObjectExtractionApplet(StandardApplet):
    """Calculates object features for each object in an image.

    Features are provided by plugins, which are responsible for
    performing the actual computation.

    """

    def __init__(self, name="Object Extraction", workflow=None,
                 projectFileGroupName="ObjectExtraction",
                 interactive=True):
        super(ObjectExtractionApplet, self).__init__(name=name, workflow=workflow)
        self._serializableItems = [ ObjectExtractionSerializer(self.topLevelOperator, projectFileGroupName) ]
        self._interactive = interactive

    @property
    def singleLaneOperatorClass(self):
        return OpObjectExtraction

    @property
    def broadcastingSlots(self):
        return ['Features']

    @property
    def singleLaneGuiClass(self):
        from ilastik.applets.objectExtraction.objectExtractionGui import ObjectExtractionGui
        from ilastik.applets.objectExtraction.objectExtractionGui import ObjectExtractionGuiNonInteractive
        if self._interactive:
            return ObjectExtractionGui
        else:
            return ObjectExtractionGuiNonInteractive

    @property
    def dataSerializers(self):
        return self._serializableItems
