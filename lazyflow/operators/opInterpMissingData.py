from lazyflow.graph import Operator, InputSlot, OutputSlot
import numpy as np

   
class OpInterpMissingData(Operator):

   name = "OpInterpMissingData"

   InputVolume = InputSlot()
   Output = OutputSlot()

   def __init__(self, *args, **kwargs):
      super(OpInterpMissingData, self).__init__(*args, **kwargs)

   def propagateDirty(self, slot, subindex, roi):
      self.Output.setDirty(roi)
 
   def setupOutputs(self):

      self.Output.meta.assignFrom( self.InputVolume.meta )
      self.Output.meta.dtype=np.uint8
      shape = list(self.InputVolume.meta.shape)
      self.Output.meta.shape = tuple(shape)
      pass

   def execute(self, slot, subindex, roi, result):
      data = self.InputVolume.get(roi).wait()
      data = self.InterpMissingLayer(data)
      result=data
      return result

   def InterpMissingLayer(self, data):
      fl=sum(sum(data))==0 #Full Layer Array



      #Interpolate First Block
      pos=-1
      if fl[0]==1:
         for i in range(fl.shape[0]):
            if fl[i]==0:
               pos=i
               break
      data[:,:,0:pos+1]=self.FirstBlock(data[:,:,0:pos+1])
 


      #Interpolate Center Leyers
      pos0=0
      pos1=0
      for i in range(fl.shape[0]-1):
         if fl[i]==0 and fl[i-1]==1:
            pos1=i
            if pos0!=0 and pos1!=0:
               data[:,:,pos0:pos1+1]=self.CenterBlock(data[:,:,pos0:pos1+1])
         if fl[i]==0 and fl[i+1]==1:
            pos0=i



      #Interpolate Last Block 
      if fl[fl.shape[0]-1]==1:
         for i in range(fl.shape[0]):
            i_rev=fl.shape[0]-i-1
            if fl[i_rev]==0:
               pos=i_rev
               break
      data[:,:,pos:data.shape[2]]=self.LastBlock(data[:,:,pos:data.shape[2]])



      return data
   
   def FirstBlock(self,data):
      for i in range(data.shape[2]-1):
         data[:,:,i]=data[:,:,data.shape[2]-1]
      return data
    
   def CenterBlock(self,sub_data):
      sub_data= np.transpose(sub_data)
      Total=sub_data.shape[0]-1
      L_0=np.array(sub_data[0,:,:], dtype=np.float32)
      L_1=np.array(sub_data[Total,:,:], dtype=np.float32) 
      for t in range(Total+1):
         Layer=(L_1*t+L_0*(Total-t))/Total  
         sub_data[t,:,:]=Layer
      return np.transpose(sub_data)

   def LastBlock(self,data):
      for i in range(data.shape[2]):
         data[:,:,i]=data[:,:,0]
      return data
