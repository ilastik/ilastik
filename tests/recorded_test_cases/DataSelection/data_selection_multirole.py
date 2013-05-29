
# Event Recording
# Started at: 2013-05-29 03:33:46.166947

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
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(49, 7), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(360, 214), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 3.484852 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.startupPage.frame.CreateList.qt_scrollarea_viewport.scrollAreaWidgetContents.child_4_QToolButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(49, 7), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(360, 214), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 3.546279 )

    obj = get_named_object( 'MainWindow.QFileDialog.buttonBox.child_1_QPushButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(34, 6), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(674, 373), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 4.913581 )

    obj = get_named_object( 'MainWindow.QFileDialog.buttonBox.child_1_QPushButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(34, 7), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(674, 374), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 4.932002 )

    obj = get_named_object( 'MainWindow.QFileDialog.buttonBox.child_1_QPushButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(34, 7), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(674, 374), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 4.993418 )

    ########################
    player.display_comment("""Add raw""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(199, 2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(517, 157), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 7.902263 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(199, 3), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(517, 158), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 8.017487 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(200, 2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(518, 158), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 8.065307 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(200, 6), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(518, 162), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 8.068423 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(201, 3), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(519, 163), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 8.115302 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(201, 5), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(519, 166), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 8.122907 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(201, 3), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(519, 167), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 8.176191 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(201, 5), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(519, 170), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 8.18268 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(201, 3), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(519, 171), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 8.232991 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(201, 4), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(519, 173), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 8.236525 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(201, 3), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(519, 174), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 8.284259 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(201, 6), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(519, 178), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 8.295526 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(201, 3), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(519, 179), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 8.299373 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(201, 3), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(519, 180), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 8.343564 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(201, 3), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(519, 181), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 8.387544 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(201, 4), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(519, 183), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 8.398067 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(201, 3), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(519, 184), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 8.401856 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(201, 3), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(519, 185), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 8.450699 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(201, 4), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(519, 187), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 8.454336 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(200, 2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(518, 187), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 8.497929 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.child_3_QSplitterHandle' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(200, 2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(518, 187), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 8.59077 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.child_3_DataDetailViewerWidget.appendButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(39, 19), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(359, 169), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 9.398815 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(39, -14), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(359, 169), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 9.473071 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(39, 1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(359, 184), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 9.821534 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(39, 1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(359, 184), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 9.826657 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(39, 2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(359, 185), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 9.83714 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(39, 4), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(359, 187), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 9.856503 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(39, 4), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(359, 187), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 9.944122 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(39, 4), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(359, 187), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 10.131728 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2f, Qt.NoModifier, """/""", False, 1), 12.029059 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2f, Qt.NoModifier, """/""", False, 1), 12.103416 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1), 12.149936 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4d, Qt.NoModifier, """m""", False, 1), 12.205506 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1), 12.260795 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4d, Qt.NoModifier, """m""", False, 1), 12.268666 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x50, Qt.NoModifier, """p""", False, 1), 12.333915 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x50, Qt.NoModifier, """p""", False, 1), 12.388627 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2f, Qt.NoModifier, """/""", False, 1), 12.950312 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2f, Qt.NoModifier, """/""", False, 1), 13.045877 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1), 13.262163 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1), 13.326201 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1), 13.366153 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1), 13.389911 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x53, Qt.NoModifier, """s""", False, 1), 13.48594 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1), 13.54212 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x53, Qt.NoModifier, """s""", False, 1), 13.582308 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1), 13.621557 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1), 13.66205 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1), 13.79758 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1), 13.85284 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2d, Qt.NoModifier, """-""", False, 1), 13.86181 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x44, Qt.NoModifier, """d""", False, 1), 13.909328 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x44, Qt.NoModifier, """d""", False, 1), 13.982094 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1), 14.030094 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1), 14.061868 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1), 14.077455 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1), 14.150255 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1), 14.181012 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1), 14.230134 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2f, Qt.NoModifier, """/""", False, 1), 14.285928 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2f, Qt.NoModifier, """/""", False, 1), 14.373353 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x43, Qt.NoModifier, """c""", False, 1), 16.518218 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x55, Qt.NoModifier, """u""", False, 1), 16.605449 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x43, Qt.NoModifier, """c""", False, 1), 16.621307 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x55, Qt.NoModifier, """u""", False, 1), 16.654019 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x42, Qt.NoModifier, """b""", False, 1), 16.758187 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1), 16.838013 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x42, Qt.NoModifier, """b""", False, 1), 16.845205 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1), 16.89336 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1), 17.046561 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1), 17.134008 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x5f, (Qt.ShiftModifier), """_""", False, 1), 17.19001 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1), 17.300606 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4f, Qt.NoModifier, """o""", False, 1), 17.388637 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4f, Qt.NoModifier, """o""", False, 1), 17.470066 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x42, Qt.NoModifier, """b""", False, 1), 17.565267 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x42, Qt.NoModifier, """b""", False, 1), 17.621707 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4a, Qt.NoModifier, """j""", False, 1), 17.726644 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1), 17.748684 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4a, Qt.NoModifier, """j""", False, 1), 17.822026 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x43, Qt.NoModifier, """c""", False, 1), 17.885058 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1), 17.889478 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x43, Qt.NoModifier, """c""", False, 1), 17.958033 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1), 18.078489 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1), 18.173426 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x53, Qt.NoModifier, """s""", False, 1), 18.18949 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x53, Qt.NoModifier, """s""", False, 1), 18.26906 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1), 19.357822 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1), 19.438386 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x5f, (Qt.ShiftModifier), """_""", False, 1), 19.534273 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1), 19.669269 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x52, Qt.NoModifier, """r""", False, 1), 19.805499 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1), 19.885978 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x52, Qt.NoModifier, """r""", False, 1), 19.917843 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x57, Qt.NoModifier, """w""", False, 1), 19.973055 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1), 20.029443 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x57, Qt.NoModifier, """w""", False, 1), 20.069047 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2e, Qt.NoModifier, """.""", False, 1), 20.309636 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2e, Qt.NoModifier, """.""", False, 1), 20.404478 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4e, Qt.NoModifier, """n""", False, 1), 20.661786 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4e, Qt.NoModifier, """n""", False, 1), 20.725879 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x50, Qt.NoModifier, """p""", False, 1), 20.84632 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x50, Qt.NoModifier, """p""", False, 1), 20.941563 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x59, Qt.NoModifier, """y""", False, 1), 21.053566 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x59, Qt.NoModifier, """y""", False, 1), 21.125069 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000004, Qt.NoModifier, """""", False, 1), 21.22987 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.child_3_DataDetailViewerWidget.appendButton' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000004, Qt.NoModifier, """""", False, 1), 21.427638 )

    ########################
    player.display_comment("""Add \"other\" (wrong file at first)""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_tabbar' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(109, 19), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(427, 53), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 26.002038 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_tabbar' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(109, 19), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(427, 53), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 26.071451 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.appendButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(48, 14), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(368, 164), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 27.50453 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_1' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(48, -18), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(368, 165), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 27.634227 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_1' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(48, -15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(368, 168), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 27.655188 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_1' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(49, -11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(369, 172), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 27.667167 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_1' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(50, -5), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(370, 178), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 27.685541 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_1' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(51, -1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(371, 182), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 27.707671 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_1' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(51, 1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(371, 184), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 27.718854 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_1' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(51, 1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(371, 184), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 27.723697 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_1' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(51, 2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(371, 185), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 28.019097 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_1' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(51, 5), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(371, 188), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 28.035404 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_1' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(51, 6), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(371, 189), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 28.051799 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.addFileButton_role_1' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(51, 6), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(371, 189), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 28.223375 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(132, 31), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(344, 94), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 30.738233 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(132, 31), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(344, 94), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 30.802485 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.buttonBox.child_1_QPushButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(16, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(656, 382), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 31.783912 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.buttonBox.child_1_QPushButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(16, 16), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(656, 383), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 31.815589 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.buttonBox.child_1_QPushButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(16, 16), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(656, 383), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 31.838333 )

    ########################
    player.display_comment("""Replace \"other\" data""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(64, 17), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(403, 99), (Qt.RightButton), (Qt.RightButton), Qt.NoModifier), 36.22812 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QContextMenuEvent(0, PyQt4.QtCore.QPoint(64, 17), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(403, 99), Qt.NoModifier), 36.23245 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(19, 25), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(403, 99), (Qt.RightButton), Qt.NoButton, Qt.NoModifier), 36.348523 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(19, 26), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(403, 100), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 36.674788 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(21, 28), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(405, 102), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 36.686111 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(22, 30), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(406, 104), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 36.704825 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(22, 31), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(406, 105), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 36.724757 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(23, 32), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(407, 106), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 36.737445 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(23, 33), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(407, 107), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 36.774132 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(23, 33), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(407, 107), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 36.91774 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(23, 33), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(407, 107), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 37.007998 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(122, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(334, 71), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 38.913894 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(122, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(334, 71), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 38.989051 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.buttonBox.child_1_QPushButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(34, 19), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(674, 386), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 39.739826 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.buttonBox.child_1_QPushButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(34, 19), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(674, 386), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 39.814453 )

    ########################
    player.display_comment("""Edit \"other\" properties: axis order""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(164, 14), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(503, 96), (Qt.RightButton), (Qt.RightButton), Qt.NoModifier), 43.189934 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QContextMenuEvent(0, PyQt4.QtCore.QPoint(164, 14), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(503, 96), Qt.NoModifier), 43.193777 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_9_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(19, 25), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(503, 96), (Qt.RightButton), Qt.NoButton, Qt.NoModifier), 43.268455 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_9_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(19, 24), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(503, 95), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 43.851377 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_9_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(19, 22), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(503, 93), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 43.860985 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_9_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(20, 21), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(504, 92), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 43.879287 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_9_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(20, 20), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(504, 91), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 43.895433 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_9_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(21, 18), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(505, 89), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 43.916535 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_9_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(21, 18), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(505, 89), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 44.144912 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_9_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(21, 18), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(505, 89), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 44.216065 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(38, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(278, 117), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 45.947208 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(37, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(277, 117), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 45.964065 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(34, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(274, 117), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 45.980244 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(25, 14), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(265, 116), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 45.996536 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(9, 14), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(249, 116), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 46.013392 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(-8, 13), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(232, 115), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 46.037734 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(-23, 13), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(217, 115), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 46.046815 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(-37, 13), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(203, 115), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 46.063946 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(-45, 13), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(195, 115), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 46.081649 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(-45, 13), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(195, 115), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 46.104957 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5a, Qt.NoModifier, """z""", False, 1), 47.0672 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x5a, Qt.NoModifier, """z""", False, 1), 47.130838 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x59, Qt.NoModifier, """y""", False, 1), 47.171635 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x59, Qt.NoModifier, """y""", False, 1), 47.228094 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x58, Qt.NoModifier, """x""", False, 1), 47.539863 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x58, Qt.NoModifier, """x""", False, 1), 47.594842 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.okButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(43, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(640, 369), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 49.319628 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.widget.okButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(43, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(640, 369), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 49.405193 )

    ########################
    player.display_comment("""Edit \"other\" properties again: Choose \"relative link\"""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(95, 22), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(434, 104), (Qt.RightButton), (Qt.RightButton), Qt.NoModifier), 52.882971 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QContextMenuEvent(0, PyQt4.QtCore.QPoint(95, 22), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(434, 104), Qt.NoModifier), 52.887778 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_10_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(19, 25), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(434, 104), (Qt.RightButton), Qt.NoButton, Qt.NoModifier), 52.984592 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_10_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(18, 23), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(433, 102), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 53.824887 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_10_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(18, 22), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(433, 101), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 53.838524 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_10_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(18, 21), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(433, 100), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 53.850863 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_10_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(17, 20), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(432, 99), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 53.949617 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_10_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(12, 20), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(427, 99), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 53.958102 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_10_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(6, 20), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(421, 99), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 53.977471 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_10_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(-32, 19), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(383, 98), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 54.323421 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(66, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(405, 97), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 55.290217 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(66, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(405, 97), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 55.391887 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonDblClick, PyQt4.QtCore.QPoint(66, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(405, 97), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 55.437504 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(66, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(405, 97), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 55.582955 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.child_7_DatasetInfoEditorWidget.widget.storageComboBox' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(96, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(336, 200), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 58.150448 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.child_7_DatasetInfoEditorWidget.widget.storageComboBox.child_1_QFrame' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(96, -8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(336, 201), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 58.223535 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.child_7_DatasetInfoEditorWidget.widget.storageComboBox.child_1_QFrame' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(96, -8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(336, 201), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 58.229485 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.child_7_DatasetInfoEditorWidget.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(89, 0), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(331, 211), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 58.61833 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.child_7_DatasetInfoEditorWidget.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(88, 2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(330, 213), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 58.631144 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.child_7_DatasetInfoEditorWidget.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(88, 5), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(330, 216), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 58.648215 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.child_7_DatasetInfoEditorWidget.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(87, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(329, 219), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 58.661844 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.child_7_DatasetInfoEditorWidget.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(85, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(327, 222), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 58.68114 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.child_7_DatasetInfoEditorWidget.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(84, 13), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(326, 224), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 58.696087 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.child_7_DatasetInfoEditorWidget.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(83, 14), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(325, 225), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 58.712773 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.child_7_DatasetInfoEditorWidget.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(82, 16), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(324, 227), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 58.729015 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.child_7_DatasetInfoEditorWidget.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(81, 20), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(323, 231), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 58.744915 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.child_7_DatasetInfoEditorWidget.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(80, 22), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(322, 233), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 58.762035 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.child_7_DatasetInfoEditorWidget.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(80, 24), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(322, 235), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 58.792604 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.child_7_DatasetInfoEditorWidget.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(79, 25), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(321, 236), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 58.805034 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.child_7_DatasetInfoEditorWidget.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(79, 26), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(321, 237), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 58.819701 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.child_7_DatasetInfoEditorWidget.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(78, 27), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(320, 238), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 58.829684 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.child_7_DatasetInfoEditorWidget.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(78, 28), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(320, 239), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 58.874602 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.child_7_DatasetInfoEditorWidget.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(77, 29), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(319, 240), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 58.885301 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.child_7_DatasetInfoEditorWidget.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(76, 29), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(318, 240), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 58.896516 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.child_7_DatasetInfoEditorWidget.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(76, 30), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(318, 241), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 58.913226 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.child_7_DatasetInfoEditorWidget.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(76, 31), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(318, 242), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 58.946416 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.child_7_DatasetInfoEditorWidget.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(75, 32), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(317, 243), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 58.967835 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.child_7_DatasetInfoEditorWidget.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(74, 33), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(316, 244), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 58.978227 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.child_7_DatasetInfoEditorWidget.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(73, 34), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(315, 245), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 59.028441 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.child_7_DatasetInfoEditorWidget.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(73, 35), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(315, 246), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 59.082833 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.child_7_DatasetInfoEditorWidget.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(73, 35), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(315, 246), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 59.149642 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.child_7_DatasetInfoEditorWidget.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(73, 35), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(315, 246), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 59.254608 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.child_7_DatasetInfoEditorWidget.widget.okButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(31, 18), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(628, 379), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 61.875317 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.child_7_DatasetInfoEditorWidget.widget.okButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(31, 18), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(628, 379), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 62.868403 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_4_QHeaderView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(200, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(539, 67), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 65.697732 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_4_QHeaderView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(200, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(539, 67), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 65.814476 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_4_QHeaderView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonDblClick, PyQt4.QtCore.QPoint(200, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(539, 67), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 65.860727 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_4_QHeaderView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(200, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(539, 67), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 65.982111 )

    ########################
    player.display_comment("""Edit \"raw\" properties: Copy to project""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_tabbar' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(50, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(368, 42), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 70.843233 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_tabbar' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(50, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(368, 42), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 70.97322 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.child_3_DataDetailViewerWidget.datasetDetailTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(35, 17), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(374, 99), (Qt.RightButton), (Qt.RightButton), Qt.NoModifier), 76.360976 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.child_3_DataDetailViewerWidget.datasetDetailTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QContextMenuEvent(0, PyQt4.QtCore.QPoint(35, 17), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(374, 99), Qt.NoModifier), 76.3678 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.child_3_DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(19, 25), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(374, 99), (Qt.RightButton), Qt.NoButton, Qt.NoModifier), 76.453734 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.child_3_DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(22, 25), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(377, 99), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 76.758054 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.child_3_DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(28, 23), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(383, 97), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 76.776334 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.child_3_DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(32, 22), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(387, 96), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 76.786868 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.child_3_DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(35, 21), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(390, 95), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 76.806086 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.child_3_DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(36, 20), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(391, 94), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 76.820813 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.child_3_DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(38, 19), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(393, 93), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 76.858261 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.child_3_DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(38, 19), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(393, 93), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 76.971227 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.child_3_DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(38, 19), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(393, 93), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 77.022015 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.widget.storageComboBox' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(119, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(359, 199), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 78.557019 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.widget.storageComboBox.child_1_QFrame' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(119, -10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(359, 199), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 78.663313 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(113, 1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(355, 212), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 79.059954 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(113, 1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(355, 212), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 79.213087 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.widget.storageComboBox.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(113, 1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(355, 212), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 79.316726 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.widget.okButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(57, 13), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(654, 374), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 80.297908 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.widget.okButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(57, 13), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(654, 374), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 80.385512 )

    ########################
    player.display_comment("""Save Project""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.child_3_DataDetailViewerWidget.datasetDetailTableView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000021, (Qt.ControlModifier), """""", False, 1), 88.325033 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(267, 49), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(274, 76), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 88.409401 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(264, 52), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(271, 79), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 88.423303 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(264, 53), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(271, 80), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 88.443038 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.child_3_DataDetailViewerWidget.datasetDetailTableView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x53, (Qt.ControlModifier), """""", False, 1), 88.461715 )

    obj = get_named_object( 'MainWindow' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x53, (Qt.ControlModifier), """""", False, 1), 88.727751 )

    obj = get_named_object( 'MainWindow' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000021, Qt.NoModifier, """""", False, 1), 88.805584 )

    player.display_comment("SCRIPT COMPLETE")
