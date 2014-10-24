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

from ilastik.workflow import Workflow

from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.nanshe.preprocessing.nanshePreprocessingApplet import NanshePreprocessingApplet
from ilastik.applets.nanshe.dictionaryLearning.nansheDictionaryLearningApplet import NansheDictionaryLearningApplet
from ilastik.applets.nanshe.postprocessing.nanshePostprocessingApplet import NanshePostprocessingApplet

class NansheWorkflow(Workflow):
    def __init__(self, shell, headless, workflow_cmdline_args, project_creation_args):
        # Create a graph to be shared by all operators
        graph = Graph()
        super(NansheWorkflow, self).__init__(shell, headless, workflow_cmdline_args, project_creation_args, graph=graph)
        self._applets = []

        # Create applets 
        self.dataSelectionApplet = DataSelectionApplet(self, "Input Data", "Input Data", supportIlastik05Import=True, batchDataGui=False)
        self.nanshePreprocessingApplet = NanshePreprocessingApplet(self, "Preprocessing", "NanshePreprocessing")
        self.nansheDictionaryLearningApplet = NansheDictionaryLearningApplet(self, "DictionaryLearning", "NansheDictionaryLearning")
        self.nanshePostprocessingApplet = NanshePostprocessingApplet(self, "Postprocessing", "NanshePostprocessing")

        opDataSelection = self.dataSelectionApplet.topLevelOperator
        opDataSelection.DatasetRoles.setValue( ['Raw Data'] )

        self._applets.append( self.dataSelectionApplet )
        self._applets.append( self.nanshePreprocessingApplet )
        self._applets.append( self.nansheDictionaryLearningApplet )
        self._applets.append( self.nanshePostprocessingApplet )

    def connectLane(self, laneIndex):
        opDataSelection = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)        
        opPreprocessing = self.nanshePreprocessingApplet.topLevelOperator.getLane(laneIndex)
        opDictionaryLearning = self.nansheDictionaryLearningApplet.topLevelOperator.getLane(laneIndex)
        opPostprocessing = self.nanshePostprocessingApplet.topLevelOperator.getLane(laneIndex)

        # Connect top-level operators
        opPreprocessing.InputImage.connect( opDataSelection.Image )
        opDictionaryLearning.InputImage.connect( opPreprocessing.Output )
        opPostprocessing.InputImage.connect( opDictionaryLearning.Output )

    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName
