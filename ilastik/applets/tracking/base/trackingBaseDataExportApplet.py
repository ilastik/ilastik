from ilastik.applets.dataExport.dataExportApplet import DataExportApplet

class TrackingBaseDataExportApplet( DataExportApplet ):
    """
    This a specialization of the generic data export applet that
    provides a special viewer for trackign output.
    """
        
    def getMultiLaneGui(self):
        if self._gui is None:
            # Gui is a special subclass of the generic gui
            from trackingBaseDataExportGui import TrackingBaseDataExportGui
            self._gui = TrackingBaseDataExportGui( self, self.topLevelOperator )
        return self._gui





