from ilastik.applets.dataExport.opDataExport import OpDataExport


class OpObjectClassificationDataExport(OpDataExport):
    """
    Used to override the default behaviour of OpDataExport operator, i.e. skip the run_export method
    when Object Feature Table is to be exported, since we do not export an image lane, but merely the table.
    """

    # Feature Table export source name
    ObjectFeaturesTable = 'Feature Table'

    def __init__(self, *args, **kwargs):
        super(OpObjectClassificationDataExport, self).__init__(*args, **kwargs)

    def run_export(self):
        '''
        We only run the export method of the parent export operator if we are not exporting Object Features Table
        '''
        selected_name = self.SelectionNames.value[self.InputSelection.value]
        if selected_name != self.ObjectFeaturesTable:
            super().run_export()
