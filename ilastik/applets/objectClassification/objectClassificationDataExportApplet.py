from ilastik.applets.dataExport.dataExportApplet import DataExportApplet

class ObjectClassificationDataExportApplet( DataExportApplet ):
    """
    This a specialization of the generic data export applet that
    provides a special viewer for object classification predictions.
    """
        
    def getMultiLaneGui(self):
        if self._gui is None:
            # Gui is a special subclass of the generic gui
            from objectClassificationDataExportGui import ObjectClassificationDataExportGui
            self._gui = ObjectClassificationDataExportGui( self, self.topLevelOperator )
        return self._gui





