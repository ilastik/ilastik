from ilastik.applets.dataSelection.dataSelectionApplet import DataSelectionApplet
from ilastik.applets.dataSelection.dataSelectionGui import DataSelectionGui ,GuiMode
from ilastik.applets.dataSelection.opDataSelection import OpMultiLaneDataSelection
from ilastik.applets.dataSelection.dataSelectionSerializer import DataSelectionSerializer, Ilastik05DataSelectionDeserializer
from ilastik.applets.base.standardApplet import StandardApplet
from ilastik.applets.base.applet import ControlCommand

from opCarvingTopLevel import OpCarvingTopLevel
from carvingSerializer import CarvingSerializer
from carvingGui import CarvingGui
from preprocessingSerializer import PreprocessingSerializer
from opPreprocessingTopLevel import OpPreprocessingTopLevel
from preprocessingGui import PreprocessingGui
from opPreprocessing import OpPreprocessing
import functools

#just for Thorben, who wants to add already preprocessed files
from cylemon.segmentation import MSTSegmentor

class PreprocessingApplet(StandardApplet):

    def __init__(self, workflow, title, projectFileGroupName, supportIlastik05Import=False):
        super(PreprocessingApplet, self).__init__( title, workflow)
        
        self._serializableItems = [ PreprocessingSerializer(self.topLevelOperator, "preprocessing") ]
        if supportIlastik05Import:
            self._serializableItems.append(Ilastik05DataSelectionDeserializer(self.topLevelOperator))
        
        self._gui = None
        self._title = title
        
        self.writeprotected = False
        self._enabledDS = True
        self._enabledReset = False
        
        #temp Var: Thorben wants to add already preprocessed Files
        self.ThorbenGraph = None
    
    def enableReset(self,er):
        if self._enabledReset != er:
            self._enabledReset = er
            #if GUI is not set up, _gui is an Adapter
            if type(self._gui)==PreprocessingGui:
                self._gui.enableReset(er)
    
    def enableDownstream(self,ed):
        if ed and not self._enabledDS: # enable Downstream 
            self._enabledDS = True
            self.guiControlSignal.emit(ControlCommand.Pop)
            
        elif not ed and self._enabledDS: # disable Downstream
            self._enabledDS = False
            self.guiControlSignal.emit(ControlCommand.DisableDownstream)
    
    def createSingleLaneGui( self , laneIndex):
        opPre = self.topLevelOperator.getLane(laneIndex)
        self._gui = PreprocessingGui( opPre )
        
        if self.writeprotected:
            self._gui.setWriteprotect()
        if not self._enabledDS:
            self.guiControlSignal.emit(ControlCommand.DisableDownstream)
        self._gui.enableReset(self._enabledReset)
        
        return self._gui
    
    #  temp - temp - temp - temp - temp - temp - temp - temp - temp
    def ThorbenWantsToAddAlreadyPreprocessedFilesDirectly(self,thorbensfile):
        print '''
            *~*~*~*~*~*~*~*~*~*~*~*~*~
            ~Do not try this at home!*
            *  this is just a hack   ~
            ~                        *
            * To use the preprocessed~
            ~  File, just hit "run"  *
            *~*~*~*~*~*~*~*~*~*~*~*~*~'''
        graph = MSTSegmentor.loadH5(thorbensfile,"graph")
        self.ThorbenGraph = graph
    #  /temp - temp - temp - temp - temp - temp - temp - temp - temp
    
    @property
    def dataSerializers(self):
        return self._serializableItems
    
    @property
    def singleLaneOperatorClass(self):
        return OpPreprocessing
    
    @property
    def broadcastingSlots(self):
        return ["Sigma","RawData"]
    
