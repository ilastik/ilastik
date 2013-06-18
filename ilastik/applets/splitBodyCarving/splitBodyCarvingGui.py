import sys
import os
from functools import partial
import numpy

from PyQt4.QtGui import QColor, QShortcut, QKeySequence

from lazyflow.roi import TinyVector

from volumina.layer import ColortableLayer
from volumina.pixelpipeline.datasources import LazyflowSource

from ilastik.workflows.carving.carvingGui import CarvingGui
from lazyflow.request import Request
from lazyflow.roi import roiToSlice

from opSplitBodyCarving import OpSplitBodyCarving

from bodySplitInfoWidget import BodySplitInfoWidget

from ilastik.applets.labeling.labelingGui import Tool

from ilastik.utility.gui import threadRouted, ThunkEventHandler, ThunkEvent

class SplitBodyCarvingGui(CarvingGui):
    
    def __init__(self, topLevelOperatorView):
        drawerUiPath = os.path.join( os.path.split(__file__)[0], 'splitBodyCarvingDrawer.ui' )
        super( SplitBodyCarvingGui, self ).__init__(topLevelOperatorView, drawerUiPath=drawerUiPath)
        self._splitInfoWidget = BodySplitInfoWidget(self, self.topLevelOperatorView)
        self._splitInfoWidget.navigationRequested.connect( self._handleNavigationRequest )
        self._labelControlUi.annotationWindowButton.pressed.connect( self._splitInfoWidget.show )
        
        # Hide all controls related to uncertainty; they aren't used in this applet
        self._labelControlUi.uncertaintyLabel.hide()
        self._labelControlUi.uncertaintyCombo.hide()
        self._labelControlUi.pushButtonUncertaintyFG.hide()
        self._labelControlUi.pushButtonUncertaintyBG.hide()
        
        # Hide manual save buttons; user must use the annotation window to save/load objects
        self._labelControlUi.saveControlLabel.hide()
        self._labelControlUi.save.hide()
        self._labelControlUi.saveAs.hide()
        self._labelControlUi.namesButton.hide()

        self.thunkEventHandler = ThunkEventHandler(self)

        fragmentColors = [ QColor(0,0,0,0), # transparent (background)
                           QColor(0, 255, 255),   # cyan
                           QColor(255, 0, 255),   # magenta
                           QColor(0, 0, 128),     # navy
                           QColor(165,  42,  42), # brown        
                           QColor(255, 105, 180), # hot pink
                           QColor(255, 165, 0),   # orange
                           QColor(173, 255,  47), # green-yellow
                           QColor(102, 205, 170), # dark aquamarine
                           QColor(128,0, 128),    # purple
                           QColor(240, 230, 140), # khaki
                           QColor(192, 192, 192), # silver
                           QColor(69, 69, 69) ]   # dark grey

        self._fragmentColors = fragmentColors

        # In this workflow, you aren't allowed to make brushstrokes unless there is a "current fragment"
        def handleEditingFragmentChange(slot, *args):
            if slot.value == "":
                self._changeInteractionMode(Tool.Navigation)
            else:
                self._changeInteractionMode(Tool.Paint)
            self._labelControlUi.paintToolButton.setEnabled( slot.value != "" )
            self._labelControlUi.eraserToolButton.setEnabled( slot.value != "" )
            self._labelControlUi.labelListView.setEnabled( slot.value != "" )
        topLevelOperatorView.CurrentEditingFragment.notifyDirty( handleEditingFragmentChange )
        handleEditingFragmentChange(topLevelOperatorView.CurrentEditingFragment)

    def _handleNavigationRequest(self, coord3d):
        self.editor.posModel.cursorPos = list(coord3d)
        self.editor.posModel.slicingPos = list(coord3d)
        self.editor.navCtrl.panSlicingViews( list(coord3d), [0,1,2] )
        
    def labelingContextMenu(self, names, op, position5d):
        return None
