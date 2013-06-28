
# Event Recording
# Started at: 2013-06-25 18:37:24.238816

def playback_events(player):
    import PyQt4.QtCore
    from PyQt4.QtCore import Qt, QEvent, QPoint
    import PyQt4.QtGui
    from ilastik.utility.gui.eventRecorder.objectNameUtils import get_named_object
    from ilastik.utility.gui.eventRecorder.eventRecorder import EventPlayer
    from ilastik.shell.gui.startShellGui import shell    

    player.display_comment("SCRIPT STARTING")


    ########################
    player.display_comment("""New Project (Object Classification - binary)""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.startupPage.frame.CreateList.qt_scrollarea_viewport.scrollAreaWidgetContents.child_8_QToolButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(171, 3), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(482, 364), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 5.529566 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.startupPage.frame.CreateList.qt_scrollarea_viewport.scrollAreaWidgetContents.child_8_QToolButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(171, 3), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(482, 364), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 5.993592 )

    obj = get_named_object( 'MainWindow.QFileDialog.fileNameEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000004, Qt.NoModifier, """""", False, 1), 7.662337 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_4_QScrollArea' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000004, Qt.NoModifier, """""", False, 1), 8.039033 )

    ########################
    player.display_comment("""Add data (raw and binary)""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.appendButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(67, 25), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(387, 145), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 9.945773 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(68, -5), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(388, 148), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 10.20563 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(69, -2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(389, 151), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 10.212432 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(70, 0), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(390, 153), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 10.219185 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(70, 0), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(390, 153), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 10.224273 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(71, 3), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(391, 156), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 10.22903 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(72, 5), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(392, 158), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 10.241088 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(72, 7), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(392, 160), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 10.245759 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(73, 9), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(393, 162), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 10.250658 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(74, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(394, 163), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 10.258842 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(74, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(394, 165), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 10.26531 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(74, 13), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(394, 166), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 10.276154 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(75, 14), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(395, 167), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 10.281116 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(75, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(395, 168), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 10.290123 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(75, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(395, 168), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 10.490923 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2f, Qt.NoModifier, """/""", False, 1), 11.7432 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2f, Qt.NoModifier, """/""", False, 1), 11.81358 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1), 11.903111 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1), 12.015039 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1), 12.031953 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1), 12.12773 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000003, Qt.NoModifier, """""", False, 1), 12.647396 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000003, Qt.NoModifier, """""", False, 1), 12.751082 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4d, Qt.NoModifier, """m""", False, 1), 12.815633 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4d, Qt.NoModifier, """m""", False, 1), 12.871295 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x50, Qt.NoModifier, """p""", False, 1), 12.927425 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x50, Qt.NoModifier, """p""", False, 1), 12.999471 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2f, Qt.NoModifier, """/""", False, 1), 13.167607 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2f, Qt.NoModifier, """/""", False, 1), 13.29064 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1), 13.367465 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1), 13.439142 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1), 13.487649 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1), 13.511524 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x53, Qt.NoModifier, """s""", False, 1), 13.575277 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1), 13.631406 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x53, Qt.NoModifier, """s""", False, 1), 13.663502 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1), 13.69544 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, (Qt.ShiftModifier), """T""", False, 1), 13.727305 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1), 13.855106 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1), 13.886848 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x44, Qt.NoModifier, """d""", False, 1), 13.918754 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2d, Qt.NoModifier, """-""", False, 1), 13.928709 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x44, Qt.NoModifier, """d""", False, 1), 14.01525 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1), 14.015438 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1), 14.078973 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1), 14.087106 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1), 14.150841 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1), 14.191327 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1), 14.263311 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2f, Qt.NoModifier, """/""", False, 1), 14.455804 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2f, Qt.NoModifier, """/""", False, 1), 14.543373 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x43, Qt.NoModifier, """c""", False, 1), 15.431117 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x55, Qt.NoModifier, """u""", False, 1), 15.519486 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x43, Qt.NoModifier, """c""", False, 1), 15.567009 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x55, Qt.NoModifier, """u""", False, 1), 15.591123 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x42, Qt.NoModifier, """b""", False, 1), 15.678806 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x42, Qt.NoModifier, """b""", False, 1), 15.75944 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1), 15.767712 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1), 15.838967 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1), 15.910936 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1), 15.975414 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x5f, (Qt.ShiftModifier), """_""", False, 1), 16.055242 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1), 16.111164 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4f, Qt.NoModifier, """o""", False, 1), 16.159063 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4f, Qt.NoModifier, """o""", False, 1), 16.24751 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x42, Qt.NoModifier, """b""", False, 1), 16.311537 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x42, Qt.NoModifier, """b""", False, 1), 16.37529 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4a, Qt.NoModifier, """j""", False, 1), 16.463333 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1), 16.526847 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x43, Qt.NoModifier, """c""", False, 1), 16.551505 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4a, Qt.NoModifier, """j""", False, 1), 16.583433 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1), 16.583615 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x43, Qt.NoModifier, """c""", False, 1), 16.615365 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1), 16.695132 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1), 16.767041 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x53, Qt.NoModifier, """s""", False, 1), 16.791063 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x53, Qt.NoModifier, """s""", False, 1), 16.839483 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1), 17.343002 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1), 17.423293 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1), 17.519149 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2d, Qt.NoModifier, """-""", False, 1), 17.527164 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x52, Qt.NoModifier, """r""", False, 1), 17.775369 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1), 17.878879 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x52, Qt.NoModifier, """r""", False, 1), 17.927122 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x57, Qt.NoModifier, """w""", False, 1), 17.951327 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1), 17.991206 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x57, Qt.NoModifier, """w""", False, 1), 18.055029 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2e, Qt.NoModifier, """.""", False, 1), 18.062957 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2e, Qt.NoModifier, """.""", False, 1), 18.167354 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4e, Qt.NoModifier, """n""", False, 1), 18.351216 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4e, Qt.NoModifier, """n""", False, 1), 18.423087 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x50, Qt.NoModifier, """p""", False, 1), 18.487188 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x50, Qt.NoModifier, """p""", False, 1), 18.55963 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x59, Qt.NoModifier, """y""", False, 1), 18.607645 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x59, Qt.NoModifier, """y""", False, 1), 18.66345 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000004, Qt.NoModifier, """""", False, 1), 18.73536 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.appendButton' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000004, Qt.NoModifier, """""", False, 1), 19.20357 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_tabbar' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(147, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(465, 49), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 20.875392 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_tabbar' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(147, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(465, 49), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 20.989805 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.appendButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(69, 17), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(389, 137), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 21.691355 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_1' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(69, -14), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(389, 139), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 21.971925 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_1' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(69, -11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(389, 142), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 21.982497 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_1' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(68, -6), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(388, 147), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 21.99597 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_1' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(68, -1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(388, 152), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 22.013915 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_1' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(68, 2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(388, 155), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 22.031116 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_1' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(66, 7), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(386, 160), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 22.050616 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_1' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(66, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(386, 161), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 22.063936 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_1' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(66, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(386, 161), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 22.355053 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(141, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(437, 67), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 26.227505 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(141, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(437, 67), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 26.308061 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonDblClick, PyQt4.QtCore.QPoint(141, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(437, 67), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 26.435201 )

    ########################
    player.display_comment("""Navigate to Object Extraction tab...""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_5_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(179, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(185, 311), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 31.312366 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_5_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(179, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(185, 311), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 31.416707 )

    ########################
    player.display_comment("""Select Features: Count, Mean""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_6_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.containingWidget.selectFeaturesButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(153, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(168, 132), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 36.754594 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_6_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.containingWidget.selectFeaturesButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(153, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(168, 132), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 37.015365 )

    obj = get_named_object( 'FeatureSelectionDialog.widget.treeWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(51, 204), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(210, 264), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 38.986941 )

    obj = get_named_object( 'FeatureSelectionDialog.widget.treeWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(51, 204), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(210, 264), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 39.060032 )

    obj = get_named_object( 'FeatureSelectionDialog.widget.treeWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(51, 309), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(210, 369), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 40.186476 )

    obj = get_named_object( 'FeatureSelectionDialog.widget.treeWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(51, 309), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(210, 369), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 40.258932 )

    obj = get_named_object( 'FeatureSelectionDialog.widget.buttonBox.child_1_QPushButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(53, 24), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(536, 473), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 41.434418 )

    obj = get_named_object( 'FeatureSelectionDialog.widget.buttonBox.child_1_QPushButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(53, 24), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(536, 473), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 41.539617 )

    ########################
    player.display_comment("""Navigate to Object Classification tab...""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(123, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(129, 338), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 44.611164 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(123, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(129, 338), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 44.674309 )

    ########################
    player.display_comment("""Subset Features (all)""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.subsetFeaturesButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(173, 13), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(188, 164), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 51.305377 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.subsetFeaturesButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(173, 13), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(188, 164), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 51.448522 )

    obj = get_named_object( 'FeatureSubSelectionDialog.widget.treeWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(53, 19), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(212, 79), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 52.520077 )

    obj = get_named_object( 'FeatureSubSelectionDialog.widget.treeWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(53, 19), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(212, 79), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 52.6023 )

    obj = get_named_object( 'FeatureSubSelectionDialog.widget.treeWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(52, 41), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(211, 101), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 52.980785 )

    obj = get_named_object( 'FeatureSubSelectionDialog.widget.treeWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(52, 41), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(211, 101), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 53.053233 )

    obj = get_named_object( 'FeatureSubSelectionDialog.widget.buttonBox.child_1_QPushButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(28, 19), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(511, 468), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 54.440319 )

    obj = get_named_object( 'FeatureSubSelectionDialog.widget.buttonBox.child_1_QPushButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(28, 19), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(511, 468), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 54.554533 )

    ########################
    player.display_comment("""Add label classes""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.AddLabelButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(153, 17), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(168, 311), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 58.632907 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.AddLabelButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(153, 17), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(168, 311), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 58.760697 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.AddLabelButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(173, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(188, 306), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 59.856891 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.AddLabelButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(173, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(188, 306), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 60.008216 )

    ########################
    player.display_comment("""Hide \'Objects\' layer""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_3_lane_0.layerWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(18, 96), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(25, 543), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 65.622695 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_3_lane_0.layerWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(18, 96), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(25, 543), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 65.884971 )

    ########################
    player.display_comment("""Label 2 objects""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_3_lane_0.layerWidget' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000021, (Qt.ControlModifier), """""", False, 1), 70.191886 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(149, 187), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(460, 214), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 70.214428 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(151, 191), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(462, 218), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 70.240964 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(153, 193), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(464, 220), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 70.26375 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(156, 197), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(467, 224), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 70.286189 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(158, 198), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(469, 225), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 70.301324 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(163, 200), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(474, 227), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 70.32194 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(165, 201), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(476, 228), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 70.360113 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(165, 201), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(476, 228), 240, Qt.NoButton, (Qt.ControlModifier), 2), 70.38915 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(165, 201), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(476, 228), 240, Qt.NoButton, (Qt.ControlModifier), 2), 70.496887 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(165, 201), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(476, 228), 120, Qt.NoButton, (Qt.ControlModifier), 2), 70.526973 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(165, 201), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(476, 228), 120, Qt.NoButton, (Qt.ControlModifier), 2), 70.80226 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(165, 201), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(476, 228), 120, Qt.NoButton, (Qt.ControlModifier), 2), 71.088911 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(165, 201), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(476, 228), 120, Qt.NoButton, (Qt.ControlModifier), 2), 71.25022 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(165, 201), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(476, 228), 120, Qt.NoButton, (Qt.ControlModifier), 2), 71.40126 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(165, 201), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(476, 228), 120, Qt.NoButton, (Qt.ControlModifier), 2), 71.601223 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(165, 201), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(476, 228), 120, Qt.NoButton, (Qt.ControlModifier), 2), 71.818348 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(165, 201), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(476, 228), 120, Qt.NoButton, (Qt.ControlModifier), 2), 72.681633 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_3_lane_0.layerWidget' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000021, Qt.NoModifier, """""", False, 1), 73.516912 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.child_2_QTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(208, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(225, 207), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 75.152434 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.child_2_QTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(208, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(225, 207), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 75.265434 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(109, 106), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(420, 133), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 76.3527 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(109, 106), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(420, 133), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 76.727381 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.child_2_QTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(169, 45), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(186, 244), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 79.209317 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.child_2_QTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(169, 45), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(186, 244), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 79.335424 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000021, (Qt.ControlModifier), """""", False, 1), 80.755268 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(210, 111), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(521, 138), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 80.775711 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(209, 111), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(520, 138), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 80.862541 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(211, 111), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(522, 138), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 80.927266 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(218, 109), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(529, 136), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 80.955038 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(222, 108), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(533, 135), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 80.978421 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(227, 105), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(538, 132), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 81.00714 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(230, 105), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(541, 132), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 81.030164 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(233, 105), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(544, 132), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 81.051818 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(236, 105), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(547, 132), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 81.088707 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(237, 105), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(548, 132), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 81.11659 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(238, 105), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(549, 132), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 81.137966 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(239, 105), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(550, 132), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 81.200636 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(239, 104), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(550, 131), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 81.399788 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(239, 104), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(550, 131), 120, Qt.NoButton, (Qt.ControlModifier), 2), 81.483672 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(239, 104), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(550, 131), 240, Qt.NoButton, (Qt.ControlModifier), 2), 81.519767 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(239, 104), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(550, 131), 120, Qt.NoButton, (Qt.ControlModifier), 2), 81.581721 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(239, 104), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(550, 131), 120, Qt.NoButton, (Qt.ControlModifier), 2), 81.646091 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(240, 104), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(551, 131), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 81.817339 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(245, 103), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(556, 130), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 81.846074 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(255, 103), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(566, 130), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 81.871225 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(260, 103), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(571, 130), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 81.89702 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(260, 102), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(571, 129), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 81.936304 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(261, 102), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(572, 129), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 81.968189 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000021, Qt.NoModifier, """""", False, 1), 81.991462 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(250, 99), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(561, 126), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 82.963519 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(250, 99), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(561, 126), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 83.288187 )

    ########################
    player.display_comment("""Live Update""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.checkInteractive' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(9, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(24, 331), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 91.096759 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.checkInteractive' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(9, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(24, 331), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 91.17301 )

    ########################
    player.display_comment("""Save Project""")
    ########################

    obj = get_named_object( 'MainWindow.child_7_QMenuBar' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(23, 9), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(23, 9), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 95.848883 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(23, -10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(23, 9), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 95.931196 )

    obj = get_named_object( 'MainWindow.child_7_QMenuBar' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(24, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(27, 19), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 96.344754 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(25, -3), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(25, 16), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 96.365413 )

    obj = get_named_object( 'MainWindow.child_7_QMenuBar' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(25, 16), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(35, 38), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 96.385151 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(27, 0), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(27, 19), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 96.403907 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(39, 30), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(39, 49), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 96.420105 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(40, 33), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(40, 52), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 96.43849 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(42, 37), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(42, 56), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 96.461267 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(42, 39), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(42, 58), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 96.478739 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(42, 42), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(42, 61), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 96.499688 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(43, 42), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(43, 61), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 96.516024 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(43, 44), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(43, 63), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 96.539398 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(43, 46), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(43, 65), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 96.561382 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(43, 48), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(43, 67), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 96.582423 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(43, 49), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(43, 68), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 96.654142 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(43, 50), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(43, 69), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 96.670347 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(43, 51), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(43, 70), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 96.701437 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(42, 53), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(42, 72), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 96.718518 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(41, 54), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(41, 73), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 96.737678 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(41, 56), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(41, 75), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 96.752656 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(40, 56), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(40, 75), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 96.770589 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(40, 57), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(40, 76), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 96.789113 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(40, 57), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(40, 76), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 96.904585 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(40, 57), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(40, 76), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 96.984711 )

    player.display_comment("SCRIPT COMPLETE")
