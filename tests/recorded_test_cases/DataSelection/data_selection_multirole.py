
# Event Recording
# Started at: 2013-06-25 18:32:00.772564

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
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(95, 9), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(406, 266), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 2.121171 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.startupPage.frame.CreateList.qt_scrollarea_viewport.scrollAreaWidgetContents.child_4_QToolButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(95, 9), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(406, 266), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 2.201118 )

    obj = get_named_object( 'MainWindow.QFileDialog.fileNameEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000004, Qt.NoModifier, """""", False, 1), 4.005714 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_2_QScrollArea' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000004, Qt.NoModifier, """""", False, 1), 4.433816 )

    ########################
    player.display_comment("""Add raw data""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.appendButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(66, 20), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(386, 140), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 7.118417 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(66, -13), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(386, 140), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 7.200823 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(64, -1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(384, 152), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 7.357397 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(64, 0), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(384, 153), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 7.372735 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(62, 5), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(382, 158), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 7.385161 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(62, 6), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(382, 159), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 7.398111 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(61, 9), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(381, 162), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 7.425732 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(61, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(381, 164), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 7.441559 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(61, 13), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(381, 166), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 7.454478 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(60, 14), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(380, 167), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 7.468724 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(60, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(380, 168), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 7.483353 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(60, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(380, 168), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 7.614459 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(60, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(380, 168), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 7.694367 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2f, Qt.NoModifier, """/""", False, 1), 10.23469 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2f, Qt.NoModifier, """/""", False, 1), 10.34657 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1), 10.466689 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4d, Qt.NoModifier, """m""", False, 1), 10.514508 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1), 10.587336 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x50, Qt.NoModifier, """p""", False, 1), 10.59511 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4d, Qt.NoModifier, """m""", False, 1), 10.618819 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x50, Qt.NoModifier, """p""", False, 1), 10.68313 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2f, Qt.NoModifier, """/""", False, 1), 10.787113 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2f, Qt.NoModifier, """/""", False, 1), 10.923451 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1), 10.970875 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1), 11.042976 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1), 11.098383 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1), 11.114583 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x53, Qt.NoModifier, """s""", False, 1), 11.170556 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1), 11.234459 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x53, Qt.NoModifier, """s""", False, 1), 11.267668 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1), 11.314309 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, (Qt.ShiftModifier), """T""", False, 1), 11.338829 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1), 11.418934 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1), 11.482698 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x44, Qt.NoModifier, """d""", False, 1), 11.498812 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2d, Qt.NoModifier, """-""", False, 1), 11.522606 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x44, Qt.NoModifier, """d""", False, 1), 11.570512 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1), 11.594415 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1), 11.658972 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1), 11.667053 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1), 11.730708 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1), 11.778421 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1), 11.834379 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2f, Qt.NoModifier, """/""", False, 1), 11.858491 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2f, Qt.NoModifier, """/""", False, 1), 11.954873 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x43, Qt.NoModifier, """c""", False, 1), 12.938216 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x55, Qt.NoModifier, """u""", False, 1), 13.026725 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x43, Qt.NoModifier, """c""", False, 1), 13.042274 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x55, Qt.NoModifier, """u""", False, 1), 13.099043 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x42, Qt.NoModifier, """b""", False, 1), 13.195082 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x42, Qt.NoModifier, """b""", False, 1), 13.290656 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1), 13.314873 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1), 13.388916 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1), 13.498906 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1), 13.562567 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x5f, (Qt.ShiftModifier), """_""", False, 1), 13.650866 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1), 13.675027 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4f, Qt.NoModifier, """o""", False, 1), 13.778658 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4f, Qt.NoModifier, """o""", False, 1), 13.843011 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x42, Qt.NoModifier, """b""", False, 1), 13.92301 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x42, Qt.NoModifier, """b""", False, 1), 13.978561 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4a, Qt.NoModifier, """j""", False, 1), 14.059128 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1), 14.114773 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x43, Qt.NoModifier, """c""", False, 1), 14.162848 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4a, Qt.NoModifier, """j""", False, 1), 14.172381 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1), 14.178729 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x43, Qt.NoModifier, """c""", False, 1), 14.21863 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1), 14.299038 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1), 14.354863 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x53, Qt.NoModifier, """s""", False, 1), 14.394683 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x53, Qt.NoModifier, """s""", False, 1), 14.466337 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1), 14.586503 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1), 14.698734 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1), 14.778977 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2d, Qt.NoModifier, """-""", False, 1), 14.794916 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x52, Qt.NoModifier, """r""", False, 1), 14.88304 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1), 14.987057 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x52, Qt.NoModifier, """r""", False, 1), 15.026743 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x57, Qt.NoModifier, """w""", False, 1), 15.082823 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1), 15.122445 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x57, Qt.NoModifier, """w""", False, 1), 15.194537 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2e, Qt.NoModifier, """.""", False, 1), 15.323064 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2e, Qt.NoModifier, """.""", False, 1), 15.45068 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4e, Qt.NoModifier, """n""", False, 1), 15.570533 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4e, Qt.NoModifier, """n""", False, 1), 15.674772 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x50, Qt.NoModifier, """p""", False, 1), 15.83468 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x50, Qt.NoModifier, """p""", False, 1), 15.922953 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x59, Qt.NoModifier, """y""", False, 1), 16.018747 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x59, Qt.NoModifier, """y""", False, 1), 16.100212 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000004, Qt.NoModifier, """""", False, 1), 16.49836 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.appendButton' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000004, Qt.NoModifier, """""", False, 1), 16.837965 )

    ########################
    player.display_comment("""Add binary (wrong file first try)""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.appendButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(108, 17), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(428, 137), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 22.861607 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(108, -16), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(428, 137), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 22.926183 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(133, -105), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(453, 48), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 24.07098 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_tabbar' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(124, 14), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(442, 48), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 25.182061 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_tabbar' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(125, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(443, 49), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 25.336181 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_tabbar' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(125, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(443, 49), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 25.353602 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.appendButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(99, 24), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(419, 144), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 25.98188 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_1' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(99, -9), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(419, 144), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 26.05605 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_1' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(98, -2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(418, 151), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 26.356192 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_1' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(97, 0), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(417, 153), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 26.376815 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_1' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(97, 4), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(417, 157), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 26.387345 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_1' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(96, 4), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(416, 157), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 26.41247 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_1' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(96, 6), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(416, 159), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 26.442319 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_1' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(96, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(416, 161), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 26.458957 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_1' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(95, 9), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(415, 162), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 26.477112 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_1' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(95, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(415, 163), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 26.538811 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_1' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(95, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(415, 163), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 26.933368 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_1' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(95, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(415, 163), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 27.013672 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(130, 21), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(426, 80), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 31.461687 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(130, 21), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(426, 80), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 31.590229 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000004, Qt.NoModifier, """""", False, 1), 34.442089 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.appendButton' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000004, Qt.NoModifier, """""", False, 1), 34.72533 )

    ########################
    player.display_comment("""Replace incorrect file.""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(118, 13), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(457, 95), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 37.649161 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(118, 13), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(457, 95), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 37.728908 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonDblClick, PyQt4.QtCore.QPoint(118, 13), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(457, 95), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 37.792793 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(118, 13), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(457, 95), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 38.000455 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.cancelButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(19, 23), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(619, 380), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 40.264581 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.cancelButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(19, 23), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(619, 380), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 40.360757 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(82, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(421, 97), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 42.064765 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(82, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(421, 97), (Qt.RightButton), (Qt.LeftButton | Qt.RightButton), Qt.NoModifier), 43.15311 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QContextMenuEvent(0, PyQt4.QtCore.QPoint(82, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(421, 97), Qt.NoModifier), 43.164532 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(19, 25), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(421, 97), (Qt.LeftButton), (Qt.RightButton), Qt.NoModifier), 43.344599 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(19, 25), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(421, 97), (Qt.RightButton), Qt.NoButton, Qt.NoModifier), 43.66502 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(21, 26), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(423, 98), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 43.790507 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(24, 30), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(426, 102), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 43.809547 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(26, 32), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(428, 104), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 43.828459 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(28, 33), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(430, 105), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 43.849447 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(28, 34), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(430, 106), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 43.862377 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(29, 34), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(431, 106), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 43.881467 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(29, 34), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(431, 106), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 44.168949 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(29, 34), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(431, 106), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 44.345115 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(127, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(423, 70), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 46.816607 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(127, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(423, 70), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 46.905544 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.buttonBox.child_1_QPushButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(18, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(743, 378), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 48.144447 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.buttonBox.child_1_QPushButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(18, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(743, 378), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 48.200708 )

    ########################
    player.display_comment("""Edit properties: axis order""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(159, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(498, 97), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 51.872876 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(159, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(498, 97), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 51.927439 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonDblClick, PyQt4.QtCore.QPoint(159, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(498, 97), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 51.985268 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(159, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(498, 97), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 52.198638 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(49, 5), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(375, 103), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 53.06102 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(40, 5), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(366, 103), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 53.074699 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(30, 5), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(356, 103), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 53.095809 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(16, 5), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(342, 103), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 53.111771 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(0, 6), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(326, 104), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 53.125619 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(-18, 9), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(308, 107), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 53.152371 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(-39, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(287, 110), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 53.163311 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(-42, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(284, 110), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 53.174058 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(-43, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(283, 110), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 53.199991 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(-43, 13), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(283, 111), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 53.214072 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(-43, 13), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(283, 111), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 53.223352 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5a, Qt.NoModifier, """z""", False, 1), 53.997324 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x5a, Qt.NoModifier, """z""", False, 1), 54.093172 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x59, Qt.NoModifier, """y""", False, 1), 54.293737 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x59, Qt.NoModifier, """y""", False, 1), 54.397366 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x58, Qt.NoModifier, """x""", False, 1), 54.52559 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x58, Qt.NoModifier, """x""", False, 1), 54.645345 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.okButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(29, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(712, 369), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 55.888537 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.okButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(29, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(712, 369), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 55.987125 )

    ########################
    player.display_comment("""Edit properties again: relative link""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(129, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(468, 97), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 57.837316 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(129, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(468, 97), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 57.893324 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonDblClick, PyQt4.QtCore.QPoint(129, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(468, 97), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 57.949129 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(129, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(468, 97), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 58.040427 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.storageComboBox' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(99, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(425, 200), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 58.997261 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.storageComboBox.child_1_QFrame' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(98, -5), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(424, 200), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 59.128712 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.storageComboBox.child_1_QFrame' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(98, -5), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(424, 200), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 59.195655 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(94, 0), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(422, 207), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 59.477654 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(94, 3), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(422, 210), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 59.498299 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(93, 6), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(421, 213), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 59.530228 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(93, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(421, 215), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 59.548162 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(92, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(420, 217), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 59.570161 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(92, 13), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(420, 220), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 59.590717 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(91, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(419, 222), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 59.617286 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(89, 19), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(417, 226), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 59.64817 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(89, 22), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(417, 229), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 59.667194 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(88, 23), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(416, 230), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 59.688285 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(88, 25), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(416, 232), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 59.717833 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(87, 27), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(415, 234), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 59.737331 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(87, 28), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(415, 235), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 59.757105 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(86, 28), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(414, 235), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 59.980175 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(85, 30), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(413, 237), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 59.997912 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(85, 31), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(413, 238), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 60.032638 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(85, 32), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(413, 239), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 60.045336 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(85, 33), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(413, 240), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 60.114559 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(85, 34), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(413, 241), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 60.154305 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(85, 35), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(413, 242), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 60.176584 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(84, 36), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(412, 243), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 60.196294 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(85, 36), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(413, 243), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 60.250774 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(85, 37), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(413, 244), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 60.280995 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(85, 37), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(413, 244), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 60.291499 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(85, 37), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(413, 244), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 60.351593 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.okButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(47, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(730, 369), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 61.917381 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.okButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(47, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(730, 369), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 61.973486 )

    ########################
    player.display_comment("""Edit raw properties: relative link""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_tabbar' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(57, 18), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(375, 52), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 64.492973 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_tabbar' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(57, 18), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(375, 52), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 64.673814 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(59, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(398, 93), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 66.612884 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(59, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(398, 93), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 66.684502 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonDblClick, PyQt4.QtCore.QPoint(59, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(398, 93), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 66.740985 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(59, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(398, 93), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 66.951275 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.widget.storageComboBox' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(103, 9), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(429, 194), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 68.180554 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.widget.storageComboBox.child_1_QFrame' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(103, -11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(429, 194), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 68.262085 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.widget.storageComboBox.child_1_QFrame' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(100, 0), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(426, 205), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 68.603126 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(92, 9), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(420, 216), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 68.628574 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(87, 16), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(415, 223), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 68.647888 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(86, 19), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(414, 226), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 68.681528 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(84, 23), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(412, 230), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 68.699154 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(83, 23), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(411, 230), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 68.729045 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(82, 25), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(410, 232), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 68.747295 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(81, 25), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(409, 232), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 68.763838 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(81, 26), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(409, 233), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 68.778694 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(80, 27), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(408, 234), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 68.922946 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(77, 31), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(405, 238), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 68.94696 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(74, 36), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(402, 243), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 68.976002 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(73, 38), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(401, 245), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 68.989183 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(72, 39), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(400, 246), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 69.004171 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(69, 40), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(397, 247), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 69.029269 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(69, 41), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(397, 248), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 69.047681 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(67, 41), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(395, 248), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 69.070304 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(66, 41), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(394, 248), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 69.088285 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(65, 41), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(393, 248), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 69.11471 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(65, 41), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(393, 248), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 69.190064 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(65, 41), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(393, 248), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 69.279313 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.widget.okButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(41, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(724, 365), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 70.212584 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.widget.okButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(41, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(724, 365), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 70.285796 )

    ########################
    player.display_comment("""Show summary tab.""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_tabbar' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(180, 9), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(498, 43), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 80.313243 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_tabbar' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(180, 9), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(498, 43), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 80.47544 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.qt_splithandle_' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(296, 1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(614, 156), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 84.769565 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.qt_splithandle_' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(295, 2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(613, 157), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 84.889086 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.qt_splithandle_' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(295, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(613, 164), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 84.911744 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.qt_splithandle_' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(300, 44), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(618, 207), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 85.041119 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.qt_splithandle_' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(303, 29), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(621, 235), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 85.051971 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.qt_splithandle_' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(301, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(619, 244), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 85.19485 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.qt_splithandle_' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(301, 2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(619, 245), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 85.208387 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.qt_splithandle_' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(301, -2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(619, 242), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 85.625496 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.qt_splithandle_' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(300, -1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(618, 240), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 85.641412 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.qt_splithandle_' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(298, -10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(616, 229), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 85.783102 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.qt_splithandle_' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(297, -4), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(615, 224), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 85.803926 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.qt_splithandle_' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(297, 1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(615, 224), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 86.401403 )

    ########################
    player.display_comment("""Remove all.""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.fileInfoTabWidgetPage1.laneSummaryTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(67, 14), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(406, 96), (Qt.RightButton), (Qt.RightButton), Qt.NoModifier), 91.248019 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.fileInfoTabWidgetPage1.laneSummaryTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QContextMenuEvent(0, PyQt4.QtCore.QPoint(67, 14), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(406, 96), Qt.NoModifier), 91.252047 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.fileInfoTabWidgetPage1.laneSummaryTableView.child_10_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(19, 25), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(406, 96), (Qt.RightButton), Qt.NoButton, Qt.NoModifier), 91.462793 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.fileInfoTabWidgetPage1.laneSummaryTableView.child_10_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(20, 22), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(407, 93), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 92.063615 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.fileInfoTabWidgetPage1.laneSummaryTableView.child_10_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(24, 16), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(411, 87), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 92.082611 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.fileInfoTabWidgetPage1.laneSummaryTableView.child_10_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(26, 14), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(413, 85), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 92.107913 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.fileInfoTabWidgetPage1.laneSummaryTableView.child_10_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(28, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(415, 83), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 92.12995 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.fileInfoTabWidgetPage1.laneSummaryTableView.child_10_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(29, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(416, 83), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 92.145216 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.fileInfoTabWidgetPage1.laneSummaryTableView.child_10_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(29, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(416, 82), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 92.156203 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.fileInfoTabWidgetPage1.laneSummaryTableView.child_10_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(29, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(416, 82), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 92.534559 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.fileInfoTabWidgetPage1.laneSummaryTableView.child_10_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(29, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(416, 82), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 92.670302 )

    player.display_comment("SCRIPT COMPLETE")
