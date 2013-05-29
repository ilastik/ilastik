
# Event Recording
# Started at: 2013-05-28 23:24:04.887372

def playback_events(player):
    import PyQt4.QtCore
    from PyQt4.QtCore import Qt, QEvent, QPoint
    import PyQt4.QtGui
    from ilastik.utility.gui.eventRecorder.objectNameUtils import get_named_object
    from ilastik.utility.gui.eventRecorder.eventRecorder import EventPlayer
    from ilastik.shell.gui.startShellGui import shell    

    player.display_comment("SCRIPT STARTING")


    ########################
    player.display_comment("""New Project (Layer Viewer)""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.startupPage.frame.CreateList.qt_scrollarea_viewport.scrollAreaWidgetContents.child_4_QToolButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(107, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(418, 215), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 2.377995 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.startupPage.frame.CreateList.qt_scrollarea_viewport.scrollAreaWidgetContents.child_4_QToolButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(107, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(418, 215), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 2.439313 )

    obj = get_named_object( 'MainWindow.QFileDialog.buttonBox.child_1_QPushButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(51, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(691, 378), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 4.59387 )

    obj = get_named_object( 'MainWindow.QFileDialog.buttonBox.child_1_QPushButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(51, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(691, 378), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 4.658614 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(268, 2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(586, 157), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 6.867422 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(268, 3), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(586, 158), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 6.964729 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(268, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(586, 166), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 7.029442 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(266, 16), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(584, 180), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 7.033271 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(266, 3), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(584, 181), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 7.409816 )

    ########################
    player.display_comment("""Add raw""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.child_3_DataDetailViewerWidget.appendButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(69, 14), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(389, 157), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 9.01598 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(69, -11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(389, 165), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 9.110818 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(69, -5), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(389, 171), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 9.120365 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(69, 0), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(389, 176), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 9.124688 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(67, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(387, 184), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 9.127564 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(67, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(387, 186), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 9.142158 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(67, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(387, 188), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 9.1594 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(67, 14), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(387, 190), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 9.178722 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(66, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(386, 191), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 9.193026 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(66, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(386, 191), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 9.816962 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2f, Qt.NoModifier, """/""", False, 1), 11.542708 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2f, Qt.NoModifier, """/""", False, 1), 11.623566 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1), 11.685124 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4d, Qt.NoModifier, """m""", False, 1), 11.734508 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1), 11.765164 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4d, Qt.NoModifier, """m""", False, 1), 11.797579 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x50, Qt.NoModifier, """p""", False, 1), 11.846844 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x50, Qt.NoModifier, """p""", False, 1), 11.910537 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2f, Qt.NoModifier, """/""", False, 1), 12.279256 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2f, Qt.NoModifier, """/""", False, 1), 12.341755 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1), 12.56668 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1), 12.629378 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1), 12.662245 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1), 12.679244 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x53, Qt.NoModifier, """s""", False, 1), 12.758689 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1), 12.805506 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x53, Qt.NoModifier, """s""", False, 1), 12.85325 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1), 12.902535 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1), 12.918402 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1), 13.030486 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1), 13.061371 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2d, Qt.NoModifier, """-""", False, 1), 13.093428 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x44, Qt.NoModifier, """d""", False, 1), 13.108882 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x44, Qt.NoModifier, """d""", False, 1), 13.190444 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1), 13.222029 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1), 13.285869 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1), 13.301687 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1), 13.349598 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1), 13.413174 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1), 13.462336 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2f, Qt.NoModifier, """/""", False, 1), 13.462544 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2f, Qt.NoModifier, """/""", False, 1), 13.525479 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x43, Qt.NoModifier, """c""", False, 1), 15.462007 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x55, Qt.NoModifier, """u""", False, 1), 15.542479 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x43, Qt.NoModifier, """c""", False, 1), 15.556728 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x55, Qt.NoModifier, """u""", False, 1), 15.60666 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x42, Qt.NoModifier, """b""", False, 1), 15.702425 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x42, Qt.NoModifier, """b""", False, 1), 15.781486 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1), 15.814516 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1), 15.878187 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1), 16.053245 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1), 16.150853 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x5f, (Qt.ShiftModifier), """_""", False, 1), 16.2627 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1), 16.326409 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4f, Qt.NoModifier, """o""", False, 1), 16.406395 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4f, Qt.NoModifier, """o""", False, 1), 16.469828 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x42, Qt.NoModifier, """b""", False, 1), 16.534669 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x42, Qt.NoModifier, """b""", False, 1), 16.613624 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1), 16.67903 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4a, Qt.NoModifier, """j""", False, 1), 16.699564 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x43, Qt.NoModifier, """c""", False, 1), 16.740411 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1), 16.756878 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4a, Qt.NoModifier, """j""", False, 1), 16.790471 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x43, Qt.NoModifier, """c""", False, 1), 16.805126 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1), 16.885947 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1), 16.966546 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x53, Qt.NoModifier, """s""", False, 1), 16.998417 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x53, Qt.NoModifier, """s""", False, 1), 17.046175 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000003, Qt.NoModifier, """""", False, 1), 17.27047 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000003, Qt.NoModifier, """""", False, 1), 17.317008 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000003, Qt.NoModifier, """""", False, 1), 17.398841 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000003, Qt.NoModifier, """""", False, 1), 17.446135 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000003, Qt.NoModifier, """""", False, 1), 17.526413 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000003, Qt.NoModifier, """""", False, 1), 17.606458 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000003, Qt.NoModifier, """""", False, 1), 17.670366 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000003, Qt.NoModifier, """""", False, 1), 17.7179 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000003, Qt.NoModifier, """""", False, 1), 17.797883 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000003, Qt.NoModifier, """""", False, 1), 17.909971 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4a, Qt.NoModifier, """j""", False, 1), 17.974617 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4a, Qt.NoModifier, """j""", False, 1), 18.037993 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1), 18.053611 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x43, Qt.NoModifier, """c""", False, 1), 18.085258 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1), 18.13367 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x43, Qt.NoModifier, """c""", False, 1), 18.165552 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1), 18.246138 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1), 18.293923 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x53, Qt.NoModifier, """s""", False, 1), 18.854131 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x53, Qt.NoModifier, """s""", False, 1), 18.933161 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1), 19.254196 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1), 19.349705 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x5f, (Qt.ShiftModifier), """_""", False, 1), 19.446336 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1), 19.478226 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x52, Qt.NoModifier, """r""", False, 1), 19.830504 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1), 19.910579 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x52, Qt.NoModifier, """r""", False, 1), 19.94164 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x57, Qt.NoModifier, """w""", False, 1), 19.990001 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1), 20.02147 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x57, Qt.NoModifier, """w""", False, 1), 20.100865 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2e, Qt.NoModifier, """.""", False, 1), 20.325824 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2e, Qt.NoModifier, """.""", False, 1), 20.422359 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4e, Qt.NoModifier, """n""", False, 1), 20.613584 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4e, Qt.NoModifier, """n""", False, 1), 20.741414 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x50, Qt.NoModifier, """p""", False, 1), 20.822102 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x50, Qt.NoModifier, """p""", False, 1), 20.900664 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x59, Qt.NoModifier, """y""", False, 1), 20.998759 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x59, Qt.NoModifier, """y""", False, 1), 21.062036 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000004, Qt.NoModifier, """""", False, 1), 21.573443 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.child_3_DataDetailViewerWidget.appendButton' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000004, Qt.NoModifier, """""", False, 1), 21.760914 )

    ########################
    player.display_comment("""Add (wrong) \"other\" data""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_tabbar' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(122, 21), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(440, 55), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 25.15357 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_tabbar' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(122, 21), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(440, 55), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 25.21885 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.appendButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(78, 23), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(398, 166), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 26.547241 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_1' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(78, -8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(398, 168), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 26.603515 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_1' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(78, -3), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(398, 173), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 26.620327 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_1' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(80, 3), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(400, 179), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 26.639951 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_1' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(80, 3), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(400, 179), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 26.644554 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_1' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(81, 7), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(401, 183), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 26.653118 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_1' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(82, 9), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(402, 185), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 26.670077 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_1' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(82, 9), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(402, 185), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 26.706359 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_1' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(82, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(402, 187), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 26.721267 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_1' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(82, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(402, 187), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 26.90864 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(122, 24), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(334, 87), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 28.689738 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(122, 24), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(334, 87), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 28.786652 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(122, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(334, 73), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 29.660751 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(122, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(334, 73), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 29.834622 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(120, 20), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(332, 83), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 30.073312 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(120, 20), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(332, 83), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 30.156666 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.buttonBox.child_1_QPushButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(29, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(669, 379), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 30.769904 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.buttonBox.child_1_QPushButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(29, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(669, 379), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 30.834935 )

    ########################
    player.display_comment("""Replace \"other\" data""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(68, 17), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(407, 99), (Qt.RightButton), (Qt.RightButton), Qt.NoModifier), 32.993623 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QContextMenuEvent(0, PyQt4.QtCore.QPoint(68, 17), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(407, 99), Qt.NoModifier), 32.99873 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(19, 25), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(407, 99), (Qt.RightButton), Qt.NoButton, Qt.NoModifier), 33.086012 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(20, 25), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(408, 99), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 33.47582 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(22, 29), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(410, 103), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 33.485482 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(25, 33), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(413, 107), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 33.497971 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(28, 36), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(416, 110), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 33.513594 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(28, 37), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(416, 111), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 33.529078 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(28, 38), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(416, 112), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 33.658572 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(28, 38), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(416, 112), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 33.753997 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(122, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(334, 75), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 36.138569 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(122, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(334, 75), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 36.207845 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.buttonBox.child_1_QPushButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(33, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(673, 378), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 37.123366 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.buttonBox.child_1_QPushButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(33, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(673, 378), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 37.187195 )

    ########################
    player.display_comment("""Edit \"other\" --> swap axes""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(91, 14), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(430, 96), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 41.046185 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(91, 14), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(430, 96), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 41.142781 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(91, 14), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(430, 96), (Qt.RightButton), (Qt.RightButton), Qt.NoModifier), 41.201984 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QContextMenuEvent(0, PyQt4.QtCore.QPoint(91, 14), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(430, 96), Qt.NoModifier), 41.207899 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_9_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(19, 25), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(430, 96), (Qt.RightButton), Qt.NoButton, Qt.NoModifier), 41.314213 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_9_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(20, 25), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(431, 96), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 42.037472 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_9_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(21, 27), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(432, 98), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 42.051563 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_9_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(23, 31), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(434, 102), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 42.069254 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_9_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(25, 33), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(436, 104), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 42.087996 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_9_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(25, 35), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(436, 106), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 42.10195 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_9_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(25, 35), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(436, 106), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 42.270916 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_9_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(25, 33), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(436, 104), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 42.290679 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_9_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(25, 28), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(436, 99), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 42.302401 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_9_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(25, 21), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(436, 92), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 42.319612 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_9_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(25, 18), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(436, 89), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 42.33609 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_9_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(25, 16), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(436, 87), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 42.352747 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_9_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(25, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(436, 86), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 42.370296 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_9_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(25, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(436, 86), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 42.481376 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_9_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(25, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(436, 86), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 42.560939 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(40, 9), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(280, 111), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 43.816398 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(39, 9), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(279, 111), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 43.838157 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(36, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(276, 110), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 43.855407 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(32, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(272, 110), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 43.871416 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(22, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(262, 110), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 43.888788 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(9, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(249, 110), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 43.906731 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(-8, 9), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(232, 111), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 43.922316 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(-17, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(223, 112), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 43.937571 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(-27, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(213, 113), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 43.955032 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(-29, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(211, 114), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 43.972143 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(-29, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(211, 114), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 44.000179 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5a, Qt.NoModifier, """z""", False, 1), 44.799015 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x5a, Qt.NoModifier, """z""", False, 1), 44.894953 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x59, Qt.NoModifier, """y""", False, 1), 45.121285 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x58, Qt.NoModifier, """x""", False, 1), 45.150887 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x59, Qt.NoModifier, """y""", False, 1), 45.182098 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x58, Qt.NoModifier, """x""", False, 1), 45.231396 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.okButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(64, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(661, 371), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 47.384329 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.okButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(64, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(661, 371), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 47.458473 )

    ########################
    player.display_comment("""Edit \"other\" again --> Change to \"relative link\"""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(157, 14), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(496, 96), (Qt.RightButton), (Qt.RightButton), Qt.NoModifier), 52.282474 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QContextMenuEvent(0, PyQt4.QtCore.QPoint(157, 14), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(496, 96), Qt.NoModifier), 52.288108 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_10_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(19, 25), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(496, 96), (Qt.RightButton), Qt.NoButton, Qt.NoModifier), 52.408371 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_10_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(19, 26), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(496, 97), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 52.76648 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_10_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(22, 30), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(499, 101), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 52.788434 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_10_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(24, 34), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(501, 105), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 52.797177 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_10_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(27, 38), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(504, 109), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 52.814735 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_10_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(30, 40), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(507, 111), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 52.830413 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_10_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(30, 40), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(507, 111), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 53.347942 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_10_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(30, 38), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(507, 109), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 53.363532 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_10_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(30, 27), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(507, 98), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 53.381345 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_10_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(30, 16), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(507, 87), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 53.398686 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_10_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(30, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(507, 82), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 53.408964 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_10_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(30, 9), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(507, 80), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 53.418886 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_10_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(30, 7), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(507, 78), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 53.454256 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_10_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(30, 6), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(507, 77), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 53.648132 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_10_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(30, 6), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(507, 77), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 53.719374 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.child_7_DatasetInfoEditorWidget.widget.storageComboBox' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(148, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(388, 197), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 55.823723 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.child_7_DatasetInfoEditorWidget.widget.storageComboBox.child_1_QFrame' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(148, -12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(388, 197), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 55.911984 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.child_7_DatasetInfoEditorWidget.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(146, 4), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(388, 215), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 56.224901 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.child_7_DatasetInfoEditorWidget.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(146, 7), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(388, 218), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 56.242307 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.child_7_DatasetInfoEditorWidget.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(146, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(388, 222), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 56.484435 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.child_7_DatasetInfoEditorWidget.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(146, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(388, 226), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 56.496631 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.child_7_DatasetInfoEditorWidget.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(146, 19), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(388, 230), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 56.508543 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.child_7_DatasetInfoEditorWidget.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(145, 23), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(387, 234), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 56.533193 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.child_7_DatasetInfoEditorWidget.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(144, 26), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(386, 237), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 56.541867 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.child_7_DatasetInfoEditorWidget.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(144, 28), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(386, 239), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 56.564002 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.child_7_DatasetInfoEditorWidget.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(143, 32), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(385, 243), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 56.572875 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.child_7_DatasetInfoEditorWidget.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(142, 35), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(384, 246), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 56.597211 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.child_7_DatasetInfoEditorWidget.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(142, 37), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(384, 248), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 56.607648 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.child_7_DatasetInfoEditorWidget.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(141, 38), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(383, 249), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 56.636475 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.child_7_DatasetInfoEditorWidget.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(139, 38), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(381, 249), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 56.71233 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.child_7_DatasetInfoEditorWidget.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(139, 39), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(381, 250), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 56.728887 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.child_7_DatasetInfoEditorWidget.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(139, 39), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(381, 250), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 56.866719 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.child_7_DatasetInfoEditorWidget.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(139, 39), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(381, 250), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 56.936249 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.child_7_DatasetInfoEditorWidget.widget.okButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(52, 5), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(649, 366), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 57.799834 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.child_7_DatasetInfoEditorWidget.widget.okButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(52, 5), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(649, 366), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 58.009024 )

    ########################
    player.display_comment("""Edit \"raw\" properties --> Copy to project""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_tabbar' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(38, 3), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(356, 37), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 60.544473 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_tabbar' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(37, 3), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(355, 37), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 60.65201 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_tabbar' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(37, 3), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(355, 37), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 60.656314 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.child_3_DataDetailViewerWidget.datasetDetailTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(46, 22), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(385, 104), (Qt.RightButton), (Qt.RightButton), Qt.NoModifier), 61.436572 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.child_3_DataDetailViewerWidget.datasetDetailTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QContextMenuEvent(0, PyQt4.QtCore.QPoint(46, 22), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(385, 104), Qt.NoModifier), 61.443978 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.child_3_DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(19, 25), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(385, 104), (Qt.RightButton), Qt.NoButton, Qt.NoModifier), 61.507233 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.child_3_DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(20, 25), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(386, 104), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 61.605058 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.child_3_DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(21, 25), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(387, 104), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 61.707367 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.child_3_DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(22, 24), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(388, 103), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 61.733902 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.child_3_DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(23, 24), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(389, 103), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 61.741841 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.child_3_DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(24, 24), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(390, 103), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 61.754975 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.child_3_DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(25, 24), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(391, 103), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 61.771742 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.child_3_DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(26, 24), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(392, 103), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 61.788836 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.child_3_DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(27, 24), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(393, 103), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 61.805278 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.child_3_DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(29, 24), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(395, 103), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 61.82646 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.child_3_DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(30, 24), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(396, 103), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 61.97675 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.child_3_DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(30, 23), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(396, 102), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 61.989676 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.child_3_DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(31, 21), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(397, 100), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 62.020875 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.child_3_DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(31, 21), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(397, 100), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 62.032919 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.child_3_DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(32, 20), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(398, 99), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 62.0517 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.child_3_DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(32, 18), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(398, 97), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 62.064483 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.child_3_DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(32, 18), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(398, 97), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 62.193711 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.child_3_DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(32, 18), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(398, 97), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 62.259281 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.widget.storageComboBox' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(139, 9), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(379, 198), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 64.132586 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.widget.storageComboBox.child_1_QFrame' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(139, -11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(379, 198), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 64.195166 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(137, 4), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(379, 215), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 64.563644 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(137, 4), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(379, 215), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 64.574077 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(136, 14), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(378, 225), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 64.589635 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(135, 13), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(377, 224), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 64.68383 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(135, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(377, 223), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 64.764088 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(135, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(377, 222), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 64.780093 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(135, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(377, 222), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 64.796372 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(135, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(377, 221), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 64.814515 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(135, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(377, 221), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 64.941101 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(135, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(377, 221), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 65.02725 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.widget.okButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(41, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(638, 371), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 65.908414 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.widget.okButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(41, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(638, 371), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 66.017584 )

    ########################
    player.display_comment("""View Summary tab""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_tabbar' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(199, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(517, 42), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 77.742992 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_tabbar' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(199, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(517, 42), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 77.837696 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.fileInfoTabWidgetPage1.laneSummaryTableView.child_5_QHeaderView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(198, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(537, 67), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 79.837708 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.fileInfoTabWidgetPage1.laneSummaryTableView.child_5_QHeaderView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(199, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(538, 67), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 79.912675 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.fileInfoTabWidgetPage1.laneSummaryTableView.child_5_QHeaderView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(200, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(539, 67), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 79.917859 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.fileInfoTabWidgetPage1.laneSummaryTableView.child_5_QHeaderView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(205, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(544, 67), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 79.928132 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.fileInfoTabWidgetPage1.laneSummaryTableView.child_5_QHeaderView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(218, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(557, 67), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 79.940991 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.fileInfoTabWidgetPage1.laneSummaryTableView.child_5_QHeaderView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(238, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(577, 67), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 79.956041 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.fileInfoTabWidgetPage1.laneSummaryTableView.child_5_QHeaderView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(258, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(597, 67), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 79.970601 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.fileInfoTabWidgetPage1.laneSummaryTableView.child_5_QHeaderView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(285, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(624, 70), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 79.986508 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.fileInfoTabWidgetPage1.laneSummaryTableView.child_5_QHeaderView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(303, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(642, 70), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 80.010005 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.fileInfoTabWidgetPage1.laneSummaryTableView.child_5_QHeaderView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(315, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(654, 71), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 80.024848 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.fileInfoTabWidgetPage1.laneSummaryTableView.child_5_QHeaderView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(322, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(661, 71), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 80.036877 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.fileInfoTabWidgetPage1.laneSummaryTableView.child_5_QHeaderView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(325, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(664, 71), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 80.07092 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.fileInfoTabWidgetPage1.laneSummaryTableView.child_5_QHeaderView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(325, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(664, 71), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 80.419656 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.fileInfoTabWidgetPage1.laneSummaryTableView.child_5_QHeaderView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(99, 6), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(438, 65), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 81.308265 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.fileInfoTabWidgetPage1.laneSummaryTableView.child_5_QHeaderView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(102, 6), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(441, 65), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 81.392606 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.fileInfoTabWidgetPage1.laneSummaryTableView.child_5_QHeaderView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(105, 7), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(444, 66), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 81.408683 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.fileInfoTabWidgetPage1.laneSummaryTableView.child_5_QHeaderView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(119, 9), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(458, 68), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 81.42447 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.fileInfoTabWidgetPage1.laneSummaryTableView.child_5_QHeaderView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(134, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(473, 69), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 81.441432 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.fileInfoTabWidgetPage1.laneSummaryTableView.child_5_QHeaderView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(161, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(500, 69), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 81.463125 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.fileInfoTabWidgetPage1.laneSummaryTableView.child_5_QHeaderView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(178, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(517, 69), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 81.477983 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.fileInfoTabWidgetPage1.laneSummaryTableView.child_5_QHeaderView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(183, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(522, 69), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 81.491502 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.fileInfoTabWidgetPage1.laneSummaryTableView.child_5_QHeaderView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(184, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(523, 69), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 81.826702 )

    ########################
    player.display_comment("""Save project""")
    ########################

    obj = get_named_object( 'MainWindow.child_7_QMenuBar' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(24, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(24, 11), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 48.839549 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(24, -5), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(24, 11), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 48.892886 )

    obj = get_named_object( 'MainWindow.child_7_QMenuBar' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(24, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(25, 19), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 49.286497 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(25, 3), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(25, 19), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 49.295966 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(27, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(27, 24), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 49.302607 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(28, 14), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(28, 30), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 49.317017 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(31, 23), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(31, 39), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 49.326071 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(32, 30), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(32, 46), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 49.347754 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(34, 34), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(34, 50), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 49.357907 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(34, 38), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(34, 54), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 49.386116 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(34, 41), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(34, 57), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 49.39559 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(34, 43), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(34, 59), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 49.409421 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(34, 44), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(34, 60), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 49.424628 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(34, 45), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(34, 61), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 49.448217 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(34, 46), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(34, 62), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 49.527814 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(34, 47), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(34, 63), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 49.542932 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(34, 47), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(34, 63), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 49.69123 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(34, 47), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(34, 63), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 49.738475 )


    player.display_comment("SCRIPT COMPLETE")
