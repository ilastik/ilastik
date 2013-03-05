from lazyflow.graph import Operator, InputSlot, OutputSlot
import numpy as np
import vigra

class OpInterpMissingData(Operator):
    name = "OpInterpMissingData"

    InputVolume = InputSlot()
    InputSearchDepth = InputSlot()
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
        depth= self.InputSearchDepth.value

        data = data.view( vigra.VigraArray )
        data.axistags = self.InputVolume.meta.axistags
        self._interpMissingLayer(data.withAxes(*'xyz'))

        z_index = self.InputVolume.meta.axistags.index('z')
        n_layers = self.InputVolume.meta.getTaggedShape()['z']


        old_start = roi.start
        old_stop = roi.stop


        #   while rio top layer is empty, 
        #   push layer from data to top of rio
        offset0=0
        while(np.sum(data[:,:,0])==0):

            #searched depth reached
            if offset0==depth:
                break

            #top layer reached
            if old_start[z_index]-offset0==0:
                break

            offset0+=1
            new_key = (slice(old_start[0], old_stop[0], None), slice(old_start[1], old_stop[1]), \
                    slice(old_start[2]-offset0, old_stop[2]))
            data = self.InputVolume[new_key].wait()



        #   while rio bottem layer is empty, 
        #   push layer from data to bottem of rio 
        offset1=0
        while(np.sum(data[:,:,-1])==0):


            #searched depth reached
            if offset1==depth:
                break

            #bottem layer reached
            if old_stop[z_index]+offset1==n_layers:
                break

            offset1+=1
            new_key = (slice(old_start[0], old_stop[0], None), slice(old_start[1], old_stop[1]), \
                    slice(old_start[2]-offset0, old_stop[2]+offset1))
            data = self.InputVolume[new_key].wait()



        #   apply Interpolation
        self._interpMissingLayer(data)


        #   cut data to origin shape or rio
        if offset0!=0:
            data=data[:,:,offset0:]
        if offset1!=0:
            data=data[:,:,0:-offset1]


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


        #Interpolate Center Layers
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
        Description: interpolates all layers between the first and the last slices

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
        Description: set the values of the last few empty layers to these of the last correct one

                     [last correct layer]
                            |
                     e.g. 467000 --> 467777

        :param data: Must be 3d, in xyz order.
        """
        for i in range(data.shape[2]):
            data[:,:,i]=data[:,:,0]
        return data
