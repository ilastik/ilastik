#!/usr/bin/env python
# -*- coding: utf-8 -*-

#    Copyright 2010, 2011 C Sommer, C Straehle, U Koethe, FA Hamprecht. All rights reserved.
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

# TODO
# TODO
# TODO
# port the following revisions:
#    1f810747c21380eda916c2c5b7b5d1893f92663e
#    e65f5bad2cd9fdaefbe7ceaafa0cce0e071b56e4

if __name__ == "__main__":
    
    #make the program quit on Ctrl+C
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    import os, sys

    import numpy as np
    from PyQt4.QtCore import QObject, QRectF, QTime, Qt
    from PyQt4.QtGui import QColor, QApplication, QSplitter, QPushButton, \
                            QVBoxLayout, QWidget, QHBoxLayout, QMainWindow
    
    from lazyflow.graph import Graph, Operator, InputSlot, OutputSlot
    from volumeeditor.pixelpipeline.datasources import LazyflowSource, ConstantSource
    from volumeeditor.pixelpipeline._testing import OpDataProvider
    from volumeeditor._testing.from_lazyflow import OpDataProvider5D, OpDelay
    from volumeeditor.layer import GrayscaleLayer, RGBALayer, ColortableLayer
    from volumeeditor.layerwidget.layerwidget import LayerWidget
    from volumeeditor.layerstack import LayerStackModel
    from volumeeditor.volumeEditor import VolumeEditor
    from volumeeditor.volumeEditorWidget import VolumeEditorWidget
    from volumeeditor.pixelpipeline.datasources import ArraySource, LazyflowSinkSource

    from labelListView import LabelListView, Label
    from labelListModel import LabelListModel
    
    from PyQt4 import QtCore, QtGui

    app = QApplication(sys.argv)

    class Test(QMainWindow):
        def __init__(self, useGL, argv):
            QMainWindow.__init__(self)
            
            self.layerstack = LayerStackModel()
            
              
       
            fn = os.path.split(os.path.abspath(__file__))[0] +"/5d.npy"
            raw = np.load(fn)

            nucleisrc = ArraySource(raw[...,0:1]/20)
            membranesrc = ArraySource(raw[...,0:1]/20)
            
            layer1 = GrayscaleLayer( membranesrc )
            layer1.name = "Membranes"
            self.layerstack.append(layer1)
            
            layer2 = RGBALayer( red = nucleisrc )
            layer2.name = "Nuclei"
            layer2.opacity = 0.5
            
         
            
            self.layerstack.append(layer2)
            
            shape = raw.shape
            labelsrc = self.createLabelSource(shape)
            red   = QColor(255,0,0)
            green = QColor(0,255,0)
            black = QColor(0,0,0,0)
            
            self.labellayer = ColortableLayer(labelsrc, colorTable = [black.rgba(), red.rgba(), green.rgba()] )
            self.labellayer.name = "Labels"
            self.layerstack.append(self.labellayer)        
            
            
            
            self.editor = VolumeEditor(shape, self.layerstack, labelsink=labelsrc, useGL=useGL)  
            self.editor.setDrawingEnabled(True)
            
            self.MainSplitter = QSplitter()
            self.MainSplitter.setContentsMargins(0,0,0,0)
            
            
            widget = VolumeEditorWidget( self.editor )
            self.MainSplitter.addWidget(widget)
            
            
            self.editor.posModel.slicingPos = [5,10,2]
           
            
            
            #self.layerWidgetButton = QPushButton("Layers")
            #self.layerWidgetButton.setCheckable(True)
            
            
            #add label stuff
            self.labelList = LabelListView()
            
            model = LabelListModel([Label("Label 1", red), Label("Label 2", green)])
            self.labelList.setModel(model)
            self.labelList.clicked.connect(self.switchLabel)
            self.labelList.doubleClicked.connect(self.switchColor)
            
            
            
            #the layer stuff is now here
            #show rudimentary layer widget
            model = self.editor.layerStack
            ######################################################################
            
            self.fitToViewButton   = QPushButton("fitToView")
            self.startClassification   = QPushButton("Start")
            
            
            
            
            self.view = LayerWidget(model)

            
            lh = QHBoxLayout()
            lh.addWidget(self.view)
            
            up   = QPushButton('Up')
            down = QPushButton('Down')
            delete = QPushButton('Delete')
            add = QPushButton('Add artifical layer')
            lv  = QVBoxLayout()
            lh.addLayout(lv)
            
            lv.addWidget(up)
            lv.addWidget(down)
            lv.addWidget(delete)
            lv.addWidget(add)
            
            #w.setGeometry(100, 100, 800,600)
            
            up.clicked.connect(model.moveSelectedUp)
            model.canMoveSelectedUp.connect(up.setEnabled)
            down.clicked.connect(model.moveSelectedDown)
            model.canMoveSelectedDown.connect(down.setEnabled)
            delete.clicked.connect(model.deleteSelected)
            model.canDeleteSelected.connect(delete.setEnabled)

            
            
            
            #Left Part
            v = QVBoxLayout()
            v.addWidget(self.startClassification)
            v.addWidget(self.fitToViewButton)
            
            #v.addWidget(self.layerWidgetButton)
            v.addWidget(self.labelList)
            v.addLayout(lh)
            v.addStretch()
            
            
            
            
            h = QHBoxLayout()
            h.addWidget(self.MainSplitter)
            dummy=QWidget()
            dummy.setLayout(v)
            self.MainSplitter.addWidget(dummy)
            
            
            
            
            
            
            self.centralWidget = QWidget()
            self.centralWidget.setLayout(h)
            self.setCentralWidget(self.centralWidget)

            def fit():
                for i in range(3):
                    self.editor.imageViews[i].changeViewPort(QRectF(0,0,30,30))
            self.fitToViewButton.toggled.connect(fit)       

            


 
            
            def addConstantLayer():
                src = ConstantSource(128)
                layer = RGBALayer( green = src )
                layer.name = "Soylent Green"
                layer.opacity = 0.5
                model.append(layer)
            add.clicked.connect(addConstantLayer)
            ######################################################################
            
#            def layers(toggled):
#                if toggled:
#                    w.show()
#                    w.raise_()
#                else:
#                    w.hide()
#            self.layerWidgetButton.toggled.connect(layers)
    
        
        
        
        def switchLabel(self, modelIndex):
            self.editor.brushingModel.setDrawnNumber(modelIndex.row()+1)
            
        def switchColor(self, modelIndex):
            if modelIndex.column()>0:
                return
            #FIXME: we shouldn't pass the role like that, some object should know it
            newcolor = self.labelList.model().data(modelIndex, Qt.EditRole)
            self.labellayer.colorTable[modelIndex.row()+1]=newcolor.rgba()

        
        def createLabelSource(self, shape):
            from lazyflow import operators
            g = Graph()
            self.g=g
            opLabels = operators.OpSparseLabelArray(g)                                
            opLabels.inputs["shape"].setValue(shape[:-1] + (1,))
            opLabels.inputs["eraser"].setValue(100)                
            #opLabels.inputs["Input"][0,0,0,0,0] = 1                    
            #opLabels.inputs["Input"][0,0,0,1,0] = 2                    
            
            labelsrc = LazyflowSinkSource(opLabels, opLabels.outputs["Output"], opLabels.inputs["Input"])
            return labelsrc
        
        def startClassification():
          self.g
        
    t = Test(False, [])
    t.show()

    app.exec_()

