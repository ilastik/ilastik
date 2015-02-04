from ilastik.applets.pixelClassification import PixelClassificationGui

class IiBoostPixelClassificationGui( PixelClassificationGui ):
    
    def __init__(self, *args, **kwargs):
        super(IiBoostPixelClassificationGui, self).__init__(*args, **kwargs)

        # Init special base class members
        # (See LabelingGui base class)
        self.minLabelNumber = 2
        self.maxLabelNumber = 2