#        pos = TinyVector(position5d)
#        sample_roi = (pos, pos+1)
#        ravelerLabelSample = self.topLevelOperatorView.RavelerLabels(*sample_roi).wait()
#        ravelerLabel = ravelerLabelSample[0,0,0,0,0]
#        
#        menu = super( SplitBodyCarvingGui, self ).labelingContextMenu(names, op, position5d)
#        menu.addSeparator()
#        highlightAction = menu.addAction( "Highlight Raveler Object {}".format( ravelerLabel ) )
#        highlightAction.triggered.connect( partial(self.topLevelOperatorView.CurrentRavelerLabel.setValue, ravelerLabel ) )
#
#        # Auto-seed also auto-highlights
#        autoSeedAction = menu.addAction( "Auto-seed background for Raveler Object {}".format( ravelerLabel ) )
#        autoSeedAction.triggered.connect( partial(OpSplitBodyCarving.autoSeedBackground, self.topLevelOperatorView, ravelerLabel ) )
#        autoSeedAction.triggered.connect( partial(self.topLevelOperatorView.CurrentRavelerLabel.setValue, ravelerLabel ) )
#        return menu

    def _update_rendering(self):
        """
        Override from the base class.
        """
        # This update has to be performed in a different thread to avoid a deadlock
        # (Because this function is running in the context of a dirty notification!)
        req = Request( self.__update_rendering )
        def handle_rendering_failure( exc, exc_info ):
            import traceback
            traceback.print_exception(*exc_info)
            sys.stderr.write("Exception raised during volume rendering update.  See traceack above.\n")
        req.notify_failed( handle_rendering_failure )
        req.submit()
    
    def __update_rendering(self):
        if not self.render:
            return

        if not self._labelControlUi.activate3DViewCheckbox.isChecked():
            return 

        rendered_volume_shape = (250, 250, 250)

        print "Starting to update 3D volume data"

        fragmentColors = self._fragmentColors
        op = self.topLevelOperatorView
        if not self._renderMgr.ready:
            self._renderMgr.setup(op.InputData.meta.shape[1:4])
        self._renderMgr.clear()
        
        # Create a 5D view of the render mgr's memory
        totalRenderVol5d = self._renderMgr.volume[numpy.newaxis, ..., numpy.newaxis]

        # Block must not exceed total bounds.
        # Shift start up if necessary
        rendering_start_3d = TinyVector(self.editor.posModel.slicingPos) - TinyVector(rendered_volume_shape)/2.0
        rendering_start_3d = numpy.maximum( (0,0,0), rendering_start_3d )

        # Compute stop and shift down if necessary
        rendering_stop_3d = rendering_start_3d + TinyVector(rendered_volume_shape)
        rendering_stop_3d = numpy.minimum( op.InputData.meta.shape[1:4], rendering_stop_3d )
        
        # Recompute start now that stop has been computed
        rendering_start_3d = rendering_stop_3d - TinyVector(rendered_volume_shape)

        rendering_roi_5d = ( (0,) + tuple(rendering_start_3d) + (0,),
                             (1,) + tuple(rendering_stop_3d) + (1,) )

        # View only the data we want to update.
        renderVol5d = totalRenderVol5d[roiToSlice( *rendering_roi_5d )]

        ravelerLabel = op.CurrentRavelerLabel.value
        if ravelerLabel != 0:
            print " Asking for fragment segmentation"
            op.CurrentFragmentSegmentation(*rendering_roi_5d).writeInto(renderVol5d).wait()
            print " Obtained Fragment Segmentation"

            fragmentNames = op.getFragmentNames(ravelerLabel)
            numFragments = len(fragmentNames)

            renderLabels = []
            for i, name in enumerate(fragmentNames):
                if name != op.CurrentEditingFragment.value:
                    assert i < len(self._fragmentColors), "Too many fragments: colortable is too small"
                    color = ( fragmentColors[i+1].red() / 255.0,
                              fragmentColors[i+1].green() / 255.0,
                              fragmentColors[i+1].blue() / 255.0 )
                    renderLabel = self._renderMgr.addObject( color=color )
                    renderLabels.append( renderLabel )

            if op.CurrentEditingFragment.value != "":
                print " Asking for masked editing segmentation"
                maskedSegmentation = op.MaskedSegmentation(*rendering_roi_5d).wait()
                print " Obtained for masked editing segmentation"
                segLabel = numFragments

                print " Start updating volume data with masked segmentation"
                renderVol5d[:] = numpy.where(maskedSegmentation != 0, segLabel, renderVol5d)
                print " Finished updating volume data with masked segmentation"

                segmentationColor = (0.0, 1.0, 0.0)
                renderLabel = self._renderMgr.addObject( color=segmentationColor )
                renderLabels.append( renderLabel )

            # Relabel with the labels we were given by the renderer.
            # (We can skip this step if the renderer is guaranteed to give labels 1,2,3...)
            if renderLabels != list(range(len(renderLabels))):
                renderVol5d[:] = numpy.array([0] + renderLabels)[renderVol5d]

        print "Finished updating 3D volume data"
        self.thunkEventHandler.post(self._refreshRenderMgr)

    @threadRouted
    def _refreshRenderMgr(self):
        """
        The render mgr can segfault if this isn't called from the main thread.
        """
        print "Begin render update"
        self._renderMgr.update()
        print "End render update"

    
    def setupLayers(self):
        def findLayer(f, layerlist):
            for l in layerlist:
                if f(l):
                    return l
            return None

        layers = []
        baseCarvingLayers = super(SplitBodyCarvingGui, self).setupLayers()        
        
        crosshairSlot = self.topLevelOperatorView.AnnotationCrosshairs
        if crosshairSlot.ready():
            # 0=Transparent, 1=pink
            colortable = [QColor(0, 0, 0, 0).rgba(), QColor(236, 184, 201).rgba()]
            crosshairLayer = ColortableLayer(LazyflowSource(crosshairSlot), colortable, direct=True)
            crosshairLayer.name = "Annotation Points"
            crosshairLayer.visible = True
            crosshairLayer.opacity = 1.0
            layers.append(crosshairLayer)
        
        
        highlightedObjectSlot = self.topLevelOperatorView.CurrentRavelerObject
        if highlightedObjectSlot.ready():
            # 0=Transparent, 1=blue
            colortable = [QColor(0, 0, 0, 0).rgba(), QColor(0, 0, 255).rgba()]
            highlightedObjectLayer = ColortableLayer(LazyflowSource(highlightedObjectSlot), colortable, direct=True)
            highlightedObjectLayer.name = "Current Raveler Object"
            highlightedObjectLayer.visible = False
            highlightedObjectLayer.opacity = 0.25
            layers.append(highlightedObjectLayer)

        remainingRavelerObjectSlot = self.topLevelOperatorView.CurrentRavelerObjectRemainder
        if remainingRavelerObjectSlot.ready():
            # 0=Transparent, 1=blue
            colortable = [QColor(0, 0, 0, 0).rgba(), QColor(255, 0, 0).rgba()]
            remainingObjectLayer = ColortableLayer(LazyflowSource(remainingRavelerObjectSlot), colortable, direct=True)
            remainingObjectLayer.name = "Remaining Raveler Object"
            remainingObjectLayer.visible = True
            remainingObjectLayer.opacity = 0.25
            layers.append(remainingObjectLayer)

        fragmentSegSlot = self.topLevelOperatorView.CurrentFragmentSegmentation
        if fragmentSegSlot.ready():
            colortable = map(QColor.rgba, self._fragmentColors)
            fragSegLayer = ColortableLayer(LazyflowSource(fragmentSegSlot), colortable, direct=True)
            fragSegLayer.name = "Saved Fragments"
            fragSegLayer.visible = True
            fragSegLayer.opacity = 0.25
            layers.append(fragSegLayer)

        ravelerLabelsSlot = self.topLevelOperatorView.RavelerLabels
        if ravelerLabelsSlot.ready():
            colortable = []
            for i in range(256):
                r,g,b = numpy.random.randint(0,255), numpy.random.randint(0,255), numpy.random.randint(0,255)
                colortable.append(QColor(r,g,b).rgba())
            ravelerLabelLayer = ColortableLayer(LazyflowSource(ravelerLabelsSlot), colortable, direct=True)
            ravelerLabelLayer.name = "Raveler Labels"
            ravelerLabelLayer.visible = False
            ravelerLabelLayer.opacity = 0.4
            layers.append(ravelerLabelLayer)

        maskedSegSlot = self.topLevelOperatorView.MaskedSegmentation
        if maskedSegSlot.ready():
            colortable = [QColor(0,0,0,0).rgba(), QColor(0,0,0,0).rgba(), QColor(0,255,0).rgba()]
            maskedSegLayer = ColortableLayer(LazyflowSource(maskedSegSlot), colortable, direct=True)
            maskedSegLayer.name = "Masked Segmentation"
            maskedSegLayer.visible = True
            maskedSegLayer.opacity = 0.3
            layers.append(maskedSegLayer)
            
            # Hide the original carving segmentation.
            # TODO: Remove it from the list altogether?
            carvingSeg = findLayer( lambda l: l.name == "segmentation", baseCarvingLayers )
            if carvingSeg is not None:
                carvingSeg.visible = False

        def removeBaseLayer(layerName):
            layer = findLayer(lambda l: l.name == layerName, baseCarvingLayers)
            if layer:
                baseCarvingLayers.remove(layer)

        # Don't show carving layers that aren't relevant to the split-body workflow
        removeBaseLayer( "uncertainty" )
        removeBaseLayer( "done seg" )
        removeBaseLayer( "pmap" )
        removeBaseLayer( "hints" )
        removeBaseLayer( "done" )
        removeBaseLayer( "done" )
        
        # Attach a shortcut to the raw data layer
        if self.topLevelOperatorView.RawData.ready():
            rawLayer = findLayer(lambda l: l.name == "raw", baseCarvingLayers)
            assert rawLayer is not None, "Couldn't find the raw data layer.  Did it's name change?"
            rawLayer.shortcutRegistration = ( "Carving",
                                              "Raw Data to Top",
                                              QShortcut( QKeySequence("f"),
                                                         self.viewerControlWidget(),
                                                         partial(self._toggleRawDataPosition, rawLayer) ),
                                             rawLayer )
        layers += baseCarvingLayers
        return layers

    def _toggleRawDataPosition(self, rawLayer):
        index = self.layerstack.layerIndex(rawLayer)
        self.layerstack.selectRow( index )
        if index <= 2:
            self.layerstack.moveSelectedToBottom()
        else:
            # Move it almost to the top (under the seeds and the annotation crosshairs)
            self.layerstack.moveSelectedToRow(2)
            