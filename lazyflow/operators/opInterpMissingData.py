from lazyflow.graph import Operator, InputSlot, OutputSlot
import numpy as np
import vigra
    
class OpInterpMissingData(Operator):
    name = "OpInterpMissingData"

    InputVolume = InputSlot()
    Output = OutputSlot()

    def setupOutputs(self):
        # Output has the same shape/axes/dtype/drange as input
        self.Output.meta.assignFrom( self.InputVolume.meta )
        
        # Check for errors
        taggedShape = self.InputVolume.meta.getTaggedShape()
        if 't' in taggedShape:
            assert taggedShape['t'] == 1, "Non-spatial dimensions must be of length 1"
        if 'c' in taggedShape:
            assert taggedShape['c'] == 1, "Non-spatial dimensions must be of length 1"

    def execute(self, slot, subindex, roi, result):
        data = self.InputVolume.get(roi).wait()
        data = data.view( vigra.VigraArray )
        data.axistags = self.InputVolume.meta.axistags
        
        self._interpMissingLayer(data.withAxes(*'xyz'))
        result[:] = data
        return result

    def propagateDirty(self, slot, subindex, roi):
        # TODO: This implementation of propagateDirty() isn't correct.
        #       That's okay for now, since this operator will never be used with input data that becomes dirty.
        self.Output.setDirty(roi)
 
    def _interpMissingLayer(self, data):
        """
        Description: Interpolates empty layers and stacks of layers in which all values are zero.
        
        :param data: Must be 3d, in xyz order.
        """
        fl=data.sum(0).sum(0)==0 #False Layer Array

        #Interpolate First Block
        if fl[0]==1:
            for i in range(fl.shape[0]):
                if fl[i]==0:
                    data[:,:,0:i+1]=self._firstBlock(data[:,:,0:i+1])
                    break

        
        #Interpolate Center Leyers
        pos0=0
        pos1=0
        for i in range(1,fl.shape[0]-1):
           if fl[i]==1:
              if fl[i-1]==0:
                pos0=i-1
              if fl[i+1]==0:
                pos1=i+1
              if pos1!=0:
                data[:,:,pos0:pos1+1]=self._centerBlock(data[:,:,pos0:pos1+1])
                pos1=0


        #Interpolate Last Block 
        if fl[fl.shape[0]-1]==1:
            for i in range(fl.shape[0]):
                i_rev=fl.shape[0]-i-1
                if fl[i_rev]==0:
                    data[:,:,i_rev:data.shape[2]]=self._lastBlock(data[:,:,i_rev:data.shape[2]])
                    break
    
    def _firstBlock(self,data):
        """
        Description: set the values of the first few empty layers to these of the first correct one

                     [first correct layer]
                            |
                     e.g 000764 --> 777764

        :param data: Must be 3d, in xyz order.
        """
        for i in range(data.shape[2]-1):
            data[:,:,i]=data[:,:,data.shape[2]-1]
        return data
     
    def _centerBlock(self,sub_data):
        """
        Description: interpolates all layers between the first and the last slice od the data

                     e.g 80004 --> 87654

        :param sub_data: Must be 3d, in xyz order.
        """
        sub_data = sub_data.transpose()
        Total=sub_data.shape[0]-1
        L_0=np.array(sub_data[0,:,:], dtype=np.float32)
        L_1=np.array(sub_data[Total,:,:], dtype=np.float32) 
        for t in range(Total+1):
            Layer=(L_1*t+L_0*(Total-t))/Total  
            sub_data[t,:,:]=Layer
        return sub_data.transpose()

    def _lastBlock(self,data):
        """
        Description: set the value of the last few empty layers to these of the last correct one

                     [last correct layer]
                            |
                     e.g. 467000 --> 467777

        :param data: Must be 3d, in xyz order.
        """
        for i in range(data.shape[2]):
            data[:,:,i]=data[:,:,0]
        return data
