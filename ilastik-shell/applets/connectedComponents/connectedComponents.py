#make the program quit on Ctrl+C
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

import os, sys, numpy, copy

from PyQt4.QtCore import pyqtSignal, QTimer, QRectF, Qt
from PyQt4.QtGui import QColor, QMainWindow, QApplication, QFileDialog, \
                        QMessageBox, qApp, QItemSelectionModel, QIcon, QTransform
from PyQt4 import uic

from lazyflow.graph import Graph
from lazyflow.operators import Op5ToMulti, OpArrayCache, OpBlockedArrayCache, \
                               OpArrayPiper, OpPredictRandomForest, \
                               OpSingleChannelSelector, OpSparseLabelArray, \
                               OpMultiArrayStacker, OpTrainRandomForest, OpPixelFeatures, \
                               OpMultiArraySlicer2,OpH5Reader, OpBlockedSparseLabelArray, \
                               OpMultiArrayStacker, OpTrainRandomForestBlocked, OpPixelFeatures, \
                               OpH5ReaderBigDataset, OpSlicedBlockedArrayCache, OpPixelFeaturesPresmoothed
                               
from connected_comp import OpThreshold, OpConnectedComponents

from volumina.api import LazyflowSource, GrayscaleLayer, RGBALayer, ColortableLayer, \
    AlphaModulatedLayer, LayerStackModel, VolumeEditor, LazyflowSinkSource

from volumina import colortables

from labelListView import Label
from labelListModel import LabelListModel

from featureTableWidget import FeatureEntry
from featureDlg import FeatureDlg

import vigra


class ConnectedComponentsPipeline( object ):
    def __init__( self, graph ):
        ##
        # thresholding
        ##
        self.opThreshold = OpThreshold(graph)
        ##
        # entry point:
        #self.opThreshold.inputs["Input"].connect(self.pCache.outputs["Output"])
        #channel, value = ThresholdDlg(self.labelListModel._labels)
        channel = 0
        value = 0.5
        #ref_label = self.labelListModel._labels[channel]
        self.opThreshold.inputs["Channel"].setValue(channel)
        self.opThreshold.inputs["Threshold"].setValue(value)
        # threshsrc = LazyflowSource(self.opThreshold.outputs["Output"][0])
        
        #threshsrc.setObjectName("Threshold for %s" % ref_label.name)
        #transparent = QColor(0,0,0,0)
        #white = QColor(255,255,255)
        #colorTable = [transparent.rgba(), white.rgba()]
        #threshLayer = ColortableLayer(threshsrc, colorTable = colorTable )
        #threshLayer.name = "Threshold for %s" % ref_label.name
        #self.layerstack.insert(1, threshLayer)
        #self.CCButton.setEnabled(True)

        ##
        # connected components
        ##
        self.opCC = OpConnectedComponents(graph)
        self.opCC.inputs["Input"].connect(self.opThreshold.outputs["Output"])
        #we shouldn't have to define these. But just in case...
        self.opCC.inputs["Neighborhood"].setValue(6)
        self.opCC.inputs["Background"].setValue(0)
        
        # ccsrc = LazyflowSource(self.opCC.outputs["Output"][0])
        # ccsrc.setObjectName("Connected Components")
        # ctb = colortables.create_default_16bit()
        # ctb.insert(0, QColor(0, 0, 0, 0).rgba()) # make background transparent
        # ccLayer = ColortableLayer(ccsrc, ctb)
        # ccLayer.name = "Connected Components"
        # self.layerstack.insert(1, ccLayer)
        
if __name__ == "__main__":
    g = Graph()
    pipeline = ConnectedComponentsPipeline( g )
