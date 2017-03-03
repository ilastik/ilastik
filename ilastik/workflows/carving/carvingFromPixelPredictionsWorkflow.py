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
from lazyflow.graph import Graph
from lazyflow.operators.opReorderAxes import OpReorderAxes

from ilastik.workflow import Workflow

from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.featureSelection import FeatureSelectionApplet
from ilastik.applets.pixelClassification import PixelClassificationApplet

from lazyflow.operators import OpSingleChannelSelector

from carvingApplet import CarvingApplet
from preprocessingApplet import PreprocessingApplet

import ilastik.config
if ilastik.config.cfg.getboolean('ilastik', 'debug'):
    class CarvingFromPixelPredictionsWorkflow(Workflow):
        
        workflowName = "Carving From Pixel Predictions"
        defaultAppletIndex = 0 # show DataSelection by default
        
        @property
        def applets(self):
            return self._applets
        
        @property
        def imageNameListSlot(self):
            return self.dataSelectionApplet.topLevelOperator.ImageName
    
        def __init__(self, shell, headless, workflow_cmdline_args, project_creation_args, hintoverlayFile=None, pmapoverlayFile=None, *args, **kwargs):
            if workflow_cmdline_args:
                assert False, "Not using workflow cmdline args yet."
            
            if hintoverlayFile is not None:
                assert isinstance(hintoverlayFile, str), "hintoverlayFile should be a string, not '%s'" % type(hintoverlayFile)
            if pmapoverlayFile is not None:
                assert isinstance(pmapoverlayFile, str), "pmapoverlayFile should be a string, not '%s'" % type(pmapoverlayFile)
    
            graph = Graph()
            
            super(CarvingFromPixelPredictionsWorkflow, self).__init__(shell, headless, workflow_cmdline_args, project_creation_args, *args, graph=graph, **kwargs)
            
            ## Create applets 
            self.dataSelectionApplet = DataSelectionApplet(self, "Input Data", "Input Data", supportIlastik05Import=True, batchDataGui=False)
            opDataSelection = self.dataSelectionApplet.topLevelOperator
            opDataSelection.DatasetRoles.setValue( ['Raw Data'] )
    
            self.featureSelectionApplet = FeatureSelectionApplet(self, "Feature Selection", "FeatureSelections")
            self.pixelClassificationApplet = PixelClassificationApplet(self, "PixelClassification")
            
            self.carvingApplet = CarvingApplet(workflow=self,
                                               projectFileGroupName="carving",
                                               hintOverlayFile=hintoverlayFile,
                                               pmapOverlayFile=pmapoverlayFile)
            
            self.preprocessingApplet = PreprocessingApplet(workflow=self,
                                               title = "Preprocessing",
                                               projectFileGroupName="carving")
            
            #self.carvingApplet.topLevelOperator.MST.connect(self.preprocessingApplet.topLevelOperator.PreprocessedData)
            
            # Expose to shell
            self._applets = []
            self._applets.append(self.dataSelectionApplet)
            self._applets.append(self.featureSelectionApplet)
            self._applets.append(self.pixelClassificationApplet)
            self._applets.append(self.preprocessingApplet)
            self._applets.append(self.carvingApplet)
            
        def connectLane(self, laneIndex):
            ## Access applet operators
            opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
            opFeatureSelection = self.featureSelectionApplet.topLevelOperator.getLane(laneIndex)
            opPixelClassification = self.pixelClassificationApplet.topLevelOperator.getLane(laneIndex)
            opPreprocessing = self.preprocessingApplet.topLevelOperator.getLane(laneIndex)
            opCarvingLane = self.carvingApplet.topLevelOperator.getLane(laneIndex)
    
            op5 = OpReorderAxes(parent=self)
            op5.AxisOrder.setValue("txyzc")
            op5.Input.connect(opData.Image)
            
            ## Connect operators
            opFeatureSelection.InputImage.connect( op5.Output )
            opPixelClassification.InputImages.connect( op5.Output )
            opPixelClassification.FeatureImages.connect( opFeatureSelection.OutputImage )
            opPixelClassification.CachedFeatureImages.connect( opFeatureSelection.CachedOutputImage )
            
            # We assume the membrane boundaries are found in the first prediction class (channel 0)
            opSingleChannelSelector = OpSingleChannelSelector(parent=self)
            opSingleChannelSelector.Input.connect( opPixelClassification.PredictionProbabilities )
            opSingleChannelSelector.Index.setValue(0)
            
            opPreprocessing.OverlayData.connect( op5.Output )
            opPreprocessing.InputData.connect( opSingleChannelSelector.Output )

            opCarvingLane.OverlayData.connect( op5.Output )
            opCarvingLane.InputData.connect( opSingleChannelSelector.Output )
            opCarvingLane.FilteredInputData.connect( opPreprocessing.FilteredImage )
    
            # Special input-input connection: WriteSeeds metadata must mirror the input data
            opCarvingLane.WriteSeeds.connect( opCarvingLane.InputData )
    
            opCarvingLane.MST.connect(opPreprocessing.PreprocessedData)
            opCarvingLane.UncertaintyType.setValue("none")
            
            self.preprocessingApplet.enableDownstream(False)
