from ilastik.applets.base.appletSerializer import AppletSerializer

class PredictionViewerSerializer(AppletSerializer):

    def __init__(self, topLevelOperator, predictionGroupName):
        super(PredictionViewerSerializer, self).__init__("PredictionViewer")
        self._predictionGroupName = predictionGroupName
        self._topLevelOperator = topLevelOperator
    
    def serializeToHdf5(self, hdf5File, projectFilePath):
        pass
    
    def deserializeFromHdf5(self, hdf5File, projectFilePath):
        try:
            predictionGroup = hdf5File[self._predictionGroupName]
        except:
            return

        pmapColors = None
        labelNames = None
        try:        
            pmapColors = predictionGroup['PmapColors'].value
            self._topLevelOperator.PmapColors.setValue( list(pmapColors) )
            
        except KeyError:
            pass

        try:        
            labelNames = predictionGroup['LabelNames'].value
            self._topLevelOperator.LabelNames.setValue( list(labelNames) )
        except KeyError:
            pass
    
    

    