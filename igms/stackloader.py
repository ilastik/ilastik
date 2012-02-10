#!/usr/bin/env python
# -*- coding: utf-8 -*-

#    Copyright 2010 C Sommer, C Straehle, U Koethe, FA Hamprecht. All rights reserved.
#    
#    Redistribution and use in source and binary forms, with or without modification, are
#    permitted provided that the following conditions are met:
#    
#       1. Redistributions of source code must retain the above copyright notice, this list of
#          conditions and the following disclaimer.
#    
#       2. Redistributions in binary form must reproduce the above copyright notice, this list
#          of conditions and the following disclaimer in the documentation and/or other materials
#          provided with the distribution.
#    
#    THIS SOFTWARE IS PROVIDED BY THE ABOVE COPYRIGHT HOLDERS ``AS IS'' AND ANY EXPRESS OR IMPLIED
#    WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
#    FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE ABOVE COPYRIGHT HOLDERS OR
#    CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#    CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
#    SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
#    ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#    NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
#    ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#    
#    The views and conclusions contained in the software and documentation are those of the
#    authors and should not be interpreted as representing official policies, either expressed
#    or implied, of their employers.

import glob
import os
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.operators.obsolete.vigraOperators import *



from PyQt4 import QtCore, QtGui
from shutil import rmtree


#*******************************************************************************
# O p S t a c k C h a i n B u i l d e r                                                        *
#*******************************************************************************


class OpStackChainBuilder(Operator):
    name = "OpStackChainBuilder"
    inputSlots = [InputSlot("globstring"),InputSlot("convert"),InputSlot("invert")]
    outputSlots = [OutputSlot("output")]
    
    def __init__(self, graph, register = True):
        Operator.__init__(self, graph, register)
        
        self.Loader = OpStackLoader(self.graph)
        self.Inverter = OpGrayscaleInverter(self.graph)
        self.OutPiper = OpArrayPiper(self.graph)
        self.GrayConverter = OpRgbToGraysacle(self.graph)
    
    def setupOutputs(self):
        assert self.inputs["globstring"].shape is not None
        self.Loader.inputs["globstring"].connect(self.inputs["globstring"])
        if self.inputs["invert"].value and not self.inputs["convert"].value:
            self.Inverter.inputs["input"].connect(self.Loader.outputs["stack"])
            self.OutPiper.inputs["Input"].connect(self.Inverter.outputs["output"])
        
        elif self.inputs["convert"].value and not self.inputs["invert"].value:
            self.GrayConverter.inputs["input"].connect(self.Loader.outputs["stack"])
            self.OutPiper.inputs["Input"].connect(self.GrayConverter.outputs["output"])
            
            self.outputs["output"]._dtype = self.GrayConverter.outputs["output"]._dtype
            self.outputs["output"]._axistags = self.GrayConverter.outputs["output"]._axistags
            self.outputs["output"]._shape = self.GrayConverter.outputs["output"]._shape
            
        elif self.inputs["convert"].value and self.inputs["invert"].value:

            self.Inverter.inputs["input"].connect(self.Loader.outputs["stack"])
            self.GrayConverter.inputs["input"].connect(self.Inverter.outputs["output"])
            self.OutPiper.inputs["Input"].connect(self.GrayConverter.outputs["output"])
            
            self.outputs["output"]._dtype = self.GrayConverter.outputs["output"]._dtype
            self.outputs["output"]._axistags = self.GrayConverter.outputs["output"]._axistags
            self.outputs["output"]._shape = self.GrayConverter.outputs["output"]._shape

        elif not self.inputs["convert"].value and not self.inputs["invert"].value:
            
            self.OutPiper.inputs["Input"].connect(self.Loader.outputs["stack"])
            self.outputs["output"]._dtype = self.Loader.outputs["stack"]._dtype
            self.outputs["output"]._axistags = self.Loader.outputs["stack"]._axistags
            self.outputs["output"]._shape = self.Loader.outputs["stack"]._shape
            
    def getOutSlot(self, slot, key, result):
        
        if slot.name == "output":
            req = self.OutPiper.outputs["Output"][key].allocate()
        return req.wait()
        

#*******************************************************************************
# S t a c k L o a d e r                                                        *
#*******************************************************************************

