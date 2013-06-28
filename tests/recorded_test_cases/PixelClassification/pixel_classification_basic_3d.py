
# Event Recording
# Started at: 2013-06-25 14:55:49.596572

def playback_events(player):
    import PyQt4.QtCore
    from PyQt4.QtCore import Qt, QEvent, QPoint
    import PyQt4.QtGui
    from ilastik.utility.gui.eventRecorder.objectNameUtils import get_named_object
    from ilastik.utility.gui.eventRecorder.eventRecorder import EventPlayer
    from ilastik.shell.gui.startShellGui import shell    

    player.display_comment("SCRIPT STARTING")


    ########################
    player.display_comment("""New Project (Pixel Classification)""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.startupPage.frame.CreateList.qt_scrollarea_viewport.scrollAreaWidgetContents.child_2_QToolButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(176, 6), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(487, 211), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 0.850745 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.startupPage.frame.CreateList.qt_scrollarea_viewport.scrollAreaWidgetContents.child_2_QToolButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(176, 6), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(487, 211), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 1.048123 )

    obj = get_named_object( 'MainWindow.QFileDialog.fileNameEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000005, (Qt.KeypadModifier), """""", False, 1), 4.172158 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_4_QScrollArea' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000005, (Qt.KeypadModifier), """""", False, 1), 4.597749 )

    ########################
    player.display_comment("""Select Input Data (3D)""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.appendButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(55, 22), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(375, 142), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 9.843644 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(55, -11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(375, 142), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 9.965246 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(62, -2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(382, 151), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 11.657604 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(63, 1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(383, 154), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 11.671863 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(63, 3), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(383, 156), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 11.683636 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(63, 4), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(383, 157), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 11.695004 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(64, 5), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(384, 158), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 11.727262 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(64, 6), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(384, 159), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 11.741511 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(64, 7), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(384, 160), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 11.748468 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(64, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(384, 161), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 11.76826 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(64, 9), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(384, 162), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 11.783849 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(64, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(384, 163), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 11.935948 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(64, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(384, 164), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 11.951944 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(64, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(384, 164), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 12.027307 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(64, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(384, 164), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 12.187776 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2f, Qt.NoModifier, """/""", False, 1), 13.64012 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2f, Qt.NoModifier, """/""", False, 1), 13.779594 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1), 13.824207 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4d, Qt.NoModifier, """m""", False, 1), 13.86558 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1), 13.936118 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4d, Qt.NoModifier, """m""", False, 1), 13.952054 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x50, Qt.NoModifier, """p""", False, 1), 13.983912 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x50, Qt.NoModifier, """p""", False, 1), 14.071745 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2f, Qt.NoModifier, """/""", False, 1), 14.176235 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2f, Qt.NoModifier, """/""", False, 1), 14.305045 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1), 14.328711 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1), 14.392885 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1), 14.456307 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1), 14.472514 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x53, Qt.NoModifier, """s""", False, 1), 14.544218 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1), 14.592117 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x53, Qt.NoModifier, """s""", False, 1), 14.633061 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1), 14.688084 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1), 14.735759 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1), 14.856291 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1), 14.952011 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2d, Qt.NoModifier, """-""", False, 1), 14.960153 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x44, Qt.NoModifier, """d""", False, 1), 14.983933 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x44, Qt.NoModifier, """d""", False, 1), 15.07171 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1), 15.080035 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1), 15.136241 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1), 15.151903 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1), 15.216027 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1), 15.263695 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1), 15.312513 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2f, Qt.NoModifier, """/""", False, 1), 15.312658 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2f, Qt.NoModifier, """/""", False, 1), 15.424366 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x52, Qt.NoModifier, """r""", False, 1), 16.400587 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x52, Qt.NoModifier, """r""", False, 1), 16.488599 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1), 16.496448 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4e, Qt.NoModifier, """n""", False, 1), 16.599989 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1), 16.609943 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4e, Qt.NoModifier, """n""", False, 1), 16.696449 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x44, Qt.NoModifier, """d""", False, 1), 17.040628 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x44, Qt.NoModifier, """d""", False, 1), 17.12012 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1), 17.24065 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1), 17.35238 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x5f, (Qt.ShiftModifier), """_""", False, 1), 17.432053 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1), 17.488596 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x55, Qt.NoModifier, """u""", False, 1), 17.560537 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x49, Qt.NoModifier, """i""", False, 1), 17.631764 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x55, Qt.NoModifier, """u""", False, 1), 17.680371 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x49, Qt.NoModifier, """i""", False, 1), 17.727997 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4e, Qt.NoModifier, """n""", False, 1), 17.768132 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x42, Qt.NoModifier, """b""", False, 1), 17.77817 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x42, Qt.NoModifier, """b""", False, 1), 17.823931 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1), 17.832413 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4e, Qt.NoModifier, """n""", False, 1), 17.87178 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1), 17.920545 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000003, Qt.NoModifier, """""", False, 1), 18.895922 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000003, Qt.NoModifier, """""", False, 1), 18.936393 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000003, Qt.NoModifier, """""", False, 1), 19.000114 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000003, Qt.NoModifier, """""", False, 1), 19.096392 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1), 19.224558 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1), 19.264181 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x38, Qt.NoModifier, """8""", False, 1), 19.976068 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x38, Qt.NoModifier, """8""", False, 1), 20.063718 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1), 20.976203 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1), 21.016019 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1), 21.112307 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2d, Qt.NoModifier, """-""", False, 1), 21.128102 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x33, Qt.NoModifier, """3""", False, 1), 21.431983 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x33, Qt.NoModifier, """3""", False, 1), 21.495902 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x44, Qt.NoModifier, """d""", False, 1), 21.600327 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x44, Qt.NoModifier, """d""", False, 1), 21.66382 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2e, Qt.NoModifier, """.""", False, 1), 21.672065 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2e, Qt.NoModifier, """.""", False, 1), 21.791807 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4e, Qt.NoModifier, """n""", False, 1), 21.855888 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4e, Qt.NoModifier, """n""", False, 1), 21.928397 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x50, Qt.NoModifier, """p""", False, 1), 22.00004 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x50, Qt.NoModifier, """p""", False, 1), 22.071747 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x59, Qt.NoModifier, """y""", False, 1), 22.144666 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x59, Qt.NoModifier, """y""", False, 1), 22.216393 )

    obj = get_named_object( 'QListView' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000004, Qt.NoModifier, """""", False, 1), 22.408168 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.appendButton' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000004, Qt.NoModifier, """""", False, 1), 22.912564 )

    ########################
    player.display_comment("""Select Features""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_5_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(135, 18), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(141, 348), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 27.288389 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_5_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(135, 18), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(141, 348), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 27.360345 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_6_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.Form.SelectFeaturesButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(198, 13), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(204, 141), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 28.944159 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_6_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.Form.SelectFeaturesButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(198, 13), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(204, 141), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 29.115452 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.Dialog.featureTableWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(35, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(487, 68), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 31.926117 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.Dialog.featureTableWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(35, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(487, 68), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 32.065279 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.Dialog.featureTableWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(83, 39), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(535, 95), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 35.904046 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.Dialog.featureTableWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(83, 39), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(535, 95), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 36.026451 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.Dialog.featureTableWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(140, 62), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(592, 118), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 36.686416 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.Dialog.featureTableWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(140, 62), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(592, 118), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 36.793682 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.Dialog.ok' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(35, 6), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(676, 316), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 37.906156 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.Dialog.ok' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(35, 6), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(676, 316), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 38.024329 )

    ########################
    player.display_comment("""Browse features""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_2_lane_0.viewerControls.featureListWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(148, 25), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(164, 502), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 42.840848 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_2_lane_0.viewerControls.featureListWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(148, 25), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(164, 502), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 42.996585 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_2_lane_0.viewerControls.featureListWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(152, 54), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(168, 531), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 43.686194 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_2_lane_0.viewerControls.featureListWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(152, 54), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(168, 531), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 43.971037 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_2_lane_0.viewerControls.featureListWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(154, 40), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(170, 517), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 44.697326 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_2_lane_0.viewerControls.featureListWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(154, 40), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(170, 517), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 44.828841 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_2_lane_0.viewerControls.featureListWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(153, 68), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(169, 545), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 45.720415 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_2_lane_0.viewerControls.featureListWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(153, 68), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(169, 545), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 45.909351 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_2_lane_0.viewerControls.featureListWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(149, 96), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(165, 573), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 46.632148 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_2_lane_0.viewerControls.featureListWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(149, 96), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(165, 573), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 46.829402 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_2_lane_0.viewerControls.featureListWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(149, 81), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(165, 558), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 47.608497 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_2_lane_0.viewerControls.featureListWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(149, 81), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(165, 558), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 47.739335 )

    ########################
    player.display_comment("""Open Training tab""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(115, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(121, 370), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 50.672635 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(115, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(121, 370), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 50.758492 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.AddLabelButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(184, 13), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(199, 276), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 53.561096 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.AddLabelButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(184, 13), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(199, 276), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 53.679874 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.AddLabelButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(182, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(197, 278), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 54.703788 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.AddLabelButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(182, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(197, 278), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 54.952215 )

    ########################
    player.display_comment("""Added labels, now drawing...""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.child_2_QTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(156, 20), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(173, 173), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 59.428855 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.child_2_QTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(156, 20), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(173, 173), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 59.507656 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(179, 173), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(490, 200), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 60.935586 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(179, 174), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(490, 201), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 61.022804 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(186, 184), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(497, 211), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 61.0464 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(190, 191), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(501, 218), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 61.090494 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(193, 199), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(504, 226), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 61.11438 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(194, 201), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(505, 228), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 61.132105 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(195, 201), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(506, 228), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 61.178234 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(195, 202), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(506, 229), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 61.1947 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(195, 202), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(506, 229), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 61.932945 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000021, (Qt.ControlModifier), """""", False, 1), 64.3671 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(189, 216), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(500, 243), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 64.387702 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(187, 218), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(498, 245), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 64.404934 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(175, 221), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(486, 248), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 64.458507 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(122, 222), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(433, 249), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 64.476214 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(109, 222), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(420, 249), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 64.496495 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(100, 221), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(411, 248), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 64.584801 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(98, 221), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(409, 248), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 64.609971 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(99, 220), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(410, 247), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 64.654637 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(108, 218), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(419, 245), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 64.683097 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(114, 218), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(425, 245), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 64.701249 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(119, 218), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(430, 245), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 64.716759 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(121, 218), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(432, 245), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 64.736218 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(121, 217), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(432, 244), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 64.754592 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(121, 217), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(432, 244), 120, Qt.NoButton, (Qt.ControlModifier), 2), 65.871121 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(121, 217), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(432, 244), 120, Qt.NoButton, (Qt.ControlModifier), 2), 65.893348 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(121, 217), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(432, 244), 120, Qt.NoButton, (Qt.ControlModifier), 2), 65.986746 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(121, 217), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(432, 244), 480, Qt.NoButton, (Qt.ControlModifier), 2), 66.011071 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(121, 217), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(432, 244), -120, Qt.NoButton, (Qt.ControlModifier), 2), 66.133068 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(121, 217), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(432, 244), 120, Qt.NoButton, (Qt.ControlModifier), 2), 66.350106 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(121, 217), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(432, 244), 120, Qt.NoButton, (Qt.ControlModifier), 2), 66.463828 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(121, 217), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(432, 244), 120, Qt.NoButton, (Qt.ControlModifier), 2), 66.49413 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(121, 217), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(432, 244), 120, Qt.NoButton, (Qt.ControlModifier), 2), 66.6077 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(121, 217), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(432, 244), 240, Qt.NoButton, (Qt.ControlModifier), 2), 66.665522 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(121, 217), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(432, 244), 120, Qt.NoButton, (Qt.ControlModifier), 2), 66.886076 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(121, 217), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(432, 244), 120, Qt.NoButton, (Qt.ControlModifier), 2), 67.357948 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000021, Qt.NoModifier, """""", False, 1), 68.577549 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.child_2_QTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(166, 43), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(183, 196), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 69.27257 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.child_2_QTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(166, 43), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(183, 196), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 69.367173 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(315, 100), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(626, 127), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 71.134288 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(315, 101), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(626, 128), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 71.213876 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(310, 111), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(621, 138), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 71.234457 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(301, 121), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(612, 148), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 71.253485 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(291, 135), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(602, 162), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 71.323395 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(271, 166), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(582, 193), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 71.34252 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(267, 173), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(578, 200), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 71.363271 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(265, 177), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(576, 204), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 71.416153 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(261, 181), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(572, 208), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 71.436019 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(261, 183), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(572, 210), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 71.454805 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(259, 184), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(570, 211), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 71.563627 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(259, 186), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(570, 213), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 71.587204 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(258, 186), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(569, 213), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 71.605355 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(258, 186), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(569, 213), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 71.901449 )

    ########################
    player.display_comment("""Live update!""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.liveUpdateButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(137, 18), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(152, 337), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 74.938508 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.liveUpdateButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(137, 18), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(152, 337), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 75.113574 )

    ########################
    player.display_comment("""Add more labels""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(102, 235), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(413, 262), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 85.815185 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(102, 234), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(413, 261), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 85.950426 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(103, 241), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(414, 268), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 85.977537 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(105, 249), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(416, 276), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 86.055508 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(110, 261), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(421, 288), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 86.07605 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(111, 265), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(422, 292), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 86.092941 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(114, 269), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(425, 296), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 86.163053 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(123, 281), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(434, 308), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 86.186446 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(129, 285), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(440, 312), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 86.208952 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(134, 289), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(445, 316), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 86.279697 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(150, 300), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(461, 327), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 86.296911 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(155, 302), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(466, 329), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 86.313942 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(161, 305), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(472, 332), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 86.383768 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(192, 317), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(503, 344), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 86.426017 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(199, 318), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(510, 345), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 86.4504 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(208, 319), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(519, 346), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 86.529545 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(235, 320), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(546, 347), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 86.558214 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(242, 320), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(553, 347), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 86.578951 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(256, 317), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(567, 344), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 86.663088 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(272, 312), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(583, 339), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 86.688914 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(276, 309), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 336), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 86.717054 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(286, 303), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(597, 330), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 86.807692 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(298, 289), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(609, 316), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 86.837568 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(301, 283), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(612, 310), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 86.866558 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(303, 277), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(614, 304), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 86.937591 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(308, 259), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(619, 286), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 86.967789 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(309, 254), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(620, 281), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 86.992349 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(310, 249), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(621, 276), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 87.062627 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(311, 235), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(622, 262), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 87.085494 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(311, 231), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(622, 258), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 87.100716 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(312, 226), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(623, 253), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 87.168841 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(313, 218), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(624, 245), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 87.18919 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(313, 216), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(624, 243), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 87.214575 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(314, 213), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(625, 240), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 87.316292 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(314, 208), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(625, 235), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 87.34157 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(314, 208), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(625, 235), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 87.936919 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.child_2_QTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(65, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(82, 168), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 93.505137 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.child_2_QTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(65, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(82, 168), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 93.631735 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(189, 225), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(500, 252), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 96.986347 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(189, 224), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(500, 251), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 97.096543 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(189, 219), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(500, 246), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 97.118008 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(191, 210), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(502, 237), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 97.175901 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(198, 190), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(509, 217), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 97.197822 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(201, 186), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(512, 213), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 97.220381 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(202, 183), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(513, 210), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 97.325144 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(202, 182), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(513, 209), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 97.348299 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(203, 184), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(514, 211), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 97.415559 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(207, 191), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(518, 218), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 97.435632 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(214, 203), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(525, 230), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 97.501731 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(226, 221), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(537, 248), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 97.519113 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(229, 227), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(540, 254), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 97.540295 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(234, 235), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(545, 262), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 97.614744 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(240, 243), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(551, 270), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 97.64267 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(242, 245), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(553, 272), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 97.663332 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(242, 246), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(553, 273), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 97.765335 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(242, 246), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(553, 273), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 97.905618 )

    ########################
    player.display_comment("""Turn off live update""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.liveUpdateButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(157, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(172, 327), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 102.813242 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.liveUpdateButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(157, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(172, 327), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 102.898743 )

    ########################
    player.display_comment("""Full Volume Predict""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.savePredictionsButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(120, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(135, 358), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 105.035366 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.savePredictionsButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(120, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(135, 358), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 105.139738 )

    obj = get_named_object( 'MainWindow.child_7_QMenuBar' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(23, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(23, 10), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 114.092033 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(23, -9), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(23, 10), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 114.207246 )

    obj = get_named_object( 'MainWindow.child_7_QMenuBar' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(25, 13), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(29, 21), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 114.459639 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(27, -2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(27, 17), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 114.472523 )

    obj = get_named_object( 'MainWindow.child_7_QMenuBar' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(27, 17), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(35, 36), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 114.485443 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(29, 2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(29, 21), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 114.498513 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(42, 40), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(42, 59), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 114.504672 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(45, 49), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(45, 68), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 114.515048 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(49, 59), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(49, 78), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 114.526165 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(53, 78), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(53, 97), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 114.539614 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(56, 96), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(56, 115), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 114.554621 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(59, 110), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(59, 129), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 114.573686 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(61, 120), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(61, 139), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 114.593455 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(62, 126), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(62, 145), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 114.616626 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(63, 128), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(63, 147), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 114.634074 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(63, 129), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(63, 148), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 114.654831 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(63, 131), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(63, 150), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 114.667972 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(63, 132), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(63, 151), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 114.680559 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(63, 133), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(63, 152), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 114.692921 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(63, 134), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(63, 153), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 114.773381 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(63, 135), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(63, 154), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 114.781018 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(63, 137), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(63, 156), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 114.790367 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(62, 139), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(62, 158), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 114.797451 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(62, 141), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(62, 160), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 114.80539 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(62, 143), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(62, 162), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 114.817785 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(61, 146), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(61, 165), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 114.83392 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(61, 147), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(61, 166), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 114.851696 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(60, 151), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(60, 170), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 114.863489 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(60, 153), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(60, 172), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 114.870431 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(60, 155), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(60, 174), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 114.886653 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(59, 158), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(59, 177), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 114.900548 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(58, 159), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(58, 178), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 114.916243 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(58, 160), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(58, 179), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 114.99882 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(57, 161), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(57, 180), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 115.015893 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(57, 162), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(57, 181), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 115.193942 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(57, 162), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(57, 181), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 115.597548 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(58, 159), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(58, 178), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 116.293059 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(61, 154), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(61, 173), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 116.306836 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(62, 148), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(62, 167), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 116.316297 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(65, 141), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(65, 160), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 116.323445 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(68, 135), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(68, 154), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 116.329798 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(70, 125), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(70, 144), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 116.339741 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(77, 100), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(77, 119), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 116.34865 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(81, 85), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(81, 104), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 116.361243 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(85, 70), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(85, 89), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 116.380069 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(95, 33), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(95, 52), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 116.394011 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(98, 23), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(98, 42), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 116.403785 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(104, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(104, 27), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 116.430278 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(106, 1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(106, 20), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 116.439829 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(108, -4), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(108, 15), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 116.45402 )

    obj = get_named_object( 'MainWindow.child_7_QMenuBar' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(108, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(114, 2), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 116.469976 )

    obj = get_named_object( 'MainWindow.settings_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(54, -4), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(108, 15), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 116.518891 )

    obj = get_named_object( 'MainWindow.child_7_QMenuBar' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(108, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(120, -7), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 116.524844 )

    obj = get_named_object( 'MainWindow.settings_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(62, -18), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(116, 1), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 116.542505 )

    obj = get_named_object( 'MainWindow.child_7_QMenuBar' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(116, 1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(121, -8), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 116.548849 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.view_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(0, -21), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(116, -2), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 116.635842 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.view_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(6, -27), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(122, -8), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 116.66115 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.view_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(9, -33), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(125, -14), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 116.737481 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.view_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(9, -34), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(125, -15), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 116.780578 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.view_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(9, -34), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(125, -15), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 116.900773 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.view_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(45, -141), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(161, -122), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 117.549723 )

    player.display_comment("SCRIPT COMPLETE")
