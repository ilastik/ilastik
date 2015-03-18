import httplib
import socket
import logging

import pydvid
from pydvid.gui.contents_browser import ContentsBrowser

from volumina.widgets.subregionRoiWidget import SubregionRoiWidget
from PyQt4.QtGui import QVBoxLayout, QGroupBox, QSizePolicy, QMessageBox, QDialogButtonBox

from ilastik.utility import log_exception

logger = logging.getLogger(__name__)

class DvidDataSelectionBrowser(ContentsBrowser):
    """
    A subclass of the pydvid ContentsBrowser that includes a widget for optional subvolume selection.
    """
    def __init__(self, *args, **kwargs):
        # Initialize the base class...
        super( DvidDataSelectionBrowser, self ).__init__(*args, **kwargs)

        self._roi_widget = SubregionRoiWidget( parent=self )

        roi_layout = QVBoxLayout()
        roi_layout.addWidget( self._roi_widget )
        roi_groupbox = QGroupBox("Specify Region of Interest", parent=self)
        roi_groupbox.setCheckable(True)
        roi_groupbox.setChecked(False)
        roi_groupbox.setEnabled(False)
        roi_groupbox.toggled.connect( self._update_display )
        roi_groupbox.setLayout( roi_layout )
        roi_groupbox.setFixedHeight( 200 )
        roi_groupbox.setSizePolicy( QSizePolicy.Preferred, QSizePolicy.Minimum )
        self._roi_groupbox = roi_groupbox

        # Add to the layout
        layout = self.layout()
        layout.insertWidget( 3, roi_groupbox )

    def get_subvolume_roi(self):
        if self._roi_groupbox.isChecked():
            return self._roi_widget.roi
        return None

    def _update_display(self):
        super( DvidDataSelectionBrowser, self )._update_display()
        hostname, dset_uuid, dataname, node_uuid = self.get_selection()

        enable_contents = self._repos_info is not None and dataname != "" and node_uuid != ""
        self._roi_groupbox.setEnabled(enable_contents)

        if not dataname or not node_uuid:
            self._roi_widget.initWithExtents( "", (), (), () )
            return
        
        error_msg = None
        try:
            # Query the server
            connection = httplib.HTTPConnection( hostname )
            raw_metadata = pydvid.voxels.get_metadata( connection, node_uuid, dataname )
            voxels_metadata = pydvid.voxels.VoxelsMetadata( raw_metadata )
        except socket.error as ex:
            error_msg = "Socket Error: {} (Error {})".format( ex.args[1], ex.args[0] )
        except httplib.HTTPException as ex:
            error_msg = "HTTP Error: {}".format( ex.args[0] )
        except pydvid.errors.DvidHttpError as ex:
            # DVID will return an error if the selected dataset 
            #  isn't a 'voxels' dataset and thus has no voxels metadata
            # In that case, show the error on the console, and don't let the user hit 'okay'.
            log_exception( logger, level=logging.WARN )
            self._buttonbox.button(QDialogButtonBox.Ok).setEnabled(False)
            return
        else:
            self._buttonbox.button(QDialogButtonBox.Ok).setEnabled(True)

        if error_msg:
            QMessageBox.critical(self, "DVID Error", error_msg)
            self._roi_widget.initWithExtents( "", (), (), () )
            return

        self._roi_widget.initWithExtents( voxels_metadata.axiskeys, voxels_metadata.shape,
                                          voxels_metadata.minindex, voxels_metadata.shape )

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

    parser = argparse.ArgumentParser()
    parser.add_argument("--mock-server-hdf5", required=False)
    parser.add_argument("--mode", choices=["select_existing", "specify_new"], default="select_existing")
    parser.add_argument("hostname", metavar="hostname:port")
    
    sys.argv.append("emdata2:8000")

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