class StackLoader(QtGui.QDialog):
    def __init__(self, parent=None, graph = Graph()):
        
        
        #SETUP OpStackChainBuilder
        self.graph = graph
        self.ChainBuilder = OpStackChainBuilder(self.graph) 
        #set default for inputslots, because only the notifyConnectAll method is
        #overridden, so all inputslots have to be set to setup the OperatorGroup
        #correctly
        self.ChainBuilder.inputs["invert"].setValue(False)
        self.ChainBuilder.inputs["convert"].setValue(False)
        
        #SETUP LAYOUT
        #***********************************************************************
        QtGui.QWidget.__init__(self, parent)
        self.setWindowTitle("Load File Stack")
        self.setMinimumWidth(400)
        self.layout = QtGui.QVBoxLayout()
        self.setLayout(self.layout)
        
        #a list of filenames
        #internally, it's a list of lists of filenames
        #for each channel
        
        tempLayout = QtGui.QHBoxLayout()
        self.path = QtGui.QLineEdit("")
        self.connect(self.path, QtCore.SIGNAL("textChanged(QString)"), self.pathChanged)
        self.pathButton = QtGui.QPushButton("&Select")
        self.connect(self.pathButton, QtCore.SIGNAL('clicked()'), self.slotDir)
        tempLayout.addWidget(self.path)
        tempLayout.addWidget(self.pathButton)
        self.layout.addWidget(QtGui.QLabel("Path to Image Stack:"))
        self.layout.addLayout(tempLayout)

        #SETUP CheckBoxes
        
        tempLayout = QtGui.QVBoxLayout()
        self.invertCheckBox = QtGui.QCheckBox("Invert Colors")
        self.connect(self.invertCheckBox, QtCore.SIGNAL('stateChanged(int)'),self.checkBoxesChanged)
        self.convertCheckBox = QtGui.QCheckBox("Convert To GrayScale")
        self.connect(self.convertCheckBox, QtCore.SIGNAL('stateChanged(int)'),self.checkBoxesChanged)
        tempLayout.addWidget(self.invertCheckBox)
        tempLayout.addWidget(self.convertCheckBox)
        self.layout.addLayout(tempLayout)

        tempLayout = QtGui.QHBoxLayout()
        self.loadButton = QtGui.QPushButton("&Load")
        self.connect(self.loadButton, QtCore.SIGNAL('clicked()'), self.slotLoad)
        self.cancelButton = QtGui.QPushButton("&Cancel")
        self.connect(self.cancelButton, QtCore.SIGNAL('clicked()'), self.reject)
        self.previewFilesButton = QtGui.QPushButton("&Preview files")
        self.connect(self.previewFilesButton, QtCore.SIGNAL('clicked()'), self.slotPreviewFiles)
        tempLayout.addWidget(self.previewFilesButton)
        tempLayout.addStretch()
        tempLayout.addWidget(self.cancelButton)
        tempLayout.addWidget(self.loadButton)
        self.layout.addStretch()
        self.layout.addLayout(tempLayout)
        self.show()
        self.image = None

    def pathChanged(self, text):
        self.ChainBuilder.inputs["globstring"].setValue(str(text))
    
    def checkBoxesChanged(self,integer):
        if self.invertCheckBox.checkState() and not self.convertCheckBox.checkState() :
            self.ChainBuilder.inputs["invert"].setValue(True)
            self.ChainBuilder.inputs["convert"].setValue(False)
        elif not self.invertCheckBox.checkState() and self.convertCheckBox.checkState() :
            self.ChainBuilder.inputs["invert"].setValue(False)
            self.ChainBuilder.inputs["convert"].setValue(True)
        elif self.invertCheckBox.checkState() and self.convertCheckBox.checkState() :
            self.ChainBuilder.inputs["invert"].setValue(True)
            self.ChainBuilder.inputs["convert"].setValue(True)
        else:
            self.ChainBuilder.inputs["invert"].setValue(False)
            self.ChainBuilder.inputs["convert"].setValue(False)

    def slotDir(self):
        path = ""
        filename = QtGui.QFileDialog.getExistingDirectory(self, "Image Stack Directory", path)
        tempname = filename + '/*.png'
        #This is needed, because internally Qt always uses "/" separators,
        #which is a problem on Windows, as we don't use QDir to open dirs
        self.path.setText(str(QtCore.QDir.convertSeparators(tempname)))
        

    def slotPreviewFiles(self):
        self.fileTableWidget = loadOptionsWidget.previewTable(self.fileList)
        self.fileTableWidget.exec_()

    def slotLoad(self):    
        result = self.ChainBuilder.outputs["output"][:].allocate().wait()
        print result.shape
            
    def exec_(self):
        if QtGui.QDialog.exec_(self) == QtGui.QDialog.Accepted:
            return  str(self.path.text()), self.fileList, self.options
        else:
            return None, None, None

