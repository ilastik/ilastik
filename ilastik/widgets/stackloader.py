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
from lazyflow.operators.vigraOperators import *
from lazyflow.operators.ioOperators import OpStackLoader



from PyQt4 import QtCore, QtGui
from shutil import rmtree
from volumina.adaptors import Op5ifyer


#*******************************************************************************
# O p  C h a i n L o a d e r                                                   *
#*******************************************************************************

class OpChainLoader(Operator):
    name = "OpStackChainLoader"
    inputSlots = [InputSlot("globstring"),InputSlot("convert"),InputSlot("invert")]
    outputSlots = [OutputSlot("output")]
    
    def __init__(self, graph, register = True):
        Operator.__init__(self, graph, register)
        
        self.graph = graph
        self.loader = OpStackLoader(self.graph)
        self.op5ifyer = Op5ifyer(self.graph)
        self.outpiper = OpArrayPiper(self.graph)
        self.inverter = OpGrayscaleInverter(self.graph)
        self.converter = OpRgbToGrayscale(self.graph)


    def setupOutputs(self):
        
        self.loader.inputs["globstring"].setValue(self.inputs["globstring"].value)
        self.op5ifyer.inputs["input"].connect(self.loader.outputs["stack"])

        if not self.inputs["invert"].value and not self.inputs["convert"].value:
            self.outpiper.inputs["Input"].connect(self.op5ifyer.outputs["output"])
        elif not self.inputs["invert"].value and self.inputs["convert"].value:
            self.inverter.inputs["input"].connect(self.op5ifyer.outputs["output"])
            self.outpiper.inputs["Input"].connect(self.inverter.outputs["output"])
        elif self.inputs["invert"].value and not self.inputs["convert"].value:
            self.converter.inputs["input"].connect(self.op5ifyer.outputs["output"])
            self.outpiper.inputs["Input"].connect(self.converter.outputs["output"])
        elif self.inputs["invert"].value and self.inputs["convert"].value:
            self.converter.inputs["input"].connect(self.op5ifyer.outputs["output"])
            self.inverter.inputs["input"].connect(self.converter.outputs["outout"])
            self.outpiper.inputs["Input"].connect(self.inverter.outputs["output"])

        self.outputs["output"].meta.dtype = self.outpiper.outputs["Output"].meta.dtype
        self.outputs["output"].meta.shape = self.outpiper.outputs["Output"].meta.shape
        self.outputs["output"].meta.axistags = self.outpiper.outputs["Output"].meta.axistags
        
    def execute(self, slot, subindex, roi, result):
        
        result[:] = self.outpiper.outputs["Output"](roi).wait()
        return result
        
        
        
#*******************************************************************************
# S t a c k L o a d e r                                                        *
#*******************************************************************************

class StackLoader(QtGui.QDialog):
    def __init__(self, parent=None, graph = Graph()):
        
        
        #SETUP OpStackChainLoader
        self.graph = graph
        self.ChainLoader = OpChainLoader(self.graph) 
        #set default for inputslots, because only the setupOutputs method is
        #overridden, so all inputslots have to be set to setup the OperatorGroup
        #correctly
        self.ChainLoader.inputs["invert"].setValue(False)
        self.ChainLoader.inputs["convert"].setValue(False)
        
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
        #self.connect(self.loadButton, QtCore.SIGNAL('clicked()'), self.slotLoad)
        self.cancelButton = QtGui.QPushButton("&Cancel")
        self.connect(self.cancelButton, QtCore.SIGNAL('clicked()'), self.reject)
        tempLayout.addStretch()
        tempLayout.addWidget(self.cancelButton)
        tempLayout.addWidget(self.loadButton)
        self.layout.addStretch()
        self.layout.addLayout(tempLayout)
        self.show()
        self.image = None

    def pathChanged(self, text):
        self.ChainLoader.inputs["globstring"].setValue(str(text))
    
    def checkBoxesChanged(self,integer):
        if self.invertCheckBox.checkState() and not self.convertCheckBox.checkState() :
            self.ChainLoader.inputs["invert"].setValue(True)
            self.ChainLoader.inputs["convert"].setValue(False)
        elif not self.invertCheckBox.checkState() and self.convertCheckBox.checkState() :
            self.ChainLoader.inputs["invert"].setValue(False)
            self.ChainLoader.inputs["convert"].setValue(True)
        elif self.invertCheckBox.checkState() and self.convertCheckBox.checkState() :
            self.ChainLoader.inputs["invert"].setValue(True)
            self.ChainLoader.inputs["convert"].setValue(True)
        else:
            self.ChainLoader.inputs["invert"].setValue(False)
            self.ChainLoader.inputs["convert"].setValue(False)

    def slotDir(self):
        path = ""
        filename = QtGui.QFileDialog.getExistingDirectory(self, "Image Stack Directory", path)
        tempname = filename + '/*.png'
        #This is needed, because internally Qt always uses "/" separators,
        #which is a problem on Windows, as we don't use QDir to open dirs
        self.path.setText(str(QtCore.QDir.convertSeparators(tempname)))
        
    '''def slotLoad(self):    
        #result = self.ChainLoader.outputs["output"]().wait()
        pass'''
           
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
        self.g = Graph()

        self.createImages()
        
        
    def createImages(self):

        if not os.path.exists(self.testdir):
            print "creating directory '%s'" % (self.testdir)
            os.mkdir(self.testdir)
        self.block = numpy.random.rand(self.dim[0],self.dim[1],self.dim[2],self.dim[3])*255
        self.block = self.block.astype('uint8')
        op5ifyer = Op5ifyer(self.g)
        op5ifyer.inputs["Input"].setValue(self.block)
        for i in range(self.dim[2]):
            vigra.impex.writeImage(self.block[:,:,i,:],self.testdir+"%04d.png" % (i))
        self.block = op5ifyer.outputs["Output"]().wait()
    
        
    def stackAndTestFull(self,filetype = "png"):

        OpChain = OpStackChainLoader(self.g)
        OpChain.inputs["globstring"].setValue(self.testdir + '*.png')
        result = OpChain.outputs["output"][:].wait()
        assert(result == self.block).all()
    
    def stackAndTestConfig(self,filetype = "png"):
        
        g = Graph()
        OpChain = OpStackChainLoader(g)
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
        
        result = OpChain.outputs["output"]().wait()
        print 'outresult', result[:,:,:,:,0]
        
        
        #TEST THE RESULT
        #-----------------------------------------------------------------------
        
        #config(False,False) - No Inv, No Conv
        
        if self.config[0] == False and self.config[1] == False :
            print 'block', self.block[0,:,:,:,0]
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
        testclass = TestOperatorChain(configuration=(False,False),imagedimension=(2,2,2,3))
        testclass.stackAndTestConfig()
        testclass = TestOperatorChain(configuration=(True,True),imagedimension=(2,2,2,3))
        testclass.stackAndTestConfig()
        testclass = TestOperatorChain(configuration=(False,True),imagedimension=(2,2,2,3))
        testclass.stackAndTestConfig()
        testclass = TestOperatorChain(configuration=(True,False),imagedimension=(2,2,2,3))
        testclass.stackAndTestConfig()

    if '-gui' in sys.argv:
        app = QtGui.QApplication([""])
        dialog = StackLoader()
        app.exec_()





