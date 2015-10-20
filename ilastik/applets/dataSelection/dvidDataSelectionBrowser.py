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
        subvol_groupbox.toggled.connect( self._update_display )
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

    def _update_display(self):
        super( DvidDataSelectionBrowser, self )._update_display()
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
    """
    This main section permits simple command-line control.
    usage: contents_browser.py [-h] [--mock-server-hdf5=MOCK_SERVER_HDF5] hostname:port
    
    If --mock-server-hdf5 is provided, the mock server will be launched with the provided hdf5 file.
    Otherwise, the DVID server should already be running on the provided hostname.
    """
    import sys
    import argparse
    from PyQt4.QtGui import QApplication

    handler = logging.StreamHandler()
    logger.addHandler(handler)
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--mock-server-hdf5", required=False)
    parser.add_argument("--mode", choices=["select_existing", "specify_new"], default="select_existing")
    parser.add_argument("hostname", metavar="hostname:port")
    
    sys.argv.append("localhost:8000")

    DEBUG = False
    if DEBUG and len(sys.argv) == 1:
        # default debug args
        parser.print_help()
        print ""
        print "*******************************************************"
        print "No args provided.  Starting with special debug args...."
        print "*******************************************************"
        sys.argv.append("--mock-server-hdf5=/magnetic/mockdvid_gigacube_fortran.h5")
        #sys.argv.append("--mode=specify_new")
        sys.argv.append("localhost:8000")

    parsed_args = parser.parse_args()
    
    server_proc = None
    if parsed_args.mock_server_hdf5:
        from mockserver.h5mockserver import H5MockServer
        hostname, port = parsed_args.hostname.split(":")
        server_proc, shutdown_event = H5MockServer.create_and_start( parsed_args.mock_server_hdf5,
                                                     hostname,
                                                     int(port),
                                                     same_process=False,
                                                     disable_server_logging=False )
    
    app = QApplication([])
    browser = DvidDataSelectionBrowser([parsed_args.hostname], parsed_args.mode)

    try:
        if browser.exec_() == DvidDataSelectionBrowser.Accepted:
            print "The dialog was accepted with result: ", browser.get_selection()
            print "Subvolume roi:", browser.get_subvolume_roi()
        else:
            print "The dialog was rejected."
    finally:
        if server_proc:
            shutdown_event.set()
            server_proc.join()