class TestOperatorChain():
    
    def __init__(self,testdirectory='./testImages/',imagedimension = (200,200,50,3),configuration = (False,False)):
        
        self.testdir = testdirectory
        self.dim = imagedimension
        self.config = configuration
        self.result = None
        self.block = None
        

        self.createImages()
        
        
    def createImages(self):

        if not os.path.exists(self.testdir):
            print "creating directory '%s'" % (self.testdir)
            os.mkdir(self.testdir)
        self.block = numpy.random.rand(self.dim[0],self.dim[1],self.dim[2],self.dim[3])*255
        self.block = self.block.astype('uint8')
        for i in range(self.dim[2]):
            vigra.impex.writeImage(self.block[:,:,i,:],self.testdir+"%04d.png" % (i))
    
        
    def stackAndTestFull(self,filetype = "png"):

        g = Graph()
        OpChain = OpStackChainBuilder(g)
        OpChain.inputs["globstring"].setValue(self.testdir + '*.png')
        result = OpChain.outputs["output"][:].allocate().wait()
        assert(result == self.block).all()
    
    def stackAndTestConfig(self,filetype = "png"):
        
        g = Graph()
        OpChain = OpStackChainBuilder(g)
        OpChain.inputs["globstring"].setValue(self.testdir + '*.png')
        
        #CONFIGURE THE OPERATORCHAIN
        #-----------------------------------------------------------------------
        #config(False,False) - No Inv, No Conv
        if self.config[0] == False and self.config[1] == False:
            OpChain.inputs["invert"].setValue(False)
            OpChain.inputs["convert"].setValue(False)
        
        #config(True,False) - Inv, No Conv
        if self.config[0] == True and self.config[1] == False:
            OpChain.inputs["invert"].setValue(True)
            OpChain.inputs["convert"].setValue(False)
            
        #config(True,False) - No Inv, Conv
        if self.config[0] == False and self.config[1] == True:
            OpChain.inputs["invert"].setValue(False)
            OpChain.inputs["convert"].setValue(True)
            
        #config(True,True) - Inv, Conv
        if self.config[0] == True and self.config[1] == True:
            OpChain.inputs["convert"].setValue(True)
            OpChain.inputs["invert"].setValue(True)

        #OBTAIN THE RESULT
        #-----------------------------------------------------------------------

        result = OpChain.outputs["output"][:].allocate().wait()
        
        
        #TEST THE RESULT
        #-----------------------------------------------------------------------
        
        #config(False,False) - No Inv, No Conv
        
        if self.config[0] == False and self.config[1] == False :
            assert(result == self.block).all()
        
        #config(True,False) - Inv, No Conv
        if self.config[0] == True and self.config[1] == False:
            for i in range(result.shape[-1]):
                assert(result[:,:,:,i] == 255-self.block[:,:,:,i]).all()
        
        #config(False,True) - No Inv, Conv
        if self.config[0] == False  and self.config[1] == True:
            for i in range(result.shape[-1]):
                assert(result[:,:,:,i] == (numpy.round(0.299*self.block[:,:,:,0] + 0.587*self.block[:,:,:,1] + 0.114*self.block[:,:,:,2])).astype(int)).all()
                
        #config(True,True) - Inv, Conv
        if self.config[0] == True  and self.config[1] == True:
            for i in range(self.block.shape[-1]):
                self.block[:,:,:,i] = 255-self.block[:,:,:,i]
            for i in range(result.shape[-1]):
                assert(result[:,:,:,i] == (numpy.round(0.299*self.block[:,:,:,0] + 0.587*self.block[:,:,:,1] + 0.114*self.block[:,:,:,2])).astype(int)).all()
        
        
        
        
    def cleanUp(self):
        os.rmdir(self.testdirectory) 
   
#*******************************************************************************
# i f   _ _ n a m e _ _   = =   " _ _ m a i n _ _ "                            *
#*******************************************************************************
if __name__ == "__main__":
   
    if not '-gui' in sys.argv and not '-test' in sys.argv:
        raise RuntimeError("usage: pass either option -gui or option -test")
    
    # configuration=(intert?[True/False],converttoGrayscale?[True/False])
    if '-test' in sys.argv:
        testclass = TestOperatorChain(configuration=(False,False))
        testclass.stackAndTestConfig()
        testclass = TestOperatorChain(configuration=(True,True))
        testclass.stackAndTestConfig()
        testclass = TestOperatorChain(configuration=(False,True))
        testclass.stackAndTestConfig()
        testclass = TestOperatorChain(configuration=(True,False))
        testclass.stackAndTestConfig()
        
    if '-gui' in sys.argv:
        app = QtGui.QApplication([""])
        dialog = StackLoader()
        app.exec_()





