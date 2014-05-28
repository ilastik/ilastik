import os

from PyQt4.QtCore import Qt, QTimer
from PyQt4.QtGui import QColor

from volumina.api import ColortableLayer, LazyflowSource
from ilastik.applets.labeling.labelingGui import LabelingGui

try:
    from volumina.view3d.volumeRendering import RenderingManager
    #from volumina.view3d.view3d import convertVTPtoOBJ
    #from vtk import vtkXMLPolyDataWriter, vtkPolyDataWriter
    _have_vtk = True
except ImportError:
    _have_vtk = False

class SeededWatershedGui(LabelingGui):
    
    def __init__(self, *args, **kwargs):
        kwargs['drawerUiPath'] = os.path.split(__file__)[0] + '/drawer.ui'
        super( SeededWatershedGui, self ).__init__(*args, **kwargs)
        
        def _onComputeWatershed():
            self.topLevelOperatorView.FreezeCache.setValue(False)
            QTimer.singleShot(1000, lambda: self.topLevelOperatorView.FreezeCache.setValue( True ) )
            QTimer.singleShot(1000, lambda: self._update_rendering() )            
        
        self._labelControlUi.computeWatershedButton.clicked.connect( _onComputeWatershed )
        
        def _handleLabelClassChange( topLeft, bottomRight ):
            self.updateAllLayers()
        self._labelControlUi.labelListModel.dataChanged.connect( _handleLabelClassChange)
        
        try:
            self.render = True
            self._renderMgr = RenderingManager( self.editor.view3d )
        except:
            self.render = False

#         def _handleNewLabelClass( model, start, end ):
#             assert start == end
#             self._renderMgr.addObject()
#         self._labelControlUi.labelListModel.rowsInserted.connect( _handleNewLabelClass )
# 
#         def _handleDeletedLabelClass( model, start, end ):
#             assert start == end
#             self._renderMgr.removeObject( start )
#         self._labelControlUi.labelListModel.rowsInserted.connect( _handleDeletedLabelClass )

    def setupLayers(self):
        layers = super( SeededWatershedGui, self ).setupLayers()
        
        self._watershed_layer = None
        if self.topLevelOperatorView.CachedWatershed.ready():
            watershedSource = LazyflowSource( self.topLevelOperatorView.CachedWatershed )

            # Colortable is from base class (LabelingGui)
            # We copy it to ensure that the base class notices when the colortable is changed.
            colortable = list(self._colorTable16)
            watershedLayer = ColortableLayer( watershedSource, colortable )
            watershedLayer.name = "Watershed"
            watershedLayer.visible = True
            layers.insert(0, watershedLayer )
            self._watershed_layer = watershedLayer

        # Fixme: This requires mask to be exactly 1 and 0
        if self.topLevelOperatorView.Mask.ready():
            maskSource = LazyflowSource( self.topLevelOperatorView.Mask )
            maskLayer = ColortableLayer( maskSource, [QColor(0,0,0,255).rgba(), QColor(0,0,0,0)] )
            maskLayer.name = "Mask"
            maskLayer.visible = True
            layers.insert(0, maskLayer )
        return layers

    def _update_rendering(self):
        print "Updating rendering"
        op = self.topLevelOperatorView
        if not self._renderMgr.ready:
            self._renderMgr.setup(op.InputImage.meta.shape[1:4])

        # Remove all objects from the rendering
        self._renderMgr.removeObject(None)
        
        # Now add them back, with correct colors
        colortable = self._watershed_layer.colorTable
        for color_index, color in enumerate(op.LabelColors.value):
            label_value = color_index+1
            color = QColor(colortable[label_value])
            color = (color.red() / 255.0, color.green() / 255.0, color.blue() / 255.0)
            object_id = self._renderMgr.addObject( color=color )
            assert object_id == label_value
            #self._renderMgr.setColor(label_value, color)        

        # Overwrite the data
        volume = op.CachedWatershed().wait()[0,...,0]
        print "watershed max,min = ", volume.max(), volume.min()
        self._renderMgr.volume[:] = volume
        self._renderMgr.update()

    def onLabelColorChanged(self):
        """
        Update the slot that stores label colors.
        """
        colors = []
        for data_item in self.labelListData:
            color = ( data_item.brushColor().red(), data_item.brushColor().green(), data_item.brushColor().blue() )
            colors.append( color )
        self.topLevelOperatorView.LabelColors.setValue( colors )
        
    def onLabelNameChanged(self):
        """
        Update our slot that stores label class names
        """
        names = []
        for data_item in self.labelListData:
            name = data_item.name
            names.append( name )
        self.topLevelOperatorView.LabelNames.setValue( names )
        
