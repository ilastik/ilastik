from ilastik.applets.base.appletSerializer import AppletSerializer, deleteIfPresent,\
    getOrCreateGroup

class ObjectExtractionMultiClassSerializer(AppletSerializer):
    """
    """
    SerializerVersion = 0.1
    
    def __init__(self, mainOperator, projectFileGroupName):
        super( ObjectExtractionMultiClassSerializer, self ).__init__( projectFileGroupName )
        self.mainOperator = mainOperator
        self._dirty = False
            
    def _serializeToHdf5(self, topGroup, hdf5File, projectFilePath):
        op = self.mainOperator.innerOperators[0]
        print "object extraction multi class: serializeToHdf5", topGroup, hdf5File, projectFilePath
        
        assert False, "FIXME: OpLabelImage implementation has changed, not longer has _processedTimeSteps member"
        if len(self.mainOperator.innerOperators[0]._opObjectExtraction._opLabelImage._processedTimeSteps) > 0:
            print "object extraction multi class: saving label image"        
            src = op._opObjectExtraction._opLabelImage._mem_h5
            # TODO: only save the label image if all the time steps are processed?
            deleteIfPresent( topGroup, "LabelImage")
            src.copy('/LabelImage', topGroup) 

        print "object extraction multi class: saving region features"
        deleteIfPresent( topGroup, "samples")
        samples_gr = getOrCreateGroup( topGroup, "samples" )        
        for t in op._opObjectExtraction._opRegFeats._cache.keys():
            t_gr = samples_gr.create_group(str(t))
            for ch in range(len(op._opObjectExtraction._opRegFeats._cache[t])):            
                ch_gr = t_gr.create_group(str(ch))
                ch_gr.create_dataset(name="RegionCenter", data=op._opObjectExtraction._opRegFeats._cache[t][ch]['RegionCenter'])
                ch_gr.create_dataset(name="Count", data=op._opObjectExtraction._opRegFeats._cache[t][ch]['Count'])
                ch_gr.create_dataset(name="CoordArgMaxWeight", data=op._opObjectExtraction._opRegFeats._cache[t][ch]['Coord<ArgMaxWeight>'])

        print "object extraction multi class: class probabilities"
        deleteIfPresent(topGroup, "ClassProbabilities")
        classprob_gr = getOrCreateGroup(topGroup, "ClassProbabilities")
        for t in op._opClassExtraction._cache.keys():
            classprob_gr.create_dataset(name=str(t), data=op._opClassExtraction._cache[t])        
        
#        if len(self.mainOperator.innerOperators[0]._opDistanceTransform._processedTimeSteps) > 0:
#            print "object extraction multi class: distance transform"
#            src = op._opDistanceTransform._mem_h5
#            deleteIfPresent(topGroup, "DistanceTransform")
#            src.copy('/DistanceTransform', topGroup)
        
#        if len(self.mainOperator.innerOperators[0]._opRegionalMaximum._processedTimeSteps) > 0:
#            print "object extraction multi class: maximum image"
#            src = op._opRegionalMaximum._mem_h5
#            deleteIfPresent(topGroup, "MaximumImage")
#            src.copy('/MaximumImage', topGroup)
        
        ## Do not save the region local centers, it takes ages! In fact, they are computed quite fast...
