from lazyflow.classifiers import IIBoostLazyflowClassifierFactory

from ilastik.applets.pixelClassification import OpPixelClassification
from ilastik.applets.base.applet import DatasetConstraintError

class OpIIBoostPixelClassification(OpPixelClassification):

    DEFAULT_NUM_STUMPS = 200
    
    def __init__(self, *args, **kwargs):
        super( OpIIBoostPixelClassification, self ).__init__( *args, **kwargs )
        
        # Manually override the default classifier type
        self.ClassifierFactory._defaultValue = \
            IIBoostLazyflowClassifierFactory(num_stumps=self.DEFAULT_NUM_STUMPS, 
                                             gtNegativeLabel=1, gtPositiveLabel=2, debugOutput=True)
        
        # We only permit two label classes.
        # In IIBoost, non-synapse is hard-coded to label 1, synapse is label 2
        self.LabelNames.setValue( ["Non-synapse", "Synapse"] )

    def get_num_stumps(self):
        return self.ClassifierFactory.value.num_stumps
    
    def set_num_stumps(self, num_stumps):
        factory = IIBoostLazyflowClassifierFactory(num_stumps=num_stumps, 
                                                   gtNegativeLabel=1, gtPositiveLabel=2, debugOutput=True)
        self.ClassifierFactory.setValue( factory )

    def _checkConstraints(self, laneIndex):
        """
        Override from OpPixelClassification.
        
        Check all input slots for appropriate size/shape, etc. 
        """
        if not self.InputImages[laneIndex].ready():
            return

        tagged_shape = self.InputImages[laneIndex].meta.getTaggedShape()

        if 't' in tagged_shape:
            raise DatasetConstraintError(
                 "IIBoost Pixel Classification",
                 "This classifier handles only 3D data. Your input data has a time dimension, which is not allowed.")

        if not set('xyz').issubset(tagged_shape.keys()):
            raise DatasetConstraintError(
                 "IIBoost Pixel Classification",
                 "This classifier handles only 3D data. Your input data does not have all three spatial dimensions (xyz).")
        
        super(OpIIBoostPixelClassification, self)._checkConstraints(laneIndex)
