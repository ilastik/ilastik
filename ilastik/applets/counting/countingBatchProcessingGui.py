from PyQt4.QtGui import QPushButton, QFileDialog
from ilastik.applets.batchProcessing.batchProcessingGui import BatchProcessingGui

class CountingBatchProcessingGui(BatchProcessingGui):
    
    def __init__(self, *args, **kwargs):
        super( CountingBatchProcessingGui, self ).__init__(*args, **kwargs)
        self.csv_export_path = None
        self.csv_export_file = None
    
    def initAppletDrawerUi(self):
        super( CountingBatchProcessingGui, self ).initAppletDrawerUi()
        self.select_csv_path_button = QPushButton("Select CSV Export Location...", clicked=self.select_csv_location)
        self._drawer.layout().insertWidget(1, self.select_csv_path_button)

    def select_csv_location(self):
        self.csv_export_path = QFileDialog.getSaveFileName(parent=self, caption="Exported Object Counts", filter="*.csv")

    def run_export(self):
        """
        Overridden from base class.
        """
        if self.csv_export_path:
            self.csv_export_file = open( self.csv_export_path, 'w' )
        super( CountingBatchProcessingGui, self ).run_export()

    def post_process_lane(self, lane_index):
        """
        Overridden from base class.
        """
        if self.csv_export_file:
            self.parentApplet.countingDataExportApplet.write_csv_results(self.csv_export_file, lane_index)

    def handle_batch_processing_complete(self):
        """
        Overridden from base class.
        """
        if self.csv_export_file:
            self.csv_export_file.close()
            self.csv_export_file = None
