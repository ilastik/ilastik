import argparse
from lazyflow.graph import Graph
from lazyflow.operators.opReorderAxes import OpReorderAxes

from ilastik.workflow import Workflow

from ilastik.applets.projectMetadata import ProjectMetadataApplet
from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.dataSelection.opDataSelection import DatasetInfo
from ilastik.workflows.carving.opPreprocessing import OpFilter
from ilastik.applets.splitBodyCarving.splitBodyCarvingApplet import SplitBodyCarvingApplet
from ilastik.applets.splitBodyPostprocessing.splitBodyPostprocessingApplet import SplitBodyPostprocessingApplet
from ilastik.applets.splitBodySupervoxelExport.splitBodySupervoxelExportApplet import SplitBodySupervoxelExportApplet

from lazyflow.operators.generic import OpSingleChannelSelector

from preprocessingApplet import PreprocessingApplet

from lazyflow.utility.jsonConfig import JsonConfigParser

import logging
logger = logging.getLogger(__name__)

SplitToolParamsSchema = \
{
    "_schema_name" : "split-body workflow params",
    "_schema_version" : 0.1,
    
    # Input data
    "raw_data_info" : JsonConfigParser( DatasetInfo.DatasetInfoSchema ),
    "pixel_probabilities_info" : JsonConfigParser( DatasetInfo.DatasetInfoSchema ),
    "raveler_labels_info" : JsonConfigParser( DatasetInfo.DatasetInfoSchema ),
    
    # Annotation (bookmarks) file
    "raveler_bookmarks_file" : str
}

