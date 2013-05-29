
# Event Recording
# Started at: 2013-05-29 03:27:05.118252

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

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.startupPage.frame.CreateList.qt_scrollarea_viewport.scrollAreaWidgetContents.child_7_QToolButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(46, 6), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(357, 291), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 3.868564 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.startupPage.frame.CreateList.qt_scrollarea_viewport.scrollAreaWidgetContents.child_7_QToolButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(46, 6), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(357, 291), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 3.969813 )

    obj = get_named_object( 'MainWindow.QFileDialog.buttonBox.child_1_QPushButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(45, 18), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(685, 385), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 5.244236 )

    obj = get_named_object( 'MainWindow.QFileDialog.buttonBox.child_1_QPushButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(45, 18), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(685, 385), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 5.32275 )

    ########################
    player.display_comment("""Add data (raw and binary)""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.child_3_DataDetailViewerWidget.appendButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(51, 21), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(371, 141), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 7.664001 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(50, -10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(370, 143), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 7.800635 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(49, -8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(369, 145), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 7.815201 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(48, -4), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(368, 149), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 7.833791 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(47, -1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(367, 152), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 7.846779 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(47, 2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(367, 155), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 7.868041 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(47, 2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(367, 155), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 7.873241 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(46, 3), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(366, 156), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 7.881459 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(46, 3), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(366, 156), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 8.11859 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2f, Qt.NoModifier, """/""", False, 1), 9.975926 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2f, Qt.NoModifier, """/""", False, 1), 10.036547 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1), 10.119404 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4d, Qt.NoModifier, """m""", False, 1), 10.168508 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1), 10.222457 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4d, Qt.NoModifier, """m""", False, 1), 10.256198 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x50, Qt.NoModifier, """p""", False, 1), 10.287492 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x50, Qt.NoModifier, """p""", False, 1), 10.391746 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2f, Qt.NoModifier, """/""", False, 1), 11.423513 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2f, Qt.NoModifier, """/""", False, 1), 11.51963 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1), 11.855816 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1), 11.910757 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1), 11.968072 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1), 11.976021 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x53, Qt.NoModifier, """s""", False, 1), 12.062799 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1), 12.119603 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x53, Qt.NoModifier, """s""", False, 1), 12.135039 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1), 12.208232 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1), 12.239894 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1), 12.455382 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1), 12.503324 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2d, Qt.NoModifier, """-""", False, 1), 12.544053 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x44, Qt.NoModifier, """d""", False, 1), 12.591974 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x44, Qt.NoModifier, """d""", False, 1), 12.679196 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1), 12.702657 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1), 12.750912 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1), 12.776099 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1), 12.839068 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1), 12.880019 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1), 12.935886 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2f, Qt.NoModifier, """/""", False, 1), 12.967965 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2f, Qt.NoModifier, """/""", False, 1), 13.039118 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x43, Qt.NoModifier, """c""", False, 1), 14.09605 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x43, Qt.NoModifier, """c""", False, 1), 14.216233 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x55, Qt.NoModifier, """u""", False, 1), 14.288627 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x55, Qt.NoModifier, """u""", False, 1), 14.335682 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x42, Qt.NoModifier, """b""", False, 1), 14.447518 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x42, Qt.NoModifier, """b""", False, 1), 14.535205 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1), 14.806938 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1), 14.887559 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1), 15.031045 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1), 15.112055 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x5f, (Qt.ShiftModifier), """_""", False, 1), 15.183979 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1), 15.2385 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4f, Qt.NoModifier, """o""", False, 1), 15.304513 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4f, Qt.NoModifier, """o""", False, 1), 15.383568 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x42, Qt.NoModifier, """b""", False, 1), 15.447409 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x42, Qt.NoModifier, """b""", False, 1), 15.503965 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4a, Qt.NoModifier, """j""", False, 1), 15.600345 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1), 15.64714 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x43, Qt.NoModifier, """c""", False, 1), 15.670117 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1), 15.702601 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4a, Qt.NoModifier, """j""", False, 1), 15.710271 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x43, Qt.NoModifier, """c""", False, 1), 15.752439 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1), 15.815073 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1), 15.903104 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x53, Qt.NoModifier, """s""", False, 1), 16.000131 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x53, Qt.NoModifier, """s""", False, 1), 16.079567 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1), 16.255808 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1), 16.416004 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x5f, (Qt.ShiftModifier), """_""", False, 1), 16.495483 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1), 16.520422 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x52, Qt.NoModifier, """r""", False, 1), 16.646586 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1), 16.79077 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x52, Qt.NoModifier, """r""", False, 1), 16.822296 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x57, Qt.NoModifier, """w""", False, 1), 16.872644 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1), 16.911223 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x57, Qt.NoModifier, """w""", False, 1), 16.983764 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2e, Qt.NoModifier, """.""", False, 1), 17.176093 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2e, Qt.NoModifier, """.""", False, 1), 17.288124 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4e, Qt.NoModifier, """n""", False, 1), 17.59127 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4e, Qt.NoModifier, """n""", False, 1), 17.65508 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x50, Qt.NoModifier, """p""", False, 1), 17.728296 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x50, Qt.NoModifier, """p""", False, 1), 17.822743 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x59, Qt.NoModifier, """y""", False, 1), 17.879322 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x59, Qt.NoModifier, """y""", False, 1), 17.959625 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000004, Qt.NoModifier, """""", False, 1), 18.847862 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.child_3_DataDetailViewerWidget.appendButton' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000004, Qt.NoModifier, """""", False, 1), 19.131444 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_tabbar' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(125, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(443, 46), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 20.855037 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_tabbar' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(125, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(443, 46), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 20.923978 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.appendButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(62, 23), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(382, 143), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 21.458533 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_1' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(60, -7), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(380, 146), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 21.560473 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_1' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(59, -4), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(379, 149), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 21.573477 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_1' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(58, 3), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(378, 156), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 21.590796 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_1' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(58, 3), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(378, 156), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 21.596945 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_1' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(57, 7), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(377, 160), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 21.606976 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_1' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(56, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(376, 163), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 21.622779 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_1' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(56, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(376, 164), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 21.640081 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_1' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(56, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(376, 164), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 21.830303 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(140, 7), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(352, 70), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 24.356279 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(140, 7), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(352, 70), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 24.440794 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonDblClick, PyQt4.QtCore.QPoint(140, 7), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(352, 70), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 24.488601 )

    ########################
    player.display_comment("""Object Extraction....""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(90, 54), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(97, 81), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 30.5576 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(90, 54), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(97, 81), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 30.610374 )

    ########################
    player.display_comment("""Select Features: Count / Mean""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.containingWidget.selectFeaturesButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(38, 18), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(84, 99), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 33.916885 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.containingWidget.selectFeaturesButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(38, 18), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(84, 99), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 34.018619 )

    obj = get_named_object( 'FeatureSelectionDialog.widget.treeWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(47, 197), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(79, 252), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 35.264293 )

    obj = get_named_object( 'FeatureSelectionDialog.widget.treeWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(47, 197), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(79, 252), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 35.348505 )

    obj = get_named_object( 'FeatureSelectionDialog.widget.treeWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(52, 307), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(84, 362), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 36.409977 )

    obj = get_named_object( 'FeatureSelectionDialog.widget.treeWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(52, 307), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(84, 362), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 36.495696 )

    obj = get_named_object( 'FeatureSelectionDialog.widget.buttonBox.child_1_QPushButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(33, 13), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(389, 457), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 37.07359 )

    obj = get_named_object( 'FeatureSelectionDialog.widget.buttonBox.child_1_QPushButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(33, 13), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(389, 457), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 37.169121 )

    ########################
    player.display_comment("""Object Classification...""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(90, 97), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(97, 124), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 41.758328 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(90, 97), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(97, 124), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 41.833266 )

    ########################
    player.display_comment("""Subset Features""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.subsetFeaturesButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(160, 17), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(206, 113), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 44.66739 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.subsetFeaturesButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(160, 17), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(206, 113), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 44.745302 )

    obj = get_named_object( 'FeatureSubSelectionDialog.widget.treeWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(51, 24), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(83, 79), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 45.622311 )

    obj = get_named_object( 'FeatureSubSelectionDialog.widget.treeWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(51, 25), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(83, 80), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 45.694216 )

    obj = get_named_object( 'FeatureSubSelectionDialog.widget.treeWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(51, 25), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(83, 80), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 45.708329 )

    obj = get_named_object( 'FeatureSubSelectionDialog.widget.treeWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(55, 38), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(87, 93), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 45.807626 )

    obj = get_named_object( 'FeatureSubSelectionDialog.widget.treeWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(56, 39), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(88, 94), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 45.811504 )

    obj = get_named_object( 'FeatureSubSelectionDialog.widget.treeWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(56, 39), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(88, 94), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 45.88624 )

    obj = get_named_object( 'FeatureSubSelectionDialog.widget.treeWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(51, 36), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(83, 91), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 46.893671 )

    obj = get_named_object( 'FeatureSubSelectionDialog.widget.treeWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(51, 36), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(83, 91), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 46.984014 )

    obj = get_named_object( 'FeatureSubSelectionDialog.widget.buttonBox.child_1_QPushButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(28, 20), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(384, 464), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 47.713804 )

    obj = get_named_object( 'FeatureSubSelectionDialog.widget.buttonBox.child_1_QPushButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(28, 20), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(384, 464), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 47.816362 )

    ########################
    player.display_comment("""Add Label Classes""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.AddLabelButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(83, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(129, 250), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 50.436681 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.AddLabelButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(83, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(129, 250), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 50.523946 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.AddLabelButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(89, 13), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(135, 252), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 51.719936 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.AddLabelButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(89, 13), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(135, 252), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 51.828561 )

    ########################
    player.display_comment("""Hide \"Objects\" layer""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(134, 3), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(139, 473), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 54.085652 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(134, 2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(139, 472), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 54.479566 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(134, 2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(139, 471), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 54.51943 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(134, 2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(139, 470), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 54.530164 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(134, 2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(139, 469), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 54.572366 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(134, -1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(139, 465), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 54.579332 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(134, 0), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(139, 462), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 54.626171 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(134, -1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(139, 458), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 54.633544 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(134, 1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(139, 456), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 54.681457 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(134, 0), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(139, 453), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 54.689774 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(134, 1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(139, 451), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 54.696677 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(134, 1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(139, 449), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 54.739121 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(134, -2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(139, 444), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 54.746674 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(134, 0), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(139, 441), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 54.782184 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(134, 1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(139, 439), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 54.791799 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(134, 1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(139, 437), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 54.803622 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(134, 0), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(139, 434), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 54.837872 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(134, -4), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(139, 427), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 54.846399 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(134, -1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(139, 423), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 54.893955 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(135, -2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(140, 418), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 54.90136 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(135, 1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(140, 416), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 54.946651 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(135, -3), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(140, 410), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 54.954337 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(135, 1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(140, 408), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 54.96061 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(135, 2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(140, 407), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 55.003878 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(136, 0), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(141, 404), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 55.012032 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(136, 1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(141, 402), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 55.052785 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(136, 0), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(141, 399), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 55.06112 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(136, 1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(141, 397), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 55.110802 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(136, 2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(141, 396), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 55.117589 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(136, 2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(141, 395), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 55.160381 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(136, 1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(141, 393), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 55.167954 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(136, 1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(141, 391), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 55.211572 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(136, 2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(141, 390), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 55.218645 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(136, 1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(141, 388), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 55.261676 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(136, 2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(141, 387), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 55.270622 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(136, 2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(141, 386), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 55.321755 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(136, 1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(141, 384), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 55.329779 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(136, 2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(141, 383), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 55.375287 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(136, 2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(141, 382), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 55.420886 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(136, 2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(141, 381), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 55.430975 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(136, 2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(141, 380), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 55.48471 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(136, 2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(141, 379), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 55.492827 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(136, 3), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(141, 379), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 56.084996 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_3_lane_0.layerWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(11, 62), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(18, 444), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 57.814355 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_3_lane_0.layerWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(11, 62), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(18, 444), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 57.966335 )

    ########################
    player.display_comment("""Label 2 objects""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(0, 110), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(565, 135), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 60.948924 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(246, 108), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(557, 135), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 60.968369 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(236, 108), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(547, 135), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 60.983548 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(227, 109), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(538, 136), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 60.999839 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(215, 109), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(526, 136), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 61.019967 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(203, 108), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(514, 135), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 61.033077 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(192, 106), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(503, 133), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 61.050661 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(182, 105), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(493, 132), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 61.066156 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(179, 105), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(490, 132), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 61.083615 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(175, 105), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(486, 132), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 61.099835 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(169, 107), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(480, 134), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 61.11652 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(164, 110), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(475, 137), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 61.132379 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(158, 113), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(469, 140), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 61.150648 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(154, 117), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(465, 144), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 61.166686 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(150, 118), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(461, 145), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 61.183577 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(148, 119), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(459, 146), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 61.200577 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(146, 120), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(457, 147), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 61.216062 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(145, 121), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(456, 148), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 61.234231 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(143, 122), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(454, 149), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 61.249823 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(142, 122), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(453, 149), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 61.267028 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(141, 124), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(452, 151), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 61.283669 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(138, 126), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(449, 153), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 61.299086 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(137, 127), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(448, 154), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 61.31658 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(135, 127), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(446, 154), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 61.332452 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(133, 128), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(444, 155), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 61.349695 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(133, 129), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(444, 156), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 61.366472 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(132, 129), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(443, 156), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 61.633886 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(132, 130), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(443, 157), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 61.686601 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(131, 131), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(442, 158), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 61.88621 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(128, 134), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(439, 161), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 61.903362 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(127, 135), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(438, 162), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 61.984905 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(126, 136), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(437, 163), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 62.001963 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(125, 136), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(436, 163), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 62.017076 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_8_QCheckBox' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(9, 14), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(742, 616), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 63.609628 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_8_QCheckBox' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(9, 14), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(742, 616), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 63.683126 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_8_QCheckBox' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000021, (Qt.ControlModifier), """""", False, 1), 64.052891 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(60, 103), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(371, 130), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 64.061427 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(60, 100), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(371, 127), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 64.071645 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(58, 92), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(369, 119), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 64.088607 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(56, 86), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(367, 113), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 64.106443 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(58, 85), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(369, 112), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 64.139022 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(67, 89), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(378, 116), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 64.155502 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(83, 97), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(394, 124), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 64.171948 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(96, 103), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(407, 130), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 64.189454 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(107, 108), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(418, 135), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 64.205422 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(109, 109), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(420, 136), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 64.224128 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(109, 110), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(420, 137), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 64.243521 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(110, 111), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(421, 138), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 64.256932 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(112, 115), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(423, 142), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 64.27216 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(115, 122), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(426, 149), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 64.289138 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(118, 126), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(429, 153), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 64.310107 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(120, 129), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(431, 156), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 64.321908 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(120, 130), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(431, 157), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 64.356379 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(121, 137), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(432, 164), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 64.37201 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(125, 144), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(436, 171), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 64.388896 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(128, 150), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(439, 177), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 64.405882 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(131, 151), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(442, 178), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 64.421354 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(132, 151), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(443, 178), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 64.492977 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(132, 148), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(443, 175), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 64.558713 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(129, 144), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(440, 171), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 64.574873 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(128, 142), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(439, 169), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 64.606252 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(128, 141), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(439, 168), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 64.623028 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(128, 140), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(439, 167), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 64.657715 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(128, 139), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(439, 166), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 64.673823 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(128, 139), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(439, 166), 120, Qt.NoButton, (Qt.ControlModifier), 2), 64.697515 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(128, 139), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(439, 166), 120, Qt.NoButton, (Qt.ControlModifier), 2), 64.728005 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(128, 139), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(439, 166), 240, Qt.NoButton, (Qt.ControlModifier), 2), 64.768795 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(128, 139), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(439, 166), 1320, Qt.NoButton, (Qt.ControlModifier), 2), 64.779466 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(128, 139), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(439, 166), 360, Qt.NoButton, (Qt.ControlModifier), 2), 65.164602 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(128, 139), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(439, 166), 960, Qt.NoButton, (Qt.ControlModifier), 2), 65.198096 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(128, 139), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(439, 166), 2160, Qt.NoButton, (Qt.ControlModifier), 2), 65.213012 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(128, 139), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(439, 166), 600, Qt.NoButton, (Qt.ControlModifier), 2), 65.255965 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(128, 139), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(439, 166), 480, Qt.NoButton, (Qt.ControlModifier), 2), 65.62767 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(128, 139), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(439, 166), 1680, Qt.NoButton, (Qt.ControlModifier), 2), 65.665939 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(128, 139), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(439, 166), 1200, Qt.NoButton, (Qt.ControlModifier), 2), 65.677113 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(128, 139), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(439, 166), 480, Qt.NoButton, (Qt.ControlModifier), 2), 65.728698 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(128, 139), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(439, 166), 120, Qt.NoButton, (Qt.ControlModifier), 2), 66.348277 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(128, 139), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(439, 166), 120, Qt.NoButton, (Qt.ControlModifier), 2), 66.379066 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(128, 139), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(439, 166), 600, Qt.NoButton, (Qt.ControlModifier), 2), 66.391428 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(128, 139), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(439, 166), 480, Qt.NoButton, (Qt.ControlModifier), 2), 66.434364 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(128, 139), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(439, 166), 480, Qt.NoButton, (Qt.ControlModifier), 2), 66.455601 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(128, 139), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(439, 166), 120, Qt.NoButton, (Qt.ControlModifier), 2), 67.049524 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_8_QCheckBox' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000021, Qt.NoModifier, """""", False, 1), 67.428555 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.child_2_QTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(171, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(219, 154), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 68.17815 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.child_2_QTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(171, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(219, 155), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 68.239266 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.child_2_QTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(171, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(219, 155), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 68.250965 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(47, 153), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(358, 180), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 69.24484 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(47, 153), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(358, 180), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 69.548947 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.child_2_QTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(109, 44), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(157, 188), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 70.325261 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.child_2_QTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(109, 44), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(157, 188), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 70.410055 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(158, 151), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(469, 178), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 71.440331 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(158, 151), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(469, 178), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 71.795558 )

    ########################
    player.display_comment("""Live Update""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.checkInteractive' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(20, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(66, 278), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 74.133964 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.checkInteractive' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(20, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(66, 278), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 74.218903 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.checkInteractive' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000021, (Qt.ControlModifier), """""", False, 1), 76.238661 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(134, 203), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(445, 230), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 76.260338 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(134, 195), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(445, 222), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 76.278972 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(127, 171), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(438, 198), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 76.293861 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(116, 151), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(427, 178), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 76.31262 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(104, 134), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(415, 161), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 76.327782 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(96, 125), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(407, 152), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 76.344122 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(94, 127), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(405, 154), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 76.545558 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(94, 134), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(405, 161), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 76.5634 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(97, 139), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(408, 166), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 76.578633 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(100, 145), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(411, 172), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 76.595384 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(100, 145), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(411, 172), -120, Qt.NoButton, (Qt.ControlModifier), 2), 76.68187 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(100, 145), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(411, 172), -120, Qt.NoButton, (Qt.ControlModifier), 2), 76.728844 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(100, 145), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(411, 172), -1680, Qt.NoButton, (Qt.ControlModifier), 2), 76.741763 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(99, 147), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(410, 174), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 76.752935 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(99, 147), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(410, 174), -1080, Qt.NoButton, (Qt.ControlModifier), 2), 76.781354 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(99, 147), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(410, 174), -720, Qt.NoButton, (Qt.ControlModifier), 2), 76.794329 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(99, 147), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(410, 174), -720, Qt.NoButton, (Qt.ControlModifier), 2), 76.830776 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(99, 147), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(410, 174), -480, Qt.NoButton, (Qt.ControlModifier), 2), 77.091013 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(99, 147), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(410, 174), -600, Qt.NoButton, (Qt.ControlModifier), 2), 77.134694 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(99, 147), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(410, 174), -2640, Qt.NoButton, (Qt.ControlModifier), 2), 77.147834 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(99, 147), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(410, 174), -600, Qt.NoButton, (Qt.ControlModifier), 2), 77.188395 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(99, 147), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(410, 174), -720, Qt.NoButton, (Qt.ControlModifier), 2), 77.200569 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(99, 147), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(410, 174), 120, Qt.NoButton, (Qt.ControlModifier), 2), 77.641948 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(99, 147), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(410, 174), 120, Qt.NoButton, (Qt.ControlModifier), 2), 77.685971 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(99, 147), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(410, 174), 240, Qt.NoButton, (Qt.ControlModifier), 2), 77.730368 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.checkInteractive' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000021, Qt.NoModifier, """""", False, 1), 78.054163 )

    ########################
    player.display_comment("""Save Project""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.checkInteractive' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000021, (Qt.ControlModifier), """""", False, 1), 82.130338 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.checkInteractive' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x53, (Qt.ControlModifier), """""", False, 1), 82.346827 )

    obj = get_named_object( 'MainWindow' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x53, (Qt.ControlModifier), """""", False, 1), 82.689363 )

    obj = get_named_object( 'MainWindow' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000021, Qt.NoModifier, """""", False, 1), 82.68979 )

    player.display_comment("SCRIPT COMPLETE")
