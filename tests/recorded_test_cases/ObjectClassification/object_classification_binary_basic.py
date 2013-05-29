
# Event Recording
# Started at: 2013-05-29 02:43:21.765877

def playback_events(player):
    import PyQt4.QtCore
    from PyQt4.QtCore import Qt, QEvent, QPoint
    import PyQt4.QtGui
    from ilastik.utility.gui.eventRecorder.objectNameUtils import get_named_object
    from ilastik.utility.gui.eventRecorder.eventRecorder import EventPlayer
    from ilastik.shell.gui.startShellGui import shell    

    player.display_comment("SCRIPT STARTING")


    ########################
    player.display_comment("""New Project (Object Classification from binary)""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.startupPage.frame.CreateList.qt_scrollarea_viewport.scrollAreaWidgetContents.child_7_QToolButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(80, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(391, 290), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 1.422522 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.startupPage.frame.CreateList.qt_scrollarea_viewport.scrollAreaWidgetContents.child_7_QToolButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(80, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(391, 290), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 1.500228 )

    obj = get_named_object( 'MainWindow.QFileDialog.buttonBox.child_1_QPushButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(22, 14), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(654, 381), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 3.615232 )

    obj = get_named_object( 'MainWindow.QFileDialog.buttonBox.child_1_QPushButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(22, 14), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(654, 381), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 3.716598 )

    ########################
    player.display_comment("""Add raw/binary data""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.child_3_DataDetailViewerWidget.appendButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(60, 19), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(380, 135), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 8.263396 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(60, -8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(380, 135), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 8.326874 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(60, 0), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(380, 143), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 8.713374 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(60, 0), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(380, 143), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 8.719854 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(59, 4), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(379, 147), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 8.727418 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(59, 5), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(379, 148), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 8.744929 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(59, 6), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(379, 149), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 8.780838 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(58, 7), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(378, 150), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 8.829868 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(58, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(378, 151), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 8.842676 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(58, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(378, 151), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 8.927628 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(58, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(378, 151), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 8.988454 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2f, Qt.NoModifier, """/""", False, 1), 10.033076 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2f, Qt.NoModifier, """/""", False, 1), 10.111516 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1), 10.769048 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4d, Qt.NoModifier, """m""", False, 1), 10.815967 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1), 10.864806 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4d, Qt.NoModifier, """m""", False, 1), 10.90469 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x50, Qt.NoModifier, """p""", False, 1), 10.920589 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x50, Qt.NoModifier, """p""", False, 1), 11.000552 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2f, Qt.NoModifier, """/""", False, 1), 11.160765 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2f, Qt.NoModifier, """/""", False, 1), 11.231503 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1), 11.760286 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1), 11.840652 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1), 11.887877 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1), 11.896802 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x53, Qt.NoModifier, """s""", False, 1), 11.984698 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1), 12.048221 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x53, Qt.NoModifier, """s""", False, 1), 12.079812 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1), 12.127434 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1), 12.169496 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1), 12.336556 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1), 12.41606 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2d, Qt.NoModifier, """-""", False, 1), 12.440259 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x44, Qt.NoModifier, """d""", False, 1), 12.520439 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x44, Qt.NoModifier, """d""", False, 1), 12.592092 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1), 12.624365 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1), 12.680676 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1), 12.696353 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1), 12.769432 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1), 12.792467 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1), 12.840481 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2f, Qt.NoModifier, """/""", False, 1), 13.215749 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2f, Qt.NoModifier, """/""", False, 1), 13.279836 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x43, Qt.NoModifier, """c""", False, 1), 16.160043 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x55, Qt.NoModifier, """u""", False, 1), 16.273236 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x43, Qt.NoModifier, """c""", False, 1), 16.295917 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x55, Qt.NoModifier, """u""", False, 1), 16.312747 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x42, Qt.NoModifier, """b""", False, 1), 16.424972 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x42, Qt.NoModifier, """b""", False, 1), 16.496828 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1), 16.520454 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1), 16.585752 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1), 16.721475 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1), 16.841367 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x5f, (Qt.ShiftModifier), """_""", False, 1), 16.960352 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1), 17.01692 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4f, Qt.NoModifier, """o""", False, 1), 17.168237 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4f, Qt.NoModifier, """o""", False, 1), 17.263933 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x42, Qt.NoModifier, """b""", False, 1), 17.337146 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x42, Qt.NoModifier, """b""", False, 1), 17.401019 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4a, Qt.NoModifier, """j""", False, 1), 17.489389 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1), 17.502803 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1), 17.593106 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4a, Qt.NoModifier, """j""", False, 1), 17.608859 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1), 17.736173 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1), 17.816619 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x53, Qt.NoModifier, """s""", False, 1), 17.936854 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x53, Qt.NoModifier, """s""", False, 1), 17.99327 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000003, Qt.NoModifier, """""", False, 1), 18.273042 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000003, Qt.NoModifier, """""", False, 1), 18.319986 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000003, Qt.NoModifier, """""", False, 1), 18.393059 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000003, Qt.NoModifier, """""", False, 1), 18.472543 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x43, Qt.NoModifier, """c""", False, 1), 18.505349 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x43, Qt.NoModifier, """c""", False, 1), 18.567946 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1), 18.623776 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1), 18.71302 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x53, Qt.NoModifier, """s""", False, 1), 18.800918 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x53, Qt.NoModifier, """s""", False, 1), 18.864466 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1), 20.13621 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1), 20.248555 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x5f, (Qt.ShiftModifier), """_""", False, 1), 20.31298 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1), 20.351859 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x52, Qt.NoModifier, """r""", False, 1), 20.44811 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1), 20.51931 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x52, Qt.NoModifier, """r""", False, 1), 20.575267 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x57, Qt.NoModifier, """w""", False, 1), 20.615697 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1), 20.65619 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x57, Qt.NoModifier, """w""", False, 1), 20.704537 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2e, Qt.NoModifier, """.""", False, 1), 21.200145 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2e, Qt.NoModifier, """.""", False, 1), 21.304725 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4e, Qt.NoModifier, """n""", False, 1), 21.51306 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4e, Qt.NoModifier, """n""", False, 1), 21.567178 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x50, Qt.NoModifier, """p""", False, 1), 21.665414 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x50, Qt.NoModifier, """p""", False, 1), 21.736207 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x59, Qt.NoModifier, """y""", False, 1), 21.824723 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x59, Qt.NoModifier, """y""", False, 1), 21.878644 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000004, Qt.NoModifier, """""", False, 1), 22.312631 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.child_3_DataDetailViewerWidget.appendButton' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000004, Qt.NoModifier, """""", False, 1), 22.608673 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_tabbar' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(125, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(443, 43), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 23.978884 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_tabbar' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(125, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(443, 43), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 24.056219 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.appendButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(53, 17), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(373, 133), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 24.681698 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_1' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(53, -6), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(373, 137), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 25.022115 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_1' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(53, -3), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(373, 140), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 25.037885 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_1' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(53, 2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(373, 145), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 25.056253 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_1' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(53, 2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(373, 145), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 25.060913 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_1' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(53, 5), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(373, 148), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 25.071795 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_1' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(53, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(373, 151), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 25.087561 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_1' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(53, 9), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(373, 152), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 25.104341 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_1' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(53, 9), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(373, 152), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 25.333271 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2f, Qt.NoModifier, """/""", False, 1), 26.863448 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2f, Qt.NoModifier, """/""", False, 1), 26.952339 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1), 27.199202 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4d, Qt.NoModifier, """m""", False, 1), 27.239676 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4d, Qt.NoModifier, """m""", False, 1), 27.287742 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1), 27.294663 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x50, Qt.NoModifier, """p""", False, 1), 27.37667 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x50, Qt.NoModifier, """p""", False, 1), 27.415473 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2f, Qt.NoModifier, """/""", False, 1), 27.576558 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2f, Qt.NoModifier, """/""", False, 1), 27.662938 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1), 27.895466 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1), 27.968008 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1), 28.00684 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1), 28.014865 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x53, Qt.NoModifier, """s""", False, 1), 28.102461 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1), 28.159031 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x53, Qt.NoModifier, """s""", False, 1), 28.192418 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1), 28.247988 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1), 28.271337 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1), 28.407498 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1), 28.463287 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2d, Qt.NoModifier, """-""", False, 1), 28.4801 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x44, Qt.NoModifier, """d""", False, 1), 28.526732 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x44, Qt.NoModifier, """d""", False, 1), 28.623254 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1), 28.639805 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1), 28.702853 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1), 28.710282 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1), 28.77651 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1), 28.807658 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1), 28.864193 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2f, Qt.NoModifier, """/""", False, 1), 28.903509 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2f, Qt.NoModifier, """/""", False, 1), 28.998765 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x43, Qt.NoModifier, """c""", False, 1), 29.447123 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x55, Qt.NoModifier, """u""", False, 1), 29.543943 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x43, Qt.NoModifier, """c""", False, 1), 29.574998 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x55, Qt.NoModifier, """u""", False, 1), 29.590788 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x42, Qt.NoModifier, """b""", False, 1), 29.688554 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x42, Qt.NoModifier, """b""", False, 1), 29.751329 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1), 29.751447 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1), 29.815181 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1), 29.967164 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1), 30.071995 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x5f, (Qt.ShiftModifier), """_""", False, 1), 30.168047 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1), 30.207662 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4f, Qt.NoModifier, """o""", False, 1), 30.30421 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4f, Qt.NoModifier, """o""", False, 1), 30.383638 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x42, Qt.NoModifier, """b""", False, 1), 30.463528 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x42, Qt.NoModifier, """b""", False, 1), 30.51907 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4a, Qt.NoModifier, """j""", False, 1), 30.59916 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1), 30.647314 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x43, Qt.NoModifier, """c""", False, 1), 30.688004 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1), 30.718666 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4a, Qt.NoModifier, """j""", False, 1), 30.719159 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x43, Qt.NoModifier, """c""", False, 1), 30.768203 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1), 30.831916 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x53, Qt.NoModifier, """s""", False, 1), 30.927499 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1), 30.934728 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x53, Qt.NoModifier, """s""", False, 1), 31.007812 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2f, Qt.NoModifier, """/""", False, 1), 31.126743 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2f, Qt.NoModifier, """/""", False, 1), 31.192817 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000003, Qt.NoModifier, """""", False, 1), 31.583194 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000003, Qt.NoModifier, """""", False, 1), 31.63348 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1), 31.663624 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1), 31.743117 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1), 31.823099 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2d, Qt.NoModifier, """-""", False, 1), 31.832714 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x42, Qt.NoModifier, """b""", False, 1), 32.390789 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x42, Qt.NoModifier, """b""", False, 1), 32.456121 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x49, Qt.NoModifier, """i""", False, 1), 32.520246 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4e, Qt.NoModifier, """n""", False, 1), 32.575228 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x49, Qt.NoModifier, """i""", False, 1), 32.62263 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4e, Qt.NoModifier, """n""", False, 1), 32.664391 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1), 32.680321 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x52, Qt.NoModifier, """r""", False, 1), 32.768194 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1), 32.790936 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x52, Qt.NoModifier, """r""", False, 1), 32.839461 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x59, Qt.NoModifier, """y""", False, 1), 32.846696 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x59, Qt.NoModifier, """y""", False, 1), 32.934694 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2e, Qt.NoModifier, """.""", False, 1), 33.134708 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2e, Qt.NoModifier, """.""", False, 1), 33.2472 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4e, Qt.NoModifier, """n""", False, 1), 33.392479 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4e, Qt.NoModifier, """n""", False, 1), 33.454744 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x50, Qt.NoModifier, """p""", False, 1), 33.535061 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x50, Qt.NoModifier, """p""", False, 1), 33.607644 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x59, Qt.NoModifier, """y""", False, 1), 33.680874 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x59, Qt.NoModifier, """y""", False, 1), 33.734184 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000004, Qt.NoModifier, """""", False, 1), 34.376785 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.appendButton' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000004, Qt.NoModifier, """""", False, 1), 34.586597 )

    ########################
    player.display_comment("""Object Extraction: Select Features
""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(67, 44), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(74, 68), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 40.330897 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(67, 44), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(74, 68), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 40.411344 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.containingWidget.selectFeaturesButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(170, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(216, 84), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 42.848233 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.containingWidget.selectFeaturesButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(170, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(216, 84), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 42.990501 )

    obj = get_named_object( 'FeatureSelectionDialog.widget.treeWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(52, 179), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(84, 231), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 45.325622 )

    obj = get_named_object( 'FeatureSelectionDialog.widget.treeWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(52, 179), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(84, 231), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 45.403819 )

    obj = get_named_object( 'FeatureSelectionDialog.widget.treeWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(50, 269), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(82, 321), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 46.852262 )

    obj = get_named_object( 'FeatureSelectionDialog.widget.treeWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(51, 269), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(83, 321), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 46.859095 )

    obj = get_named_object( 'FeatureSelectionDialog.widget.treeWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(51, 269), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(83, 321), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 46.956641 )

    obj = get_named_object( 'FeatureSelectionDialog.widget.buttonBox.child_1_QPushButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(28, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(384, 461), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 47.996871 )

    obj = get_named_object( 'FeatureSelectionDialog.widget.buttonBox.child_1_QPushButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(28, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(384, 461), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 48.086511 )

    ########################
    player.display_comment("""Object Classification.....""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(86, 82), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(93, 106), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 51.899236 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(86, 82), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(93, 106), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 51.977248 )

    ########################
    player.display_comment("""Subset Features""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.subsetFeaturesButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(85, 16), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(131, 97), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 55.696421 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.subsetFeaturesButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(85, 16), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(131, 97), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 55.78157 )

    obj = get_named_object( 'FeatureSubSelectionDialog.widget.treeWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(50, 18), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(82, 70), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 56.680008 )

    obj = get_named_object( 'FeatureSubSelectionDialog.widget.treeWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(50, 19), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(82, 71), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 56.737788 )

    obj = get_named_object( 'FeatureSubSelectionDialog.widget.treeWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(50, 19), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(82, 71), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 56.749918 )

    obj = get_named_object( 'FeatureSubSelectionDialog.widget.treeWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(53, 37), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(85, 89), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 56.913043 )

    obj = get_named_object( 'FeatureSubSelectionDialog.widget.treeWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(53, 37), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(85, 89), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 56.992843 )

    obj = get_named_object( 'FeatureSubSelectionDialog.widget.buttonBox.child_1_QPushButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(18, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(374, 457), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 57.781239 )

    obj = get_named_object( 'FeatureSubSelectionDialog.widget.buttonBox.child_1_QPushButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(18, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(374, 457), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 57.868777 )

    ########################
    player.display_comment("""Add Label Classes....""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.AddLabelButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(64, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(110, 230), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 60.086393 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.AddLabelButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(64, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(110, 230), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 60.181716 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.AddLabelButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(186, 18), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(232, 237), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 62.002594 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.AddLabelButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(186, 18), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(232, 237), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 62.11196 )

    ########################
    player.display_comment("""Hide \"Object\" Layer""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(154, 3), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(159, 474), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 71.056991 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(154, 1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(159, 472), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 71.23837 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(154, 2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(159, 471), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 71.288409 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(154, -3), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(159, 465), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 71.296274 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(154, -1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(159, 461), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 71.304636 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(154, 1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(159, 459), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 71.34554 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(154, -1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(159, 455), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 71.354163 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(154, 0), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(159, 452), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 71.395332 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(154, -1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(159, 448), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 71.403774 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(154, 1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(159, 446), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 71.448512 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(154, -1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(159, 442), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 71.461481 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(154, 2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(159, 441), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 71.470323 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(154, 1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(159, 439), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 71.512954 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(153, 0), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(158, 436), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 71.5204 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(152, 1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(157, 434), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 71.56468 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(151, -1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(156, 430), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 71.572741 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(151, 1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(156, 428), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 71.612638 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(150, 0), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(155, 425), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 71.621743 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(150, 0), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(155, 422), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 71.676285 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(149, 2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(154, 421), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 71.716277 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(149, 2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(154, 420), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 71.72467 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(148, 1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(153, 418), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 71.768331 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(148, 2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(153, 417), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 71.775682 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(148, 2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(153, 416), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 71.818643 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(148, 1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(153, 414), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 71.825746 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(148, 2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(153, 413), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 71.844304 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(147, 2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(152, 412), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 71.884195 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(147, 1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(152, 410), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 71.892586 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(146, 1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(151, 408), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 71.93652 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(146, 0), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(151, 405), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 71.944686 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(146, 1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(151, 403), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 71.954042 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(145, 1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(150, 401), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 71.997011 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(145, 2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(150, 400), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 72.005229 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(145, 1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(150, 398), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 72.056899 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(145, 1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(150, 396), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 72.065993 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(145, 2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(150, 395), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 72.074123 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(145, 2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(150, 394), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 72.121205 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(145, 0), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(150, 391), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 72.130676 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(145, 1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(150, 389), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 72.137046 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(145, 2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(150, 388), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 72.187106 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(145, 3), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(150, 388), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 72.435213 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_3_lane_0.layerWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(11, 56), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(18, 447), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 74.836195 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_3_lane_0.layerWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(11, 56), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(18, 447), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 75.023036 )

    ########################
    player.display_comment("""Label two objects""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_3_lane_0.layerWidget' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000021, (Qt.ControlModifier), """""", False, 1), 83.221653 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_3_lane_0.layerWidget' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000021, Qt.NoModifier, """""", False, 1), 84.35071 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_3_lane_0.layerWidget' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000022, (Qt.MetaModifier), """""", False, 1), 84.661959 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_3_lane_0.layerWidget' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000022, Qt.NoModifier, """""", False, 1), 85.149392 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_3_lane_0.layerWidget' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000021, (Qt.ControlModifier), """""", False, 1), 85.70111 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(122, 144), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(433, 168), 120, Qt.NoButton, (Qt.ControlModifier), 2), 86.086272 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(122, 144), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(433, 168), 120, Qt.NoButton, (Qt.ControlModifier), 2), 86.132137 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(122, 144), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(433, 168), 120, Qt.NoButton, (Qt.ControlModifier), 2), 86.484122 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(122, 144), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(433, 168), 120, Qt.NoButton, (Qt.ControlModifier), 2), 86.530249 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(122, 144), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(433, 168), 120, Qt.NoButton, (Qt.ControlModifier), 2), 86.572303 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(122, 144), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(433, 168), 120, Qt.NoButton, (Qt.ControlModifier), 2), 86.840363 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(122, 144), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(433, 168), 120, Qt.NoButton, (Qt.ControlModifier), 2), 86.881249 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(122, 144), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(433, 168), 360, Qt.NoButton, (Qt.ControlModifier), 2), 86.895397 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(122, 144), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(433, 168), 360, Qt.NoButton, (Qt.ControlModifier), 2), 86.939567 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(122, 144), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(433, 168), 360, Qt.NoButton, (Qt.ControlModifier), 2), 87.188343 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(122, 144), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(433, 168), 240, Qt.NoButton, (Qt.ControlModifier), 2), 87.22828 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(122, 144), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(433, 168), 360, Qt.NoButton, (Qt.ControlModifier), 2), 87.241101 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(122, 144), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(433, 168), 600, Qt.NoButton, (Qt.ControlModifier), 2), 87.280345 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(122, 144), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(433, 168), 480, Qt.NoButton, (Qt.ControlModifier), 2), 87.29582 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(122, 144), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(433, 168), 480, Qt.NoButton, (Qt.ControlModifier), 2), 87.338707 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(122, 144), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(433, 168), -120, Qt.NoButton, (Qt.ControlModifier), 2), 87.953842 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(122, 144), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(433, 168), -240, Qt.NoButton, (Qt.ControlModifier), 2), 88.002546 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(122, 144), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(433, 168), -240, Qt.NoButton, (Qt.ControlModifier), 2), 88.055784 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(122, 144), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(433, 168), 120, Qt.NoButton, (Qt.ControlModifier), 2), 88.962725 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(122, 144), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(433, 168), 120, Qt.NoButton, (Qt.ControlModifier), 2), 89.012147 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(122, 144), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(433, 168), 360, Qt.NoButton, (Qt.ControlModifier), 2), 89.056153 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(122, 144), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(433, 168), 240, Qt.NoButton, (Qt.ControlModifier), 2), 89.110828 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(122, 144), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(433, 168), 360, Qt.NoButton, (Qt.ControlModifier), 2), 89.182597 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(122, 144), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(433, 168), 240, Qt.NoButton, (Qt.ControlModifier), 2), 89.231461 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(121, 143), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(432, 167), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 90.160769 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(116, 142), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(427, 166), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 90.178214 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(112, 143), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(423, 167), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 90.204593 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(103, 143), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(414, 167), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 90.2172 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(82, 136), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(393, 160), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 90.230826 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(49, 126), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(360, 150), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 90.243568 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_3_lane_0.layerWidget' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000021, Qt.NoModifier, """""", False, 1), 90.255714 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.child_2_QTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(105, 9), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(153, 133), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 90.750265 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.child_2_QTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(105, 9), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(153, 133), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 90.814874 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(60, 56), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(371, 80), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 91.860056 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(60, 56), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(371, 80), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 92.214497 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.child_2_QTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(69, 42), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(117, 166), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 93.171423 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.child_2_QTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(69, 42), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(117, 166), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 93.233316 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(168, 58), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(479, 82), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 94.570216 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(168, 58), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(479, 82), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 94.897409 )

    ########################
    player.display_comment("""Live Update""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.checkInteractive' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(38, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(84, 256), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 98.833402 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.checkInteractive' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(38, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(84, 256), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 98.93763 )

    ########################
    player.display_comment("""Save Project""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.checkInteractive' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000021, (Qt.ControlModifier), """""", False, 1), 104.218849 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.checkInteractive' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x53, (Qt.ControlModifier), """""", False, 1), 104.56203 )

    obj = get_named_object( 'MainWindow' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x53, (Qt.ControlModifier), """""", False, 1), 104.973882 )

    obj = get_named_object( 'MainWindow' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000021, Qt.NoModifier, """""", False, 1), 104.974229 )

    player.display_comment("SCRIPT COMPLETE")
