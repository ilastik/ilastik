from ilastik.applets.pixelClassification.pixelClassificationGui import PixelClassificationGui

class IIBoostPixelClassificationGui( PixelClassificationGui ):
    
    def __init__(self, *args, **kwargs):
        super(IIBoostPixelClassificationGui, self).__init__(*args, **kwargs)

        # Init special base class members
        # (See LabelingGui base class)
        self.minLabelNumber = 2
        self.maxLabelNumber = 2

