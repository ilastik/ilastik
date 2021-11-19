from ilastik.workflows.pixelClassification import PixelClassificationWorkflow
from ilastik.applets.pixelClassification import PixelClassificationDataExportApplet
from ilastik.applets.pixelClassificationEnhancer import PixelClassificationEnhancerApplet
from ilastik.applets.batchProcessing import BatchProcessingApplet
from lazyflow.graph import Graph


class PixelClassificationEnhancerWorkflow(PixelClassificationWorkflow):
    workflowName = "Pixel Classification Enhancer"
    workflowDisplayName = "Pixel Classification Enhancer"
    workflowDescription = "Augment your predictions with Enhancer Neural Network."

    def __init__(self, shell, headless, workflow_cmdline_args, project_creation_args, *args, **kwargs):
        # Applets for training (interactive) workflow
        graph = Graph()
        super(PixelClassificationWorkflow, self).__init__(
            shell, headless, workflow_cmdline_args, project_creation_args, graph=graph, *args, **kwargs
        )
        self.stored_classifier = None
        self._applets = []
        self._workflow_cmdline_args = workflow_cmdline_args
        self.dataSelectionApplet = self.createDataSelectionApplet()
        opDataSelection = self.dataSelectionApplet.topLevelOperator

        data_instructions = (
            "Select your input data using the 'Raw Data' tab shown on the right.\n\n"
            "Power users: Optionally use the 'Prediction Mask' tab to supply a binary image that tells ilastik where it should avoid computations you don't need."
        )

        self.featureSelectionApplet = self.createFeatureSelectionApplet()

        self.pcApplet = self.createPixelClassificationEnhancerApplet()
        opClassify = self.pcApplet.topLevelOperator

        self.dataExportApplet = PixelClassificationDataExportApplet(self, "Prediction Export")
        opDataExport = self.dataExportApplet.topLevelOperator
        opDataExport.PmapColors.connect(opClassify.PmapColors)
        opDataExport.LabelNames.connect(opClassify.LabelNames)
        opDataExport.WorkingDirectory.connect(opDataSelection.WorkingDirectory)
        opDataExport.SelectionNames.setValue(self.ExportNames.asDisplayNameList())

        # Expose for shell
        self._applets.append(self.dataSelectionApplet)
        self._applets.append(self.featureSelectionApplet)
        self._applets.append(self.pcApplet)
        self._applets.append(self.dataExportApplet)

        self.dataExportApplet.prepare_for_entire_export = self.prepare_for_entire_export
        self.dataExportApplet.post_process_entire_export = self.post_process_entire_export

        self.batchProcessingApplet = BatchProcessingApplet(
            self, "Batch Processing", self.dataSelectionApplet, self.dataExportApplet
        )

        # meh:
        self.generate_random_labels = False
        self.print_labels_by_slice = False
        self.variable_importance_path = False
        self.tree_count = False
        self.label_proportion = False
        self.retrain = False

        # meh pt. 2
        self._batch_export_args = False
        self._batch_input_args = False

    def createPixelClassificationEnhancerApplet(self):
        return PixelClassificationEnhancerApplet(self, "PixelClassificationEnhancer")
