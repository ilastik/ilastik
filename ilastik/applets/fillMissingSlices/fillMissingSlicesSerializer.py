from ilastik.applets.base.appletSerializer import AppletSerializer


class FillMissingSlicesSerializer(AppletSerializer):


    ### reimplementation of methods ###
        
    def __init__(self, topGroupName, topLevelOperator):
        super( FillMissingSlicesSerializer, self ).__init__(topGroupName)
        self._operator = topLevelOperator
    
    def _serializeToHdf5(self, topGroup, hdf5File, projectFilePath):
        #FIXME OperatorSubView
        for i, s in enumerate(self._operator.innerOperators):
            self._setDataset(topGroup, 'SVM_%d'%i, s.dumps())
        
    def _deserializeFromHdf5(self, topGroup, groupVersion, hdf5File, projectFilePath):
        #FIXME OperatorSubView
        for i, s in enumerate(self._operator.innerOperators):
            s.loads(self._getDataset(topGroup, 'SVM_%d'%i))
        

    def isDirty(self):
        #FIXME OperatorSubView
        return any([s.isDirty() for s in self._operator.innerOperators])
    
    
    ### internal ###

    def _setDataset(self, group, dataName, dataValue):
        if dataName not in group.keys():
            # Create and assign
            group.create_dataset(dataName, data=dataValue)
        else:
            # Assign (this will fail if the dtype doesn't match)
            group[dataName][()] = dataValue

    def _getDataset(self, group, dataName):
        try:
            result = group[dataName].value
        except KeyError:
            result = ''
        return result 
