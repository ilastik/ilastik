from ilastik.applets.base.appletSerializer import AppletSerializer

class ObjectExtractionMultiClassSerializer(AppletSerializer):
    """
    """
    SerializerVersion = 0.1
    
    def __init__(self, mainOperator, projectFileGroupName):
        super( ObjectExtractionMultiClassSerializer, self ).__init__( projectFileGroupName, self.SerializerVersion )
        self.mainOperator = mainOperator

    def _serializeToHdf5(self, topGroup, hdf5File, projectFilePath):
        op = self.mainOperator.innerOperators[0]
        print "object extraction multi class: serializeToHdf5", topGroup, hdf5File, projectFilePath
        
        if len(self.mainOperator.innerOperators[0]._opObjectExtractionBg._opLabelImage._processedTimeSteps) > 0:
            print "object extraction multi class: saving label image"        
            src = op._opObjectExtractionBg._opLabelImage._mem_h5
            self.deleteIfPresent( topGroup, "LabelImage")
            src.copy('/LabelImage', topGroup) 

        print "object extraction multi class: saving region features"
        self.deleteIfPresent( topGroup, "samples")
        samples_gr = self.getOrCreateGroup( topGroup, "samples" )
        for t in op._opObjectExtractionBg._opRegFeats._cache.keys():
            t_gr = samples_gr.create_group(str(t))
            t_gr.create_dataset(name="RegionCenter", data=op._opObjectExtractionBg._opRegFeats._cache[t]['RegionCenter'])
            t_gr.create_dataset(name="Count", data=op._opObjectExtractionBg._opRegFeats._cache[t]['Count'])
            t_gr.create_dataset(name="CoordArgMaxWeight", data=op._opObjectExtractionBg._opRegFeats._cache[t]['Coord<ArgMaxWeight>'])

        print "object extraction multi class: class probabilities"
        self.deleteIfPresent(topGroup, "ClassProbabilities")
        classprob_gr = self.getOrCreateGroup(topGroup, "ClassProbabilities")
        for t in op._opClassExtraction._cache.keys():
            classprob_gr.create_dataset(name=str(t), data=op._opClassExtraction._cache[t])        
        
        
    def _deserializeFromHdf5(self, topGroup, groupVersion, hdf5File, projectFilePath):
        print "objectExtraction multi class: deserializeFromHdf5", topGroup, groupVersion, hdf5File, projectFilePath
        
        print "objectExtraction multi class: loading label image"
        dest = self.mainOperator.innerOperators[0]._opObjectExtractionBg._opLabelImage._mem_h5        
        
        if 'LabelImage' in topGroup.keys():            
            del dest['LabelImage']
            topGroup.copy('LabelImage', dest)
        
            self.mainOperator.innerOperators[0]._opObjectExtractionBg._opLabelImage._fixed = False        
            self.mainOperator.innerOperators[0]._opObjectExtractionBg._opLabelImage._processedTimeSteps = range(topGroup['LabelImage'].shape[0])            


        print "objectExtraction multi class: loading region features"
        if "samples" in topGroup.keys():
            cache = {}

            for t in topGroup["samples"].keys():
                cache[int(t)] = dict()
                if 'RegionCenter' in topGroup["samples"][t].keys():
                    cache[int(t)]['RegionCenter'] = topGroup["samples"][t]['RegionCenter'].value
                if 'Count' in topGroup["samples"][t].keys():                    
                    cache[int(t)]['Count'] = topGroup["samples"][t]['Count'].value
                if 'CoordArgMaxWeight' in topGroup["samples"][t].keys():
                    cache[int(t)]['Coord<ArgMaxWeight>'] = topGroup["samples"][t]['CoordArgMaxWeight'].value            
            self.mainOperator.innerOperators[0]._opObjectExtractionBg._opRegFeats._cache = cache
        
        print "objectExtraction multi class: loading class probabilities"        
        if "ClassProbabilities" in topGroup.keys():
            cache = {}
            for t in topGroup["ClassProbabilities"].keys():
                cache[int(t)] = topGroup["ClassProbabilities"][t].value                
        self.mainOperator.innerOperators[0]._opClassExtraction._cache = cache
        

    def isDirty(self):
        return True
    
    
    def unload(self):
        print "ObjExtraction.unload not implemented" 

