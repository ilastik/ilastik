import os
from functools import partial

import numpy
from PyQt4.QtCore import QTimer
from PyQt4.QtGui import QColor, QMenu, QAction

from volumina.api import ColortableLayer, LazyflowSource
from volumina.view3d.volumeRendering import RenderingManager
from ilastik.applets.labeling.labelingGui import LabelingGui

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

        ws_source_combo = self._labelControlUi.watershedSourceComboBox
        ws_source_combo.addItem( "Grayscale", userData='grayscale' )
        ws_source_combo.addItem( "Probabilities", userData='probabilities' )
        ws_source_combo.currentIndexChanged.connect( self._onWatershedSourceChanged )
        if self.topLevelOperatorView.WatershedSource.value == 'grayscale':
            ws_source_combo.setCurrentIndex( 0 )
        else:
            ws_source_combo.setCurrentIndex( 1 )
        
        self._labelControlUi.bodyIdEdit.setReadOnly(True)
        id_slot = self.topLevelOperatorView.SplittingLabelId
        def _handleLabelChanged( *args ):
            self._labelControlUi.bodyIdEdit.setText( "{}".format( id_slot.value ) )
        id_slot.notifyDirty( _handleLabelChanged )
        
        try:
            self.render = True
            self._renderMgr = RenderingManager( self.editor.view3d )
        except:
            self.render = False
        
    def _after_init(self):
        """
        Override from base class.
        """
        super( SeededWatershedGui, self )._after_init()
        self._navigate_to_focus_point()

    def _navigate_to_focus_point(self):
        op = self.topLevelOperatorView
        if op.FocusCoordinates.ready():
            # Navigate to focus
            coords_dict = op.FocusCoordinates.value
            coord3d = ( coords_dict['x'], coords_dict['y'], coords_dict['z'] )
            self.editor.posModel.cursorPos = list(coord3d)
            self.editor.posModel.slicingPos = list(coord3d)
            self.editor.navCtrl.panSlicingViews( list(coord3d), [0,1,2] )
            
            # Get body id under focus pixel and select it.
            data_position = numpy.array( (0,) + coord3d + (0,) )
            sample_pixel = op.UndersegmentedLabels( data_position, 1+data_position ).wait()
            sample_value = sample_pixel.flat[0]
            self._select_body_id(sample_value)

    def setupLayers(self):
        op = self.topLevelOperatorView
        layers = super( SeededWatershedGui, self ).setupLayers()
        
        self._watershed_layer = None
        if op.CachedWatershed.ready():
            watershedSource = LazyflowSource( op.CachedWatershed )

            # Colortable is from base class (LabelingGui)
            # We copy it to ensure that the base class notices when the colortable is changed.
            colortable = list(self._colorTable16)
            watershedLayer = ColortableLayer( watershedSource, colortable )
            watershedLayer.name = "Watershed"
            watershedLayer.opacity = 0.5
            watershedLayer.visible = True
            layers.insert(1, watershedLayer )
            self._watershed_layer = watershedLayer

        if op.SelectedMask.ready():
            maskSource = LazyflowSource( op.SelectedMask )
            maskLayer = ColortableLayer( maskSource, [QColor(0,0,0,255).rgba(), QColor(0,0,0,0)] )
            maskLayer.name = "Mask"
            maskLayer.opacity = 0.5
            maskLayer.visible = (op.SplittingLabelId.value != 0)
            layers.insert(2, maskLayer )

        if op.InvertedProbability.ready():
            probabilityLayer = self.createStandardLayerFromSlot( op.InvertedProbability )
            probabilityLayer.name = "Probabilities"
            probabilityLayer.visible = ( op.WatershedSource.value == 'probabilities' )
            probabilityLayer.opacity = 1.0
            layers.insert(3, probabilityLayer)

        if op.FinalSegmentation.ready():
            finalSegSource = LazyflowSource( op.FinalSegmentation )
            finalSegLayer = ColortableLayer( finalSegSource, [QColor(0,0,0).rgba()]*256 )
            finalSegLayer.randomizeColors(zeroIsTransparent=False)
            finalSegLayer.name = "Final Segmentation"
            finalSegLayer.visible = False
            finalSegLayer.opacity = 1.0
            layers.insert(3, finalSegLayer)

        return layers

    def _update_rendering(self):
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

    def _onWatershedSourceChanged(self):
        combo = self._labelControlUi.watershedSourceComboBox
        current_data = combo.itemData( combo.currentIndex() )
        ws_source = current_data.toPyObject()
        self.topLevelOperatorView.WatershedSource.setValue( ws_source )

        try:        
            prob_layer = self.find_layer("Probabilities")
            prob_layer.visible = (ws_source == 'probabilities')
            grayscale_layer = self.find_layer("Raw Input")
            grayscale_layer.visible = (ws_source == 'grayscale')
        except ValueError:
            pass

    def find_layer(self, name):
        index = self.layerstack.findMatchingIndex(lambda x: x.name == name)
        return self.layerstack[index]

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
    
    def handleEditorRightClick(self, data_position, globalWindowCoordinate):
        """
        Override from base class.
        """
        data_position = numpy.array(data_position)
        op = self.topLevelOperatorView
        sample_pixel = op.UndersegmentedLabels( data_position, 1+data_position ).wait()
        sample_value = sample_pixel.flat[0]
        
        menu = QMenu( parent=self )
        menu.addAction( QAction("Edit body ID {}".format( sample_value ), menu,
                                triggered=partial(self._select_body_id, sample_value)) )
        menu.exec_(globalWindowCoordinate)
        
    def _select_body_id(self, body_id):
        op = self.topLevelOperatorView
        op.SplittingLabelId.setValue( body_id )
        mask_layer = self.find_layer("Mask")
        mask_layer.visible = (op.SplittingLabelId.value != 0)









