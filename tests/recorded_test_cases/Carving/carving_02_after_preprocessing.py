
# Event Recording
# Created by Stuart
# Started at: 2014-02-18 19:53:38.335670

def playback_events(player):
    import PyQt4.QtCore
    from PyQt4.QtCore import Qt, QEvent, QPoint
    import PyQt4.QtGui
    
    # The getMainWindow() function is provided by EventRecorderApp
    mainwin = PyQt4.QtGui.QApplication.instance().getMainWindow()

    player.display_comment("SCRIPT STARTING")


    ########################
    player.display_comment("""In this recording we\'ll OPEN (not create) a previously created carving project that already has preprocessing data in it.""")
    ########################

    ########################
    player.display_comment("""Then we\'ll try to carve with it.""")
    ########################

    ########################
    player.display_comment("""Open Project....""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(267, 2), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(267, 2), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 1.847191 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(250, 3), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(250, 3), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 1.899606 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(107, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(107, 0), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 2.146573 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(83, 5), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(83, 5), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 2.19716 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(63, 8), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(63, 8), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 2.246447 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(61, 10), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(61, 10), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 2.297925 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(52, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(52, 12), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 2.347967 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(43, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(43, 12), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 2.400108 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(25, 13), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(25, 13), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 2.45025 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(25, 13), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(25, 13), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 2.548118 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(25, -6), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(25, 13), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.project_menu', event , 2.598387 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(24, -5), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(24, 14), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.project_menu', event , 3.189667 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(24, 14), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(28, 19), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 3.23668 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(26, -2), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(26, 17), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.project_menu', event , 3.282812 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(26, 17), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(34, 30), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 3.327501 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(28, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(28, 19), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.project_menu', event , 3.373292 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(34, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(34, 31), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.project_menu', event , 3.418907 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(34, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(34, 31), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.project_menu', event , 3.474749 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(34, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(34, 31), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.project_menu', event , 3.554109 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1)
    player.post_event( 'MainWindow.QFileDialog.fileNameEdit', event , 8.079515 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4d, (Qt.ShiftModifier), """M""", False, 1)
    player.post_event( 'MainWindow.QFileDialog.fileNameEdit', event , 8.116344 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4d, (Qt.ShiftModifier), """M""", False, 1)
    player.post_event( 'MainWindow.QFileDialog.fileNameEdit', event , 8.168458 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.QFileDialog.fileNameEdit', event , 8.213105 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x59, Qt.NoModifier, """y""", False, 1)
    player.post_event( 'MainWindow.QFileDialog.fileNameEdit', event , 8.295598 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x59, Qt.NoModifier, """y""", False, 1)
    player.post_event( 'MainWindow.QFileDialog.fileNameEdit', event , 8.350317 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1)
    player.post_event( 'MainWindow.QFileDialog.fileNameEdit', event , 8.549218 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x50, (Qt.ShiftModifier), """P""", False, 1)
    player.post_event( 'MainWindow.QFileDialog.fileNameEdit', event , 8.62249 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.QFileDialog.fileNameEdit', event , 8.6839 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x50, Qt.NoModifier, """p""", False, 1)
    player.post_event( 'MainWindow.QFileDialog.fileNameEdit', event , 8.729574 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x52, Qt.NoModifier, """r""", False, 1)
    player.post_event( 'MainWindow.QFileDialog.fileNameEdit', event , 8.77339 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4f, Qt.NoModifier, """o""", False, 1)
    player.post_event( 'MainWindow.QFileDialog.fileNameEdit', event , 8.817841 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x52, Qt.NoModifier, """r""", False, 1)
    player.post_event( 'MainWindow.QFileDialog.fileNameEdit', event , 8.86201 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4f, Qt.NoModifier, """o""", False, 1)
    player.post_event( 'MainWindow.QFileDialog.fileNameEdit', event , 8.907335 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4a, Qt.NoModifier, """j""", False, 1)
    player.post_event( 'MainWindow.QFileDialog.fileNameEdit', event , 8.951114 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'MainWindow.QFileDialog.fileNameEdit', event , 8.995128 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x43, Qt.NoModifier, """c""", False, 1)
    player.post_event( 'MainWindow.QFileDialog.fileNameEdit', event , 9.041144 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'MainWindow.QFileDialog.fileNameEdit', event , 9.08534 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x43, Qt.NoModifier, """c""", False, 1)
    player.post_event( 'MainWindow.QFileDialog.fileNameEdit', event , 9.129225 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4a, Qt.NoModifier, """j""", False, 1)
    player.post_event( 'MainWindow.QFileDialog.fileNameEdit', event , 9.171908 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.QFileDialog.fileNameEdit', event , 9.217997 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.QFileDialog.fileNameEdit', event , 9.263122 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2e, Qt.NoModifier, """.""", False, 1)
    player.post_event( 'MainWindow.QFileDialog.fileNameEdit', event , 9.406047 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2e, Qt.NoModifier, """.""", False, 1)
    player.post_event( 'MainWindow.QFileDialog.fileNameEdit', event , 9.46944 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x49, Qt.NoModifier, """i""", False, 1)
    player.post_event( 'MainWindow.QFileDialog.fileNameEdit', event , 9.57488 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4c, Qt.NoModifier, """l""", False, 1)
    player.post_event( 'MainWindow.QFileDialog.fileNameEdit', event , 9.645926 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x49, Qt.NoModifier, """i""", False, 1)
    player.post_event( 'MainWindow.QFileDialog.fileNameEdit', event , 9.690914 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4c, Qt.NoModifier, """l""", False, 1)
    player.post_event( 'MainWindow.QFileDialog.fileNameEdit', event , 9.735499 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x50, Qt.NoModifier, """p""", False, 1)
    player.post_event( 'MainWindow.QFileDialog.fileNameEdit', event , 9.777921 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x50, Qt.NoModifier, """p""", False, 1)
    player.post_event( 'MainWindow.QFileDialog.fileNameEdit', event , 9.852994 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000005, (Qt.KeypadModifier), """""", False, 1)
    player.post_event( 'MainWindow.QFileDialog.fileNameEdit', event , 11.414896 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000005, (Qt.KeypadModifier), """""", False, 1)
    player.post_event( 'MainWindow.QFileDialog', event , 11.471418 )

    ########################
    player.display_comment("""Open labeling applet""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(363, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(363, 0), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 14.237212 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(134, 9), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(140, 426), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QAbstractButton_2', event , 15.438309 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(134, 9), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(140, 426), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QAbstractButton_2', event , 15.536165 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(70, 7), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(85, 354), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.label_8', event , 19.894586 )

    ########################
    player.display_comment("""Draw some labels""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(443, 3), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(443, 3), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 20.857758 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(83, 37), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(394, 64), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 20.937238 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(46, 60), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(357, 87), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 21.036466 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(41, 62), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(352, 89), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 21.1743 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(16, 172), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(327, 199), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 21.27956 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(161, 174), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(472, 201), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 21.373295 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(193, 197), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(504, 224), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 21.470271 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(204, 229), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(515, 256), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 21.56354 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(206, 230), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(517, 257), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 21.659005 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(205, 230), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(516, 257), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 21.749734 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(206, 230), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(517, 257), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 21.951496 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(217, 226), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(528, 253), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 22.037239 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(218, 225), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(529, 252), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 22.210488 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(226, 223), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(537, 250), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 22.294515 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(228, 222), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(539, 249), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 22.399053 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(229, 222), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(540, 249), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 22.728589 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(230, 223), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(541, 250), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 22.827322 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(232, 224), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(543, 251), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 22.917126 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(232, 224), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(543, 251), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 23.179058 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(232, 225), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(543, 252), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 23.298417 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(226, 229), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(537, 256), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 23.385298 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(218, 233), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(529, 260), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 23.487231 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(216, 233), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(527, 260), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 23.566821 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(215, 233), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(526, 260), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 23.66591 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(215, 233), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(526, 260), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 23.969109 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(210, 233), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(521, 260), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 24.618743 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(98, 216), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(409, 243), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 24.717082 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(76, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(93, 206), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.QTableView_0.qt_scrollarea_viewport', event , 25.498945 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(76, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(93, 206), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.QTableView_0.qt_scrollarea_viewport', event , 25.590886 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(6, 186), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(317, 213), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 26.312013 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(79, 196), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(390, 223), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 26.396541 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(130, 199), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(441, 226), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 26.486893 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(152, 199), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(463, 226), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 26.585268 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(160, 199), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(471, 226), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 26.67476 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(192, 208), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(503, 235), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 26.773521 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(200, 208), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(511, 235), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 26.862403 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(203, 206), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(514, 233), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 27.163839 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(200, 201), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(511, 228), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 27.249753 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(200, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(511, 220), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 27.342109 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(200, 187), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(511, 214), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 27.437632 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(200, 188), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(511, 215), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 27.667882 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(200, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(511, 220), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 27.752488 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(200, 192), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(511, 219), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 27.995203 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(197, 180), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(508, 207), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 28.096347 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(193, 179), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(504, 206), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 28.20082 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(189, 177), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(500, 204), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 28.312294 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(187, 177), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(498, 204), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 28.409295 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(187, 176), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(498, 203), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 28.513194 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(185, 176), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(496, 203), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 28.605738 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(185, 176), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(496, 203), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 28.70407 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(183, 176), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(494, 203), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 28.799664 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(177, 175), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(488, 202), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 28.891617 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(173, 174), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(484, 201), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 28.982219 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(173, 174), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(484, 201), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 29.121901 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(171, 174), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(482, 201), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 30.739235 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(8, 177), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(319, 204), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 30.825389 )

    ########################
    player.display_comment("""Hit \"Segment\"""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(366, 6), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(366, 6), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 31.558882 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(71, 4), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(86, 351), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.label_8', event , 31.997254 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(73, 10), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(88, 378), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.segment', event , 32.393954 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(73, 10), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(88, 378), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.segment', event , 32.494707 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(37, 3), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(52, 350), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.label_8', event , 35.616329 )

    ########################
    player.display_comment("""That looks terrible... try to fix it.""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(347, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(347, 0), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 36.717602 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(23, 29), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(334, 56), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 36.851127 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(9, 48), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(320, 75), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 36.952111 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(1, 156), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(312, 183), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 37.163196 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(151, 201), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(462, 228), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 37.247196 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(171, 205), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(482, 232), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 37.348934 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(171, 202), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(482, 229), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 37.433207 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(162, 172), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(473, 199), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 37.526504 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(159, 162), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(470, 189), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 37.619421 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(163, 162), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(474, 189), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 37.71003 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(175, 167), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(486, 194), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 37.810633 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(183, 171), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(494, 198), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 37.901002 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(195, 176), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(506, 203), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 37.997169 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(205, 177), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(516, 204), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 38.092838 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(205, 183), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(516, 210), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 38.178273 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(205, 185), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(516, 212), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 38.280748 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(205, 187), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(516, 214), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 38.460765 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(204, 187), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(515, 214), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 38.545562 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(204, 189), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(515, 216), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 38.647742 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(203, 191), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(514, 218), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 38.735172 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(203, 191), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(514, 218), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 38.832273 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(180, 209), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(491, 236), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 38.930897 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(176, 211), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(487, 238), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 39.010666 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(175, 212), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(486, 239), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 39.113747 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(175, 212), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(486, 239), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 39.239024 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(174, 212), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(485, 239), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 39.610273 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(167, 212), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(478, 239), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 39.694829 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(166, 212), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(477, 239), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 40.110824 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(121, 212), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(432, 239), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 40.208743 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(121, 1), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(136, 348), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.label_8', event , 40.596508 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(103, 15), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(118, 383), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.segment', event , 40.924166 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(103, 15), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(118, 383), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.segment', event , 41.023693 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(17, 286), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(328, 313), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 41.734932 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(67, 274), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(378, 301), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 41.834817 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(76, 274), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(387, 301), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 41.92031 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(78, 273), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(389, 300), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 42.022912 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(107, 244), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(418, 271), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 42.109287 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(128, 222), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(439, 249), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 42.197785 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(136, 220), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(447, 247), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 42.298661 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(132, 221), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(443, 248), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 42.39213 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(128, 221), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(439, 248), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 42.485631 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(126, 221), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(437, 248), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 42.735471 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(126, 222), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(437, 249), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 42.823196 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(125, 222), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(436, 249), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 42.927003 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(122, 222), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(433, 249), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 45.963899 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(38, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(53, 183), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.label', event , 46.097935 )

    ########################
    player.display_comment("""That looks better""")
    ########################

    ########################
    player.display_comment("""Scroll a bit...""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(465, 10), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(465, 10), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 46.573858 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(162, 151), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(473, 178), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 46.659933 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(188, 257), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(499, 284), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 46.747989 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(185, 254), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(496, 281), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 46.843329 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(186, 252), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(497, 279), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 46.937422 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(191, 249), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(502, 276), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 47.021987 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(191, 248), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(502, 275), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 47.122534 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(191, 248), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(502, 275), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 47.405495 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(191, 248), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(502, 275), 1680, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 47.548352 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(191, 248), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(502, 275), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 50.341169 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(191, 248), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(502, 275), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 50.517494 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(191, 248), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(502, 275), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 51.118389 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(191, 248), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(502, 275), -240, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 51.254068 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(191, 248), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(502, 275), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 51.711046 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(191, 248), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(502, 275), -600, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 51.903277 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(191, 248), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(502, 275), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 52.385476 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(191, 248), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(502, 275), -240, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 52.521514 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(191, 248), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(502, 275), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 53.055365 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(191, 248), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(502, 275), -360, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 53.189621 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(191, 248), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(502, 275), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 53.617398 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(191, 248), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(502, 275), -360, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 53.757535 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(191, 248), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(502, 275), -240, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 53.901047 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(191, 248), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(502, 275), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 54.213331 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(191, 248), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(502, 275), -360, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 54.353203 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(189, 247), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(500, 274), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 55.36654 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(205, 4), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(220, 175), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.label', event , 55.481368 )

    ########################
    player.display_comment("""Save the object as \"1\"""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(357, 1), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(357, 1), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 58.046702 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(115, 10), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(130, 357), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.label_8', event , 58.169329 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(118, 14), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(133, 361), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.label_8', event , 58.799323 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(221, 10), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(236, 406), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.save', event , 59.660643 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(221, 10), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(236, 406), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.save', event , 59.748453 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x31, Qt.NoModifier, """1""", False, 1)
    player.post_event( 'CarvingObjectSaveAsDlg.lineEdit', event , 62.319976 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x31, Qt.NoModifier, """1""", False, 1)
    player.post_event( 'CarvingObjectSaveAsDlg.lineEdit', event , 62.393851 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000004, Qt.NoModifier, """""", False, 1)
    player.post_event( 'CarvingObjectSaveAsDlg.lineEdit', event , 65.117914 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000004, Qt.NoModifier, """""", False, 1)
    player.post_event( 'CarvingObjectSaveAsDlg', event , 65.272017 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(328, 212), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(639, 578), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter2.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 66.007162 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(31, 14), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(46, 185), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.label', event , 66.109079 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(26, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(41, 183), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.label', event , 66.422088 )

    ########################
    player.display_comment("""New object""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(353, 6), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(353, 6), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 67.297984 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(63, 43), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(80, 237), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.QTableView_0.qt_scrollarea_viewport', event , 68.366668 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(63, 43), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(80, 237), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.QTableView_0.qt_scrollarea_viewport', event , 68.462524 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(13, 210), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(324, 237), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 68.989233 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(186, 210), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(497, 237), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 69.082513 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(187, 211), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(498, 238), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 69.19988 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(205, 219), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(516, 246), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 69.295522 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(202, 216), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(513, 243), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 69.535985 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(168, 198), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(479, 225), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 69.626253 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(150, 172), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(461, 199), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 69.726954 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(149, 166), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(460, 193), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 69.819266 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(146, 160), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(457, 187), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 69.922586 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(143, 155), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(454, 182), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 70.011604 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(140, 153), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(451, 180), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 70.11056 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(139, 152), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(450, 179), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 70.196053 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(139, 151), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(450, 178), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 70.29363 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(139, 150), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(450, 177), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 70.388054 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(139, 150), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(450, 177), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 71.846654 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(138, 150), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(449, 177), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 71.985569 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(129, 152), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(440, 179), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 72.067711 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(126, 152), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(437, 179), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 72.158902 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(126, 152), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(437, 179), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 72.539222 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(124, 152), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(435, 179), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 74.505806 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(1, 41), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(289, 183), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_vcontainer.QScrollBar_0', event , 74.599059 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(135, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(150, 183), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.label', event , 74.689198 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(128, 14), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(143, 185), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.label', event , 74.769755 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(69, 15), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(86, 209), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.QTableView_0.qt_scrollarea_viewport', event , 75.086906 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(69, 15), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(86, 209), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.QTableView_0.qt_scrollarea_viewport', event , 75.18181 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(1, 180), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(310, 205), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0', event , 75.318363 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(189, 174), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(500, 201), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 75.405396 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(184, 168), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(495, 195), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 75.508332 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(169, 158), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(480, 185), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 75.595948 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(152, 134), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(463, 161), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 75.699018 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(153, 128), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(464, 155), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 75.785456 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(159, 122), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(470, 149), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 75.878435 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(155, 120), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(466, 147), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 75.9663 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(149, 120), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(460, 147), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 76.059333 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(149, 120), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(460, 147), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 76.156394 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(168, 134), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(479, 161), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 76.252821 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(168, 134), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(479, 161), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 76.410515 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(168, 135), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(479, 162), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 77.261383 )

    ########################
    player.display_comment("""Segment.""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(331, 11), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(331, 11), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 78.036024 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(73, 3), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(88, 350), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.label_8', event , 78.22315 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(59, 16), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(74, 384), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.segment', event , 78.561309 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(59, 16), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(74, 384), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.segment', event , 78.647527 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(47, 2), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(62, 349), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.label_8', event , 80.763242 )

    ########################
    player.display_comment("""Scroll a bit""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(423, 3), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(423, 3), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 81.593502 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(197, 33), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(508, 60), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 81.688304 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(334, 103), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(645, 130), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 81.776984 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(17, 117), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(673, 144), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 81.886602 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(17, 115), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(673, 142), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 81.973006 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(19, 115), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(675, 142), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 82.102796 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(77, 96), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(733, 123), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 82.194356 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(91, 85), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(747, 112), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 82.309188 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(90, 84), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(746, 111), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 82.39423 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(93, 85), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(749, 112), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 82.502684 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(104, 92), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(760, 119), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 82.586939 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(105, 95), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(761, 122), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 82.692835 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(105, 96), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(761, 123), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 82.777544 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(105, 96), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(761, 123), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 83.749705 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(105, 96), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(761, 123), -480, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 83.869087 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(105, 96), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(761, 123), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 84.780087 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(105, 96), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(761, 123), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 84.970623 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(105, 96), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(761, 123), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 85.687573 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(105, 96), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(761, 123), 240, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 85.822819 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(105, 96), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(761, 123), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 85.942318 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(105, 96), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(761, 123), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 86.345242 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(105, 96), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(761, 123), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 86.479242 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(105, 96), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(761, 123), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 87.031381 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(105, 96), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(761, 123), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 87.150963 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(105, 96), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(761, 123), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 87.287733 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(105, 96), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(761, 123), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 87.408718 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(105, 96), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(761, 123), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 87.781877 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(105, 96), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(761, 123), 240, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 87.904369 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(105, 96), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(761, 123), 360, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 88.02352 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(105, 96), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(761, 123), 240, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 88.159525 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(105, 96), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(761, 123), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 88.33065 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(105, 96), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(761, 123), 360, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 88.453845 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(105, 96), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(761, 123), 240, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 88.586935 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(105, 96), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(761, 123), 240, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 88.712077 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(105, 96), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(761, 123), 360, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 88.842678 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(105, 96), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(761, 123), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 88.973198 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(105, 96), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(761, 123), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 89.560041 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(105, 96), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(761, 123), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 89.712158 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(138, 101), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(794, 128), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 89.880589 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(137, 100), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(793, 127), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 90.000946 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 90.110027 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 90.209988 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 90.526114 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), 240, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 90.644916 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 90.934595 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 91.074385 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 91.870615 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -480, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 91.989336 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 92.183676 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -600, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 92.289318 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 92.540449 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -360, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 92.675263 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 92.846624 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -240, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 92.971222 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 93.214947 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -240, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 93.342245 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 93.520544 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -240, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 93.641066 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 93.859783 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 93.975464 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 94.187626 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -360, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 94.30322 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 94.512138 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -360, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 94.626077 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 94.886198 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -480, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 95.00297 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 95.268298 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -240, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 95.407883 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 95.661468 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -360, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 95.775413 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 96.058948 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -240, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 96.180792 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 96.763626 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 97.133337 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 97.63939 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -360, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 97.772623 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 97.958318 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -600, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 98.074961 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 98.267323 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -840, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 98.417307 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 98.590917 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -360, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 98.731466 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 99.014613 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 99.137902 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 99.478224 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -240, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 99.605821 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 99.754393 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 99.892105 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 100.308203 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 100.424832 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -240, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 100.579152 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 101.110525 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -480, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 101.28807 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -240, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 101.430209 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 101.715427 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -960, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 101.875505 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -240, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 102.024423 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 102.331137 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -600, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 102.481318 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -240, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 102.637753 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 102.865812 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -600, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 103.000773 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -240, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 103.342941 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -240, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 103.432272 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -240, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 103.546697 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 103.793555 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -240, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 103.875722 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 103.975982 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 105.044106 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 105.180296 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 106.29476 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -720, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 106.410044 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -240, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 106.505026 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 107.007891 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -600, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 107.087562 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(136, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(792, 126), -360, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 107.167714 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(135, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(791, 126), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 108.966957 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(174, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(485, 126), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 109.067892 )

    ########################
    player.display_comment("""Edit labels some more....""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(380, 10), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(380, 10), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 109.915853 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(108, 3), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(123, 174), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.label', event , 110.049898 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(102, 10), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(117, 181), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.label', event , 110.144648 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(56, 35), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(73, 229), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.QTableView_0.qt_scrollarea_viewport', event , 110.575653 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(56, 35), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(73, 229), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.QTableView_0.qt_scrollarea_viewport', event , 110.677104 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(74, 195), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(385, 222), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 111.078994 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(110, 170), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(766, 197), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 111.18849 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(177, 166), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(833, 193), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 111.298361 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(191, 165), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(847, 192), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 111.420874 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(185, 156), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(841, 183), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 111.52847 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(173, 154), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(829, 181), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 111.652305 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(179, 155), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(835, 182), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 111.756397 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(185, 157), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(841, 184), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 111.885306 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(185, 157), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(841, 184), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 112.446057 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(183, 153), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(839, 180), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 112.560624 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(181, 151), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(837, 178), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 112.678309 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(181, 151), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(837, 178), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 112.828931 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(181, 152), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(837, 179), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 113.085085 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(184, 158), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(840, 185), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 113.194307 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(184, 159), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(840, 186), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 113.419285 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(183, 159), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(839, 186), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 113.851767 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(304, 194), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(615, 221), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 113.937976 )

    ########################
    player.display_comment("""segment""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(450, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(450, 0), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 115.317847 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(115, 3), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(130, 350), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.label_8', event , 115.707343 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(100, 10), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(115, 357), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.label_8', event , 115.80988 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(86, 11), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(101, 379), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.segment', event , 116.105547 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(86, 11), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(101, 379), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.segment', event , 116.201742 )

    ########################
    player.display_comment("""more editing....""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(426, 8), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(426, 8), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 119.948647 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(50, 41), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(361, 68), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 120.025588 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(55, 13), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(72, 207), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.QTableView_0.qt_scrollarea_viewport', event , 120.543886 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(55, 13), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(72, 207), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.QTableView_0.qt_scrollarea_viewport', event , 120.639111 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(70, 180), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(381, 207), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 120.824112 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(45, 178), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(701, 205), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 120.946945 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(46, 176), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(702, 203), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 121.065758 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(132, 177), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(788, 204), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 121.199189 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(238, 178), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(894, 205), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 121.319525 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(232, 170), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(888, 197), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 121.452673 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(201, 157), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(857, 184), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 121.564696 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(199, 156), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(855, 183), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 121.689765 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(198, 154), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(854, 181), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 121.798814 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(197, 151), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(853, 178), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 121.915878 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(196, 150), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(852, 177), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 122.021175 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(195, 150), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(851, 177), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 122.141801 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(195, 150), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(851, 177), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 122.240622 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(191, 146), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(847, 173), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 122.363882 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(191, 146), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(847, 173), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 122.459158 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(194, 152), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(850, 179), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 122.687615 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(196, 154), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(852, 181), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 122.799456 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(195, 154), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(851, 181), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 123.22511 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(135, 165), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(791, 192), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_0.ImageView2D_0.QWidget_0', event , 123.315863 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(15, 268), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(326, 295), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 123.44225 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(96, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(111, 380), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.segment', event , 123.919371 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(94, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(109, 380), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.segment', event , 124.034602 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(94, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(109, 380), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.segment', event , 124.116912 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(17, 230), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(328, 257), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 125.183883 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(156, 207), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(467, 234), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 125.293098 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(215, 207), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(526, 234), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 125.397722 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(216, 209), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(527, 236), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 125.514783 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(201, 206), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(512, 233), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 125.625765 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(200, 206), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(511, 233), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 125.943248 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(199, 207), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(510, 234), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 126.035366 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(198, 207), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(509, 234), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 126.152838 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(197, 204), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(508, 231), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 126.249933 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(195, 201), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(506, 228), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 126.373352 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(195, 202), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(506, 229), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 126.477515 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(206, 212), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(517, 239), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 126.59839 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(206, 216), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(517, 243), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 126.705827 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(205, 216), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(516, 243), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 127.321237 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(187, 215), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(498, 242), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 127.42654 )

    ########################
    player.display_comment("""Save object as \"2\"""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(426, 13), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(426, 13), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 128.559899 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(71, 7), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(86, 403), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.save', event , 129.482996 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(71, 7), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(86, 403), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.save', event , 129.565545 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x32, Qt.NoModifier, """2""", False, 1)
    player.post_event( 'CarvingObjectSaveAsDlg.lineEdit', event , 130.379214 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x32, Qt.NoModifier, """2""", False, 1)
    player.post_event( 'CarvingObjectSaveAsDlg.lineEdit', event , 130.466667 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000004, Qt.NoModifier, """""", False, 1)
    player.post_event( 'CarvingObjectSaveAsDlg.lineEdit', event , 133.742259 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000004, Qt.NoModifier, """""", False, 1)
    player.post_event( 'CarvingObjectSaveAsDlg', event , 133.901452 )

    ########################
    player.display_comment("""Load object \"1\"""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(45, 40), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(356, 67), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 137.837972 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(6, 251), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(294, 393), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_vcontainer.QScrollBar_0', event , 139.290741 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(6, 251), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(294, 393), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_vcontainer.QScrollBar_0', event , 139.38331 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(107, 17), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(122, 422), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.namesButton', event , 141.589165 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(107, 17), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(122, 422), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.namesButton', event , 141.691512 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(62, 8), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(886, 692), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'CarvingObjectManagementDlg.verticalLayoutWidget.objectNames.qt_scrollarea_viewport', event , 144.276721 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(62, 8), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(886, 692), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'CarvingObjectManagementDlg.verticalLayoutWidget.objectNames.qt_scrollarea_viewport', event , 144.369333 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(64, 17), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(886, 843), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'CarvingObjectManagementDlg.verticalLayoutWidget.loadButton', event , 145.480838 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(64, 17), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(886, 843), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'CarvingObjectManagementDlg.verticalLayoutWidget.loadButton', event , 145.561352 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(327, 260), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(638, 626), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter2.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 148.563824 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(291, 241), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(602, 607), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter2.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 148.653772 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(278, 236), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(589, 602), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter2.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 148.7428 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(262, 229), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(573, 595), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter2.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 148.836797 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(260, 230), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(571, 596), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter2.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 149.160512 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(247, 218), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(558, 584), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter2.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 149.265494 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(224, 190), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(535, 556), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter2.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 149.390266 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(222, 184), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(533, 550), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter2.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 149.52234 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(220, 168), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(531, 534), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter2.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 149.641987 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(220, 167), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(531, 533), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter2.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 149.981073 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(220, 166), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(531, 532), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter2.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 150.088485 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(220, 166), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(531, 532), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter2.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 150.655079 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(220, 166), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(531, 532), -2880, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter2.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 150.791547 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(220, 166), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(531, 532), -600, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter2.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 150.940922 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(220, 166), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(531, 532), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter2.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 152.084682 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(220, 166), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(531, 532), -3000, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter2.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 152.211119 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(220, 166), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(531, 532), -600, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter2.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 152.372533 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(220, 166), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(531, 532), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter2.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 153.103745 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(220, 166), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(531, 532), 1320, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter2.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 153.232073 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(220, 164), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(531, 530), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter2.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 153.859204 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(203, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(514, 312), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 153.976743 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(201, 283), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(512, 310), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 154.084566 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(200, 283), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(511, 310), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 154.210438 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(200, 283), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(511, 310), 1200, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 154.310026 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(199, 283), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(510, 310), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 154.432342 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(199, 283), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(510, 310), 720, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 154.604625 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(198, 284), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(509, 311), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 155.2589 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(193, 284), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(504, 311), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 155.362587 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(193, 284), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(504, 311), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 155.589821 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(193, 284), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(504, 311), -1440, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 155.786178 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(193, 284), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(504, 311), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 156.569084 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(193, 284), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(504, 311), 600, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 156.737295 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(193, 284), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(504, 311), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 156.919805 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(191, 284), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(502, 311), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 158.17206 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(187, 284), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(498, 311), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 158.262577 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(182, 282), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(493, 309), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 158.440268 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(24, 233), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(335, 260), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 158.548947 )

    ########################
    player.display_comment("""Show completed segments (unicolor)""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(357, 1), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(357, 1), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 159.997335 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(356, 14), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(356, 14), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 160.071083 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(10, 16), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(22, 549), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_3_lane_0.layerWidget.qt_scrollarea_viewport.LayerItemWidget_Completed segments (unicolor).ToggleEye_0', event , 161.137648 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(10, 16), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(22, 549), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_3_lane_0.layerWidget.qt_scrollarea_viewport.LayerItemWidget_Completed segments (unicolor).ToggleEye_0', event , 161.384486 )

    ########################
    player.display_comment("""Hide again""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(7, 3), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(22, 360), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.label_3', event , 168.07097 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(7, 3), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(22, 360), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.label_3', event , 168.07097 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(8, 16), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(20, 549), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_3_lane_0.layerWidget.qt_scrollarea_viewport.LayerItemWidget_Completed segments (unicolor).ToggleEye_0', event , 169.295285 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(8, 16), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(20, 549), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_3_lane_0.layerWidget.qt_scrollarea_viewport.LayerItemWidget_Completed segments (unicolor).ToggleEye_0', event , 169.458789 )

    ########################
    player.display_comment("""Show completed segments (one color per object)""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(339, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(339, 0), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 171.226967 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(339, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(339, 0), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 171.226967 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(338, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(338, 0), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 171.853641 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(337, 1), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(337, 1), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 171.938368 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(335, 1), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(335, 1), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 172.019325 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(333, 2), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(333, 2), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 172.104447 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(321, 3), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(321, 3), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 172.209465 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(310, 5), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(310, 5), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 172.299262 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(10, 14), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(22, 589), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_3_lane_0.layerWidget.qt_scrollarea_viewport.LayerItemWidget_Completed segments (one color per object).ToggleEye_0', event , 173.721479 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(10, 14), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(22, 589), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_3_lane_0.layerWidget.qt_scrollarea_viewport.LayerItemWidget_Completed segments (one color per object).ToggleEye_0', event , 173.987587 )

    ########################
    player.display_comment("""Hide again""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(34, 3), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(49, 360), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.label_3', event , 177.428367 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(34, 3), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(49, 360), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.label_3', event , 177.428367 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(14, 15), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(26, 590), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_3_lane_0.layerWidget.qt_scrollarea_viewport.LayerItemWidget_Completed segments (one color per object).ToggleEye_0', event , 179.087634 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(14, 15), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(26, 590), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_3_lane_0.layerWidget.qt_scrollarea_viewport.LayerItemWidget_Completed segments (one color per object).ToggleEye_0', event , 179.247502 )

    ########################
    player.display_comment("""Show supervoxels""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(41, 427), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(47, 375), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget', event , 181.491982 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(41, 427), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(47, 375), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget', event , 181.578612 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(41, 427), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(47, 375), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget', event , 181.578612 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(7, 16), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(19, 633), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_3_lane_0.layerWidget.qt_scrollarea_viewport.LayerItemWidget_Supervoxels.ToggleEye_0', event , 182.810013 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(7, 16), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(19, 633), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_3_lane_0.layerWidget.qt_scrollarea_viewport.LayerItemWidget_Supervoxels.ToggleEye_0', event , 183.091886 )

    ########################
    player.display_comment("""Hide again""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(27, 1), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(42, 358), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.label_3', event , 185.142733 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(27, 1), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(42, 358), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.label_3', event , 185.142733 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(13, 13), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(25, 630), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_3_lane_0.layerWidget.qt_scrollarea_viewport.LayerItemWidget_Supervoxels.ToggleEye_0', event , 185.780596 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(13, 13), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(25, 630), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_3_lane_0.layerWidget.qt_scrollarea_viewport.LayerItemWidget_Supervoxels.ToggleEye_0', event , 186.001124 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(8, 135), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(295, 582), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_3_lane_0.layerWidget.qt_scrollarea_vcontainer.QScrollBar_0', event , 189.162167 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(8, 138), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(295, 585), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_3_lane_0.layerWidget.qt_scrollarea_vcontainer.QScrollBar_0', event , 189.243095 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(8, 140), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(295, 587), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_3_lane_0.layerWidget.qt_scrollarea_vcontainer.QScrollBar_0', event , 189.340279 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(8, 144), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(295, 591), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_3_lane_0.layerWidget.qt_scrollarea_vcontainer.QScrollBar_0', event , 189.423511 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(8, 147), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(295, 594), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_3_lane_0.layerWidget.qt_scrollarea_vcontainer.QScrollBar_0', event , 189.507825 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(8, 152), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(295, 599), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_3_lane_0.layerWidget.qt_scrollarea_vcontainer.QScrollBar_0', event , 189.614238 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(8, 155), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(295, 602), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_3_lane_0.layerWidget.qt_scrollarea_vcontainer.QScrollBar_0', event , 189.706469 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(8, 163), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(295, 610), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_3_lane_0.layerWidget.qt_scrollarea_vcontainer.QScrollBar_0', event , 189.814627 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(8, 170), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(295, 617), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_3_lane_0.layerWidget.qt_scrollarea_vcontainer.QScrollBar_0', event , 189.901919 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(8, 174), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(295, 621), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_3_lane_0.layerWidget.qt_scrollarea_vcontainer.QScrollBar_0', event , 190.001476 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(8, 180), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(295, 627), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_3_lane_0.layerWidget.qt_scrollarea_vcontainer.QScrollBar_0', event , 190.466637 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(8, 202), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(295, 649), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_3_lane_0.layerWidget.qt_scrollarea_vcontainer.QScrollBar_0', event , 190.550245 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(8, 211), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(295, 658), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_3_lane_0.layerWidget.qt_scrollarea_vcontainer.QScrollBar_0', event , 190.652337 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(8, 212), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(295, 659), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_3_lane_0.layerWidget.qt_scrollarea_vcontainer.QScrollBar_0', event , 190.811526 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(8, 215), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(295, 662), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_3_lane_0.layerWidget.qt_scrollarea_vcontainer.QScrollBar_0', event , 190.912657 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(8, 216), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(295, 663), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_3_lane_0.layerWidget.qt_scrollarea_vcontainer.QScrollBar_0', event , 190.996092 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(8, 216), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(295, 663), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_3_lane_0.layerWidget.qt_scrollarea_vcontainer.QScrollBar_0', event , 192.775791 )

    ########################
    player.display_comment("""Save Project.""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(305, 3), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(305, 3), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 194.102713 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(49, 18), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(49, 18), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 194.537711 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(41, 7), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(41, 7), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 194.614162 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(38, 7), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(38, 7), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 194.696457 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(38, 7), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(38, 7), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 194.789281 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(38, -12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(38, 7), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.project_menu', event , 194.877028 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(38, -8), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(38, 11), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.project_menu', event , 196.721729 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(38, 11), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(38, 64), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 196.800244 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(38, -1), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(38, 18), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.project_menu', event , 196.87011 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(38, 18), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(42, 78), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 196.939816 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(38, 11), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(38, 30), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.project_menu', event , 197.018858 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(42, 59), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(42, 78), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.project_menu', event , 197.093982 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(42, 59), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(42, 78), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.project_menu', event , 197.496747 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(42, 59), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(42, 78), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.project_menu', event , 197.620557 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(429, 1), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(713, 517), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QFileDialog.fileNameEdit', event , 200.479639 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(27, 13), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(755, 525), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.QFileDialog.buttonBox.QPushButton_0', event , 202.102367 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(27, 13), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(755, 525), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QFileDialog.buttonBox.QPushButton_0', event , 202.174399 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(313, 99), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(624, 465), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter2.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 203.865968 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(11, 16), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(11, 16), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 215.254926 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(16, 5), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(16, 5), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 215.330057 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(18, 3), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(18, 3), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 215.406837 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(34, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(34, 0), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 215.688631 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(34, 2), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(34, 2), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 215.763127 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(33, 3), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(33, 3), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 215.84085 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(33, 4), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(33, 4), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 215.921997 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(33, 5), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(33, 5), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 215.989173 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(32, 5), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(32, 5), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 216.072789 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(31, 8), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(31, 8), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 216.15402 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(31, 9), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(31, 9), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 216.23002 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(31, 9), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(31, 9), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 216.308272 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(31, -10), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(31, 9), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.project_menu', event , 216.406381 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(31, -9), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(31, 10), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.project_menu', event , 216.760895 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(31, 10), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(31, 11), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 216.862128 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(33, -3), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(33, 16), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.project_menu', event , 216.963211 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(33, 16), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(36, 38), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 217.05884 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(34, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(34, 19), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.project_menu', event , 217.151689 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(37, 46), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(37, 65), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.project_menu', event , 217.234387 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(41, 61), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(41, 80), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.project_menu', event , 217.330681 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(42, 66), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(42, 85), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.project_menu', event , 217.42307 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(43, 69), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(43, 88), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.project_menu', event , 217.505294 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(43, 68), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(43, 87), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.project_menu', event , 217.908929 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(43, 62), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(43, 81), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.project_menu', event , 217.98809 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(43, 60), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(43, 79), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.project_menu', event , 218.068747 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(43, 59), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(43, 78), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.project_menu', event , 218.185844 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(43, 45), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(43, 64), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.project_menu', event , 218.271752 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(43, 41), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(43, 60), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.project_menu', event , 218.350662 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(42, 41), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(42, 60), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.project_menu', event , 218.945074 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(16, 69), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(16, 88), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.project_menu', event , 219.016222 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(-47, 130), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(-47, 149), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.project_menu', event , 219.423559 )

    player.display_comment("SCRIPT COMPLETE")