class SplitBodyCarvingWorkflow(Workflow):
    
    workflowName = "Split Body Tool Workflow"
    defaultAppletIndex = 1 # show DataSelection by default

    DATA_ROLE_RAW = 0
    DATA_ROLE_PIXEL_PROB = 1
    DATA_ROLE_RAVELER_LABELS = 2

    @property
    def applets(self):
        return self._applets
    
    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName

    def __init__(self, headless, workflow_cmdline_args, hintoverlayFile=None, pmapoverlayFile=None, *args, **kwargs):
        graph = Graph()
        
        super(SplitBodyCarvingWorkflow, self).__init__(headless, *args, graph=graph, **kwargs)
        
        ## Create applets 
        self.projectMetadataApplet = ProjectMetadataApplet()
        self.dataSelectionApplet = DataSelectionApplet(self, "Input Data", "Input Data", supportIlastik05Import=True, batchDataGui=False)
        opDataSelection = self.dataSelectionApplet.topLevelOperator

        opDataSelection.DatasetRoles.setValue( ['Raw Data', 'Pixel Probabilities', 'Raveler Labels'] )

        self.preprocessingApplet = PreprocessingApplet(workflow=self,
                                                       title = "Preprocessing",
                                                       projectFileGroupName="preprocessing")
        
        self.splitBodyCarvingApplet = SplitBodyCarvingApplet(workflow=self,
                                                             projectFileGroupName="carving")
        
        self.splitBodyPostprocessingApplet = SplitBodyPostprocessingApplet(workflow=self)
        self.splitBodySupervoxelExportApplet = SplitBodySupervoxelExportApplet(workflow=self)
        
        # Expose to shell
        self._applets = []
        self._applets.append(self.projectMetadataApplet)
        self._applets.append(self.dataSelectionApplet)
        self._applets.append(self.preprocessingApplet)
        self._applets.append(self.splitBodyCarvingApplet)
        self._applets.append(self.splitBodyPostprocessingApplet)
        self._applets.append(self.splitBodySupervoxelExportApplet)

        self._split_tool_params = None
        if workflow_cmdline_args:
            arg_parser = argparse.ArgumentParser(description="Specify parameters for the split-body carving workflow")
            arg_parser.add_argument('--split_tool_param_file', required=False)
            parsed_args, unused_args = arg_parser.parse_known_args(workflow_cmdline_args)
            if unused_args:
                logger.warn("Unused command-line args: {}".format( unused_args ))

            if parsed_args.split_tool_param_file is None:
                logger.warn("Missing cmd-line arg: --split_tool_param_file")
            else:
                logger.debug("Parsing split tool parameters: {}".format( parsed_args.split_tool_param_file ))
                json_parser = JsonConfigParser( SplitToolParamsSchema )
                self._split_tool_params = json_parser.parseConfigFile( parsed_args.split_tool_param_file )
    
    def onProjectLoaded(self, projectManager):
        """
        Overridden from Workflow base class.  Called by the Project Manager.
        
        - Use the parameter json file provided on the command line to populate the project's input data settings.
        - Also set the annotation file location.
        - Run the preprocessing step.
        - Save the project.
        """
        if self._split_tool_params is None:
            return
        
        # -- Data Selection
        opDataSelection = self.dataSelectionApplet.topLevelOperator
        
        # If there is already data in this project, don't touch it.
        if len(opDataSelection.DatasetGroup) > 0:
            logger.warn("Not using cmd-line args because project appears to have data already.")
            return
        
        opDataSelection.DatasetGroup.resize(1)
        for role, data_params in [ ( self.DATA_ROLE_RAW,             self._split_tool_params.raw_data_info ),
                                   ( self.DATA_ROLE_PIXEL_PROB,      self._split_tool_params.pixel_probabilities_info ),
                                   ( self.DATA_ROLE_RAVELER_LABELS,  self._split_tool_params.raveler_labels_info ) ]:
            logger.debug( "Configuring dataset for role {}".format( role ) )
            logger.debug( "Params: {}".format(data_params) )
            datasetInfo = DatasetInfo()
            datasetInfo.updateFromJson( data_params )

            # Check for globstring, which means we need to import the stack first.            
            if '*' in datasetInfo.filePath:
                totalProgress = [-100]
                def handleStackImportProgress( progress ):
                    if progress / 10 != totalProgress[0] / 10:
                        totalProgress[0] = progress
                        logger.info( "Importing stack: {}%".format( totalProgress[0] ) )
                serializer = self.dataSelectionApplet.dataSerializers[0]
                serializer.progressSignal.connect( handleStackImportProgress )
                serializer.importStackAsLocalDataset( datasetInfo )
            
            opDataSelection.DatasetGroup[0][ role ].setValue( datasetInfo )


        # -- Split settings (annotation file)
        opSplitBodyCarving = self.splitBodyCarvingApplet.topLevelOperator.getLane(0)
        opSplitBodyCarving.AnnotationFilepath.setValue( self._split_tool_params.raveler_bookmarks_file )
        
        # -- Preprocessing settings
        opPreprocessing = self.preprocessingApplet.topLevelOperator.getLane(0)
        opPreprocessing.Sigma.setValue(1.0)
        opPreprocessing.Filter.setValue( OpFilter.RAW )

        # Run preprocessing
        def showProgress( progress ):
            logger.info( "Preprocessing Progress: {}%".format( progress ) )
        self.preprocessingApplet.progressSignal.connect( showProgress )
        opPreprocessing.PreprocessedData[:].wait()
        logger.info("Preprocessing Complete")
        
        logger.info("Saving project...")
        projectManager.saveProject()

    def connectLane(self, laneIndex):
        ## Access applet operators
        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opPreprocessing = self.preprocessingApplet.topLevelOperator.getLane(laneIndex)
        opSplitBodyCarving = self.splitBodyCarvingApplet.topLevelOperator.getLane(laneIndex)
        opPostprocessing = self.splitBodyPostprocessingApplet.topLevelOperator.getLane(laneIndex)

        op5Raw = OpReorderAxes(parent=self)
        op5Raw.AxisOrder.setValue("txyzc")
        op5Raw.Input.connect(opData.ImageGroup[self.DATA_ROLE_RAW])
        
        op5PixelProb = OpReorderAxes(parent=self)
        op5PixelProb.AxisOrder.setValue("txyzc")
        op5PixelProb.Input.connect(opData.ImageGroup[self.DATA_ROLE_PIXEL_PROB])

        op5RavelerLabels = OpReorderAxes(parent=self)
        op5RavelerLabels.AxisOrder.setValue("txyzc")
        op5RavelerLabels.Input.connect(opData.ImageGroup[self.DATA_ROLE_RAVELER_LABELS])

        # We assume the membrane boundaries are found in the first prediction class (channel 0)
        opSingleChannelSelector = OpSingleChannelSelector(parent=self)
        opSingleChannelSelector.Input.connect( op5PixelProb.Output )
        opSingleChannelSelector.Index.setValue(0)
        
        opPreprocessing.InputData.connect( opSingleChannelSelector.Output )
        opPreprocessing.RawData.connect( op5Raw.Output )
        opSplitBodyCarving.RawData.connect( op5Raw.Output )
        opSplitBodyCarving.InputData.connect( opSingleChannelSelector.Output )
        opSplitBodyCarving.RavelerLabels.connect( op5RavelerLabels.Output )
        opSplitBodyCarving.FilteredInputData.connect( opPreprocessing.FilteredImage )

        # Special input-input connection: WriteSeeds metadata must mirror the input data
        opSplitBodyCarving.WriteSeeds.connect( opSplitBodyCarving.InputData )

        opSplitBodyCarving.MST.connect(opPreprocessing.PreprocessedData)
        opSplitBodyCarving.UncertaintyType.setValue("none")
        
        opPostprocessing.RawData.connect( opSplitBodyCarving.RawData )
        opPostprocessing.InputData.connect( opSplitBodyCarving.InputData )
        opPostprocessing.RavelerLabels.connect( opSplitBodyCarving.RavelerLabels )
        opPostprocessing.MST.connect(opSplitBodyCarving.MstOut)

        # Split-body carving -> Postprocessing
        opPostprocessing.EditedRavelerBodyList.connect(opSplitBodyCarving.EditedRavelerBodyList)
        opPostprocessing.NavigationCoordinates.connect(opSplitBodyCarving.NavigationCoordinates)

        self.preprocessingApplet.enableDownstream(False)

        # Supervoxel export
        opSupervoxelExport = self.splitBodySupervoxelExportApplet.topLevelOperator.getLane(laneIndex)
        opSupervoxelExport.DatasetInfos.connect( opData.DatasetGroup )
        opSupervoxelExport.WorkingDirectory.connect( opData.WorkingDirectory )
        opSupervoxelExport.RawData.connect( opPreprocessing.RawData )
        opSupervoxelExport.InputData.connect( opPreprocessing.InputData )
        opSupervoxelExport.Supervoxels.connect( opPreprocessing.WatershedImage )
        opSupervoxelExport.RavelerLabels.connect( opSplitBodyCarving.RavelerLabels )
        opSupervoxelExport.AnnotationBodyIds.connect( opSplitBodyCarving.AnnotationBodyIds )
        