#        print "object extraction multi class: region local centers"
#        deleteIfPresent( topGroup, "RegionLocalCenters")
#        samples_gr = getOrCreateGroup( topGroup, "RegionLocalCenters" )        
#        for t in op._opRegionalMaximum._cache.keys():       
#            t_gr = samples_gr.create_group(str(t))
#            for label,rlc in enumerate(op._opRegionalMaximum._cache[t]):
#                if len(rlc) > 0:
#                    t_gr.create_dataset(name=str(label), data=rlc, dtype=numpy.uint8,compression=1)
#        print "region local centers: done"  
        self._dirty = False 

        
    def _deserializeFromHdf5(self, topGroup, groupVersion, hdf5File, projectFilePath):
        print "objectExtraction multi class: deserializeFromHdf5", topGroup, groupVersion, hdf5File, projectFilePath
        
        print "objectExtraction multi class: loading label image"
        assert False, "FIXME: OpLabelImage implementation has changed, not longer has _mem_h5 member"
        dest = self.mainOperator.innerOperators[0]._opObjectExtraction._opLabelImage._mem_h5                
        if 'LabelImage' in topGroup.keys():            
            del dest['LabelImage']
            topGroup.copy('LabelImage', dest)
            # TODO: only deserialize the label image if all the time steps are processed?
            self.mainOperator.innerOperators[0]._opObjectExtraction._opLabelImage._fixed = False        
            assert False, "FIXME: OpLabelImage implementation has changed, not longer has _processedTimeSteps member"
            self.mainOperator.innerOperators[0]._opObjectExtraction._opLabelImage._processedTimeSteps = range(topGroup['LabelImage'].shape[0])            


        print "objectExtraction multi class: loading region features"
        if "samples" in topGroup.keys():
            cache = {}
            for t in topGroup["samples"].keys():
                cache[int(t)] = []
                for ch in sorted(topGroup["samples"][t].keys()):
                    feat = dict()
                    if 'RegionCenter' in topGroup["samples"][t][ch].keys():
                        feat['RegionCenter'] = topGroup["samples"][t][ch]['RegionCenter'].value
                    if 'Count' in topGroup["samples"][t][ch].keys():                    
                        feat['Count'] = topGroup["samples"][t][ch]['Count'].value
                    if 'CoordArgMaxWeight' in topGroup["samples"][t][ch].keys():
                        feat['Coord<ArgMaxWeight>'] = topGroup["samples"][t][ch]['CoordArgMaxWeight'].value
                    cache[int(t)].append(feat)            
            self.mainOperator.innerOperators[0]._opObjectExtraction._opRegFeats._cache = cache
        
        print "objectExtraction multi class: loading class probabilities"        
        if "ClassProbabilities" in topGroup.keys():
            cache = {}
            for t in topGroup["ClassProbabilities"].keys():
                cache[int(t)] = topGroup["ClassProbabilities"][t].value                
        self.mainOperator.innerOperators[0]._opClassExtraction._cache = cache
        
#        print "objectExtraction multi class: loading distance transform image"
#        dest = self.mainOperator.innerOperators[0]._opDistanceTransform._mem_h5                
#        if 'DistanceTransform' in topGroup.keys():            
#            del dest['DistanceTransform']
#            topGroup.copy('DistanceTransform', dest)        
#            self.mainOperator.innerOperators[0]._opDistanceTransform._fixed = False        
#            self.mainOperator.innerOperators[0]._opDistanceTransform._processedTimeSteps = range(topGroup['DistanceTransform'].shape[0])
#        
#        print "objectExtraction multi class: maximum image"
#        dest = self.mainOperator.innerOperators[0]._opRegionalMaximum._mem_h5                
#        if 'MaximumImage' in topGroup.keys():            
#            del dest['MaximumImage']
#            topGroup.copy('MaximumImage', dest)        
#            self.mainOperator.innerOperators[0]._opRegionalMaximum._fixed = False        
#            self.mainOperator.innerOperators[0]._opRegionalMaximum._processedTimeSteps = range(topGroup['MaximumImage'].shape[0])
        
#        print "objectExtraciontn multi class: region local centers"
#        if "RegionLocalCenters" in topGroup.keys():
#            cache = {}
#            for t in topGroup["RegionLocalCenters"].keys():
#                cache[int(t)] = []                
#                labels = topGroup["RegionLocalCenters"][t].keys()
#                labels = [int(x) for x in labels]
#                for label in labels:
#                    cache[int(t)][label] = topGroup["RegionLocalCenters"][t][label].value
#            self.mainOperator.innerOperators[0]._opRegionalMaximum._cache = cache
        
        self._dirty = False
        
        
    def isDirty(self):
        return True
#        return self._dirty
        
    def handleDirty(self, slot, roi):
        self._dirty = True
    
    def unload(self):
        print "ObjExtraction.unload not implemented" 

