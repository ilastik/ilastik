import socket
import logging

import numpy
from PyQt4.QtGui import QVBoxLayout, QGroupBox, QSizePolicy, QMessageBox, QDialogButtonBox

from libdvid import DVIDException, ErrMsg, DVIDNodeService
from libdvid.voxels import VoxelsAccessor, VoxelsMetadata, DVID_BLOCK_WIDTH
from libdvid.gui.contents_browser import ContentsBrowser

from volumina.widgets.subregionRoiWidget import SubregionRoiWidget
from ilastik.utility import log_exception

logger = logging.getLogger(__name__)

class DvidDataSelectionBrowser(ContentsBrowser):
    """
    A subclass of the libdvid ContentsBrowser that includes a widget for optional subvolume selection.
    """
    def __init__(self, *args, **kwargs):
        # Initialize the base class...
        super( DvidDataSelectionBrowser, self ).__init__(*args, **kwargs)

        self._subvol_widget = SubregionRoiWidget( parent=self )

        subvol_layout = QVBoxLayout()
        subvol_layout.addWidget( self._subvol_widget )
        subvol_groupbox = QGroupBox("Specify Region of Interest", parent=self)
        subvol_groupbox.setCheckable(True)
        subvol_groupbox.setChecked(False)
        subvol_groupbox.setEnabled(False)
        subvol_groupbox.toggled.connect( self._update_status )
        subvol_groupbox.setLayout( subvol_layout )
        subvol_groupbox.setFixedHeight( 200 )
        subvol_groupbox.setSizePolicy( QSizePolicy.Preferred, QSizePolicy.Minimum )
        self._subvol_groupbox = subvol_groupbox

        # Add to the layout
        layout = self.layout()
        layout.insertWidget( 3, subvol_groupbox )

    def get_subvolume_roi(self):
        if self._subvol_groupbox.isChecked():
            return self._subvol_widget.roi
        return None

    def _update_status(self):
        super( DvidDataSelectionBrowser, self )._update_status()
        hostname, dset_uuid, dataname, node_uuid, typename = self.get_selection()

        enable_contents = self._repos_info is not None and dataname != "" and node_uuid != ""
        self._subvol_groupbox.setEnabled(enable_contents)

        if not dataname or not node_uuid:
            self._subvol_widget.initWithExtents( "", (), (), () )
            return
        
        error_msg = None
        try:
            if typename == "roi":
                node_service = DVIDNodeService(hostname, node_uuid)
                roi_blocks_xyz = numpy.array( node_service.get_roi(str(dataname)) )
                maxindex = tuple( DVID_BLOCK_WIDTH*(1 + numpy.max( roi_blocks_xyz, axis=0 )) )
                minindex = (0,0,0) # Rois are always 3D
                axiskeys = "xyz"
            else:
                # Query the server
                raw_metadata = VoxelsAccessor.get_metadata( hostname, node_uuid, dataname )
                voxels_metadata = VoxelsMetadata( raw_metadata )
                maxindex = voxels_metadata.shape
                minindex = voxels_metadata.minindex
                axiskeys = voxels_metadata.axiskeys
        except (DVIDException, ErrMsg) as ex:
            error_msg = str(ex)
            log_exception(logger)
        else:
            self._buttonbox.button(QDialogButtonBox.Ok).setEnabled(True)

        if error_msg:
            self._buttonbox.button(QDialogButtonBox.Ok).setEnabled(False)
            QMessageBox.critical(self, "DVID Error", error_msg)
            self._subvol_widget.initWithExtents( "", (), (), () )
            return

        self._subvol_widget.initWithExtents( axiskeys, maxindex, minindex, maxindex )

if __name__ == "__main__":
    # Make the program quit on Ctrl+C
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    from PyQt4.QtGui import QApplication    
    app = QApplication([])
    browser = DvidDataSelectionBrowser(["localhost:8000", "emdata2:7000"],
                                       default_node='57c4c6a0740d4509a02da6b9453204cb',
                                       mode="select_existing")

    if browser.exec_() == DvidDataSelectionBrowser.Accepted:
        print "The dialog was accepted with result: ", browser.get_selection()
    else:
        print "The dialog was rejected."
