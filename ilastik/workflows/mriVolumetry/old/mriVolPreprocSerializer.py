from ilastik.applets.base.appletSerializer import AppletSerializer, SerialSlot, SerialHdf5BlockSlot

class MriVolPreprocSerializer( AppletSerializer ):
    def __init__(self, operator, projectFileGroupName):
        slots = [SerialSlot(operator.Sigma, selfdepends=True),
                 SerialHdf5BlockSlot(operator.OutputHdf5,
                                     operator.InputHdf5,
                                     operator.CleanBlocks,
                                     name="CachedThresholdOutput")
                ]

        super(self.__class__, self).__init__(projectFileGroupName, slots=slots)
