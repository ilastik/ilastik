import socket
import logging

import numpy
from PyQt4.QtCore import Qt, QEvent
from PyQt4.QtGui import QVBoxLayout, QGroupBox, QSizePolicy, QMessageBox, QDialogButtonBox, QMouseEvent

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
        group_title = "Restrict to subvolume (Right-click a volume name above to auto-initialize these subvolume parameters.)"
        subvol_groupbox = QGroupBox(group_title, parent=self)
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

        # Special right-click behavior.
        self._repo_treewidget.viewport().installEventFilter(self)

    def get_subvolume_roi(self):
        if self._subvol_groupbox.isChecked():
            return self._subvol_widget.roi
        return None

    def eventFilter(self, widget, event):
        """
        If the user right-clicks on a volume/roi name, it triggers special behavior:
        The subvolume widget is automatically initialized with extents matching the
        right-clicked volume, regardless of the currently selected volume.
        """
        if widget is self._repo_treewidget.viewport() \
        and event.type() == QEvent.MouseButtonPress \
        and event.button() == Qt.RightButton:
            item = self._repo_treewidget.itemAt(event.pos())
            repo_uuid, dataname, typename = item.data(0, Qt.UserRole).toPyObject()
            is_roi = (typename == 'roi')
            is_voxels = (typename in ['labelblk', 'uint8blk'])
            if (is_voxels or is_roi) \
            and self._buttonbox.button(QDialogButtonBox.Ok).isEnabled():
                self._update_subvol_widget(repo_uuid, dataname, typename) # FIXME: we're passing the repo id instead of the node id. is that okay?
                self._subvol_groupbox.setChecked(True)
                return True
        return super(DvidDataSelectionBrowser, self).eventFilter(widget, event)

    def _update_status(self):
        super( DvidDataSelectionBrowser, self )._update_status()
        hostname, dset_uuid, dataname, node_uuid, typename = self.get_selection()

        enable_contents = self._repos_info is not None and dataname != "" and node_uuid != ""
        self._subvol_groupbox.setEnabled(enable_contents)

        if not dataname or not node_uuid:
            self._subvol_widget.initWithExtents( "", (), (), () )
            return
        
        self._update_subvol_widget(node_uuid, dataname, typename)
    
    def _update_subvol_widget(self, node_uuid, dataname, typename):
        """
        Update the subvolume widget with the min/max extents of the given node and dataname.
        Note: The node and dataname do not necessarily have to match the currently 
              selected node and dataname.
              This enables the right-click behavior, which can be used to  
              limit your data volume to the size of a different data volume.
        """
        error_msg = None
        try:
            if typename == "roi":
                node_service = DVIDNodeService(self._hostname, str(node_uuid))
                roi_blocks_zyx = numpy.array( node_service.get_roi(str(dataname)) )
                maxindex = tuple( DVID_BLOCK_WIDTH*(1 + numpy.max( roi_blocks_zyx, axis=0 )) )
                minindex = (0,0,0) # Rois are always 3D
                axiskeys = "zyx"
                # If the current selection is a dataset, then include a channel dimension
                if self.get_selection().typename != "roi":
                    axiskeys = "zyxc"
                    minindex = minindex + (0,)
                    maxindex = maxindex + (1,) # FIXME: This assumes that the selected data has only 1 channel...
            else:
                # Query the server
                raw_metadata = VoxelsAccessor.get_metadata( self._hostname, node_uuid, dataname )
                voxels_metadata = VoxelsMetadata( raw_metadata )
                maxindex = voxels_metadata.shape
                minindex = voxels_metadata.minindex
                axiskeys = voxels_metadata.axiskeys
                # If the current selection is a roi, then remove the channel dimension
                if self.get_selection().typename == "roi":
                    axiskeys = "zyx"
                    minindex = minindex[:-1]
                    maxindex = maxindex[:-1]
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
                                       default_nodes={ "localhost:8000" : '57c4c6a0740d4509a02da6b9453204cb'},
                                       mode="select_existing")

    if browser.exec_() == DvidDataSelectionBrowser.Accepted:
        print "The dialog was accepted with result: ", browser.get_selection()
        print "And subvolume: ", browser.get_subvolume_roi()
    else:
        print "The dialog was rejected."
