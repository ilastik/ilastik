import vigra
import h5py
import lazyflow

from lazyflow.operators.ioOperators import OpInputDataReader
from lazyflow.operators import OpMultiArraySlicer2
from lazyflow.graph import Graph

from volumina.pixelpipeline.datasources import LazyflowSource, NormalizingSource
from volumina.layer import GrayscaleLayer, ColortableLayer, ClickableColortableLayer, AlphaModulatedLayer, RGBALayer

from volumina.api import Viewer

from PyQt4.QtGui import QApplication, QColor, QKeySequence, QShortcut
from PyQt4.QtCore import QRectF, Qt

def createDefault16ColorColorTable():
    colors = []

    # Transparent for the zero label
    colors.append(QColor(0,0,0,0))

    # ilastik v0.5 colors
    colors.append( QColor( Qt.red ) )
    colors.append( QColor( Qt.green ) )
    colors.append( QColor( Qt.yellow ) )
    colors.append( QColor( Qt.blue ) )
    colors.append( QColor( Qt.magenta ) )
    colors.append( QColor( Qt.darkYellow ) )
    colors.append( QColor( Qt.lightGray ) )

    # Additional colors
    colors.append( QColor(255, 105, 180) ) #hot pink
    colors.append( QColor(102, 205, 170) ) #dark aquamarine
    colors.append( QColor(165,  42,  42) ) #brown
    colors.append( QColor(0, 0, 128) )     #navy
    colors.append( QColor(255, 165, 0) )   #orange
    colors.append( QColor(173, 255,  47) ) #green-yellow
    colors.append( QColor(128,0, 128) )    #purple
    colors.append( QColor(240, 230, 140) ) #khaki

#        colors.append( QColor(192, 192, 192) ) #silver
#        colors.append( QColor(69, 69, 69) )    # dark grey
#        colors.append( QColor( Qt.cyan ) )

    assert len(colors) == 16

    return colors
    #return [c.rgba() for c in colors]

    
def slicePredictions(graph, opReaderPred, name, layerstack):
    opPredictionSlicer = OpMultiArraySlicer2(graph=graph )
    opPredictionSlicer.Input.connect( opReaderPred.Output )
    opPredictionSlicer.AxisFlag.setValue('c')
    pred_slots = opPredictionSlicer.Slices
    
    ct = createDefault16ColorColorTable()
    layers = []
    for channel, predictionSlot in enumerate(pred_slots):
        predictsrc = LazyflowSource(predictionSlot)
        predictLayer = AlphaModulatedLayer( predictsrc,tintColor=ct[channel],range=(0.0, 1.0),normalize=(0.0, 1.0) )
        predictLayer.opacity = 0.25
        predictLayer.name = "Pred"+ name+ str(channel)
        predictLayer.visible = False
        layers.append(predictLayer)
        layerstack.append(predictLayer)
        
    #return layers
        
def showStuff():

    graph = Graph()
    rawfile = "/home/akreshuk/data/dbock/substack_05_41_aligned_elastic.h5/volume/data"
    predictions = "/home/akreshuk/data/dbock/substack_05_41_rec_pred.h5/volume/data"
    predictions2 = "/home/akreshuk/data/dbock/substack_05_41_rec_pred2.h5/volume/data"
    predictions3 = "/home/akreshuk/ilastik/substack_05_41_aligned_elastic_res_from_Training_2.h5/volume/data"
    predictions4 = "/home/akreshuk/ilastik/substack_05_41_aligned_elastic_res_from_Training_2_noint.h5/volume/data"

    opReaderRaw = OpInputDataReader(graph=graph)
    opReaderRaw.FilePath.setValue(rawfile)

    opReaderPred = OpInputDataReader(graph=graph)
    opReaderPred.FilePath.setValue(predictions)
    
    opReaderPred2 = OpInputDataReader(graph=graph)
    opReaderPred2.FilePath.setValue(predictions2)
    
    opReaderPred3 = OpInputDataReader(graph=graph)
    opReaderPred3.FilePath.setValue(predictions3)
    
    opReaderPred4 = OpInputDataReader(graph=graph)
    opReaderPred4.FilePath.setValue(predictions4)

    app = QApplication([])
    v = Viewer()
    direct = False

    rawdata = LazyflowSource(opReaderRaw.outputs["Output"])
    sh = (1,)+opReaderRaw.Output.meta.shape
    v.dataShape = sh

    lraw = GrayscaleLayer(rawdata, direct=direct)
    lraw.visible=True
    lraw.name = "raw"
    v.layerstack.append(lraw)
    
    #layers = slicePredictions(graph, opReaderPred, "", v.layerstack)
    #layers = slicePredictions(graph, opReaderPred2, "ml", v.layerstack)
    layers = slicePredictions(graph, opReaderPred3, "ml_inter", v.layerstack)
    layers = slicePredictions(graph, opReaderPred4, "ml", v.layerstack)
        
    v.show()
    app.exec_()
    
if __name__=="__main__":
    showStuff()