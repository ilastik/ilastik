###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
#		   http://ilastik.org/license.html
###############################################################################
from ilastik.applets.base.standardApplet import StandardApplet

from preprocessingSerializer import PreprocessingSerializer
from opPreprocessing import OpPreprocessing

class PreprocessingApplet(StandardApplet):

    def __init__(self, workflow, title, projectFileGroupName, supportIlastik05Import=False):
        super(PreprocessingApplet, self).__init__( title, workflow)

        self._workflow = workflow
        
        self._serializableItems = [ PreprocessingSerializer(self.topLevelOperator, projectFileGroupName) ]
        
        self._gui = None
        self._title = title
        
        self.writeprotected = False
        self._enabledWriteprotect = True
        self._enabledDS = True
        self._enabledReset = False
        
    def enableWriteprotect(self,value):
        if self._enabledWriteprotect!=value:
            self._enabledWriteprotect = value
            self._gui.enableWriteprotect(value)
    
    def enableReset(self,er):
        if self._workflow._headless:
            return
        from preprocessingGui import PreprocessingGui
        if self._enabledReset != er:
            self._enabledReset = er
            #if GUI is not set up, _gui is an Adapter
            if type(self._gui)==PreprocessingGui:
                self._gui.enableReset(er)
    
    def enableDownstream(self,ed):
        if self._workflow._headless:
            return
        from preprocessingGui import PreprocessingGui
        if ed and not self._enabledDS: # enable Downstream 
            self._enabledDS = True
        if not ed and self._enabledDS: # disable Downstream
            self._enabledDS = False
        if isinstance(self._gui,PreprocessingGui): # if the gui is already set up, apply enabling to write-protect checkbox
            self._gui.enableWriteprotect(ed)
    
    def createSingleLaneGui( self , laneIndex):
        from preprocessingGui import PreprocessingGui
        opPre = self.topLevelOperator.getLane(laneIndex)
        self._gui = PreprocessingGui( self, opPre )
        
        if self.writeprotected:
            self._gui.setWriteprotect()
        
        self.enableDownstream(self._enabledDS)
        self._gui.enableReset(self._enabledReset)
        
        return self._gui
    
    @property
    def dataSerializers(self):
        return self._serializableItems
    
    @property
    def singleLaneOperatorClass(self):
        return OpPreprocessing
    
    @property
    def broadcastingSlots(self):
        return ["Sigma", "Filter"]
    
