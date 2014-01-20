
# Event Recording
# Created by Stuart
# Started at: 2014-01-20 22:39:17.304909

def playback_events(player):
    import PyQt4.QtCore
    from PyQt4.QtCore import Qt, QEvent, QPoint
    import PyQt4.QtGui
    
    # The getMainWindow() function is provided by EventRecorderApp
    mainwin = PyQt4.QtGui.QApplication.instance().getMainWindow()

    player.display_comment("SCRIPT STARTING")


    event = PyQt4.QtGui.QResizeEvent(PyQt4.QtCore.QSize(1000, 650), PyQt4.QtCore.QSize(1000, 750))
    player.post_event( 'MainWindow', event , 0.660198 )

    ########################
    player.display_comment("""In this recording, we\'ll create an object classification project and add (generated) data to it and do some basic labeling and training.""")
    ########################

    ########################
    player.display_comment("""New Project (Object Classification)""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(289, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(289, 0), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 1.368803 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(106, 16), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(417, 513), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.startupPage.frame.CreateList.qt_scrollarea_viewport.scrollAreaWidgetContents.QToolButton_14', event , 7.322243 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(106, 16), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(417, 513), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.startupPage.frame.CreateList.qt_scrollarea_viewport.scrollAreaWidgetContents.QToolButton_14', event , 7.409471 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000004, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.QFileDialog.fileNameEdit', event , 9.096179 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000004, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.QFileDialog', event , 9.170328 )

    ########################
    player.display_comment("""Add raw data""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(51, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(373, 96), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport.QWidget_0.AddFileButton_0', event , 12.547411 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(51, -14), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(373, 96), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 12.635365 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(46, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(368, 110), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 13.199332 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(45, 3), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(367, 113), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 13.279778 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(44, 5), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(366, 115), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 13.39732 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(43, 9), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(365, 119), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 13.46709 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(43, 9), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(365, 119), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 13.574459 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(43, 9), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(365, 119), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 13.645252 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2f, Qt.NoModifier, """/""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 15.032127 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2f, Qt.NoModifier, """/""", False, 1)
    player.post_event( 'QListView_0', event , 15.105471 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x48, Qt.NoModifier, """h""", False, 1)
    player.post_event( 'QListView_0', event , 15.29228 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x48, Qt.NoModifier, """h""", False, 1)
    player.post_event( 'QListView_0', event , 15.357916 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4f, Qt.NoModifier, """o""", False, 1)
    player.post_event( 'QListView_0', event , 15.439412 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4d, Qt.NoModifier, """m""", False, 1)
    player.post_event( 'QListView_0', event , 15.535224 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4f, Qt.NoModifier, """o""", False, 1)
    player.post_event( 'QListView_0', event , 15.597331 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'QListView_0', event , 15.657442 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4d, Qt.NoModifier, """m""", False, 1)
    player.post_event( 'QListView_0', event , 15.719733 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'QListView_0', event , 15.779742 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2f, Qt.NoModifier, """/""", False, 1)
    player.post_event( 'QListView_0', event , 15.841453 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2f, Qt.NoModifier, """/""", False, 1)
    player.post_event( 'QListView_0', event , 15.906259 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x56, Qt.NoModifier, """v""", False, 1)
    player.post_event( 'QListView_0', event , 16.447622 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x56, Qt.NoModifier, """v""", False, 1)
    player.post_event( 'QListView_0', event , 16.534718 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'QListView_0', event , 16.597504 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'QListView_0', event , 16.703381 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x47, Qt.NoModifier, """g""", False, 1)
    player.post_event( 'QListView_0', event , 16.765037 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x47, Qt.NoModifier, """g""", False, 1)
    player.post_event( 'QListView_0', event , 16.827794 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x52, Qt.NoModifier, """r""", False, 1)
    player.post_event( 'QListView_0', event , 16.888306 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'QListView_0', event , 16.950989 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x52, Qt.NoModifier, """r""", False, 1)
    player.post_event( 'QListView_0', event , 17.014581 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'QListView_0', event , 17.074246 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'QListView_0', event , 17.135911 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'QListView_0', event , 17.195626 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'QListView_0', event , 17.255449 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'QListView_0', event , 17.317123 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2f, Qt.NoModifier, """/""", False, 1)
    player.post_event( 'QListView_0', event , 17.378259 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2f, Qt.NoModifier, """/""", False, 1)
    player.post_event( 'QListView_0', event , 17.445139 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x46, Qt.NoModifier, """f""", False, 1)
    player.post_event( 'QListView_0', event , 18.795503 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x46, Qt.NoModifier, """f""", False, 1)
    player.post_event( 'QListView_0', event , 18.908036 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'QListView_0', event , 18.96751 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'QListView_0', event , 19.029306 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4b, Qt.NoModifier, """k""", False, 1)
    player.post_event( 'QListView_0', event , 19.090575 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'QListView_0', event , 19.151737 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4b, Qt.NoModifier, """k""", False, 1)
    player.post_event( 'QListView_0', event , 19.212767 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'QListView_0', event , 19.273119 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1)
    player.post_event( 'QListView_0', event , 19.333404 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'QListView_0', event , 19.394225 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1)
    player.post_event( 'QListView_0', event , 19.45937 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2d, Qt.NoModifier, """-""", False, 1)
    player.post_event( 'QListView_0', event , 19.522973 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'QListView_0', event , 19.585923 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'QListView_0', event , 19.647479 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'QListView_0', event , 19.710383 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'QListView_0', event , 19.7702 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x53, Qt.NoModifier, """s""", False, 1)
    player.post_event( 'QListView_0', event , 19.831572 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'QListView_0', event , 19.893831 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x53, Qt.NoModifier, """s""", False, 1)
    player.post_event( 'QListView_0', event , 19.955304 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'QListView_0', event , 20.014789 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1)
    player.post_event( 'QListView_0', event , 20.075108 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'QListView_0', event , 20.135022 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1)
    player.post_event( 'QListView_0', event , 20.196083 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2d, Qt.NoModifier, """-""", False, 1)
    player.post_event( 'QListView_0', event , 20.257449 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x44, Qt.NoModifier, """d""", False, 1)
    player.post_event( 'QListView_0', event , 20.316822 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x44, Qt.NoModifier, """d""", False, 1)
    player.post_event( 'QListView_0', event , 20.377186 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'QListView_0', event , 20.438145 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'QListView_0', event , 20.503866 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'QListView_0', event , 20.569443 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'QListView_0', event , 20.631957 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'QListView_0', event , 20.697504 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'QListView_0', event , 20.760395 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000004, Qt.NoModifier, """""", False, 1)
    player.post_event( 'QListView_0', event , 20.824082 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000004, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 20.886782 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x43, Qt.NoModifier, """c""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 22.811152 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x55, Qt.NoModifier, """u""", False, 1)
    player.post_event( 'QListView_0', event , 22.930899 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x43, Qt.NoModifier, """c""", False, 1)
    player.post_event( 'QListView_0', event , 22.992838 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x55, Qt.NoModifier, """u""", False, 1)
    player.post_event( 'QListView_0', event , 23.053131 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x42, Qt.NoModifier, """b""", False, 1)
    player.post_event( 'QListView_0', event , 23.113205 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x42, Qt.NoModifier, """b""", False, 1)
    player.post_event( 'QListView_0', event , 23.178376 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'QListView_0', event , 23.242529 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'QListView_0', event , 23.304503 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1)
    player.post_event( 'QListView_0', event , 23.459954 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'QListView_0', event , 23.579281 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'QListView_0', event , 23.640968 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1)
    player.post_event( 'QListView_0', event , 23.703874 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4f, Qt.NoModifier, """o""", False, 1)
    player.post_event( 'QListView_0', event , 23.838691 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4f, Qt.NoModifier, """o""", False, 1)
    player.post_event( 'QListView_0', event , 23.937949 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x42, Qt.NoModifier, """b""", False, 1)
    player.post_event( 'QListView_0', event , 24.015617 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x42, Qt.NoModifier, """b""", False, 1)
    player.post_event( 'QListView_0', event , 24.076999 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4a, Qt.NoModifier, """j""", False, 1)
    player.post_event( 'QListView_0', event , 24.180109 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'QListView_0', event , 24.256741 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4a, Qt.NoModifier, """j""", False, 1)
    player.post_event( 'QListView_0', event , 24.319254 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x43, Qt.NoModifier, """c""", False, 1)
    player.post_event( 'QListView_0', event , 24.378853 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'QListView_0', event , 24.441898 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x43, Qt.NoModifier, """c""", False, 1)
    player.post_event( 'QListView_0', event , 24.501443 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'QListView_0', event , 24.561258 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'QListView_0', event , 24.623473 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x53, Qt.NoModifier, """s""", False, 1)
    player.post_event( 'QListView_0', event , 24.684024 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x53, Qt.NoModifier, """s""", False, 1)
    player.post_event( 'QListView_0', event , 24.746477 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1)
    player.post_event( 'QListView_0', event , 24.922292 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'QListView_0', event , 25.197458 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'QListView_0', event , 25.28298 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1)
    player.post_event( 'QListView_0', event , 25.345906 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x52, Qt.NoModifier, """r""", False, 1)
    player.post_event( 'QListView_0', event , 25.523875 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'QListView_0', event , 25.620065 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x52, Qt.NoModifier, """r""", False, 1)
    player.post_event( 'QListView_0', event , 25.681444 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x57, Qt.NoModifier, """w""", False, 1)
    player.post_event( 'QListView_0', event , 25.743036 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'QListView_0', event , 25.807082 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2e, Qt.NoModifier, """.""", False, 1)
    player.post_event( 'QListView_0', event , 25.870887 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x57, Qt.NoModifier, """w""", False, 1)
    player.post_event( 'QListView_0', event , 25.933076 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2e, Qt.NoModifier, """.""", False, 1)
    player.post_event( 'QListView_0', event , 25.994309 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'QListView_0', event , 26.053497 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'QListView_0', event , 26.115148 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x50, Qt.NoModifier, """p""", False, 1)
    player.post_event( 'QListView_0', event , 26.175457 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x50, Qt.NoModifier, """p""", False, 1)
    player.post_event( 'QListView_0', event , 26.237068 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x59, Qt.NoModifier, """y""", False, 1)
    player.post_event( 'QListView_0', event , 26.313429 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x59, Qt.NoModifier, """y""", False, 1)
    player.post_event( 'QListView_0', event , 26.375874 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000004, Qt.NoModifier, """""", False, 1)
    player.post_event( 'QListView_0', event , 26.48292 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(47, 53), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(365, 116), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport', event , 28.078552 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000004, Qt.NoModifier, """""", False, 1)
    player.post_event( 'QListView_0', event , 28.143118 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(43, 34), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(365, 116), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport', event , 28.717985 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000004, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport.QWidget_0.AddFileButton_0', event , 28.809388 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000004, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport.QWidget_0.AddFileButton_0', event , 28.890362 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(15, 34), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(337, 116), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.QHeaderView_0.qt_scrollarea_viewport', event , 29.685473 )

    ########################
    player.display_comment("""Add binary data""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(452, 15), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(452, 15), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 30.478479 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(452, 15), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(452, 15), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 30.61971 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(141, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(461, 57), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1', event , 30.820054 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(121, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(461, 59), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.QHeaderView_1.qt_scrollarea_viewport', event , 30.920384 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(141, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(461, 57), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1', event , 31.087599 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(141, 17), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(459, 51), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_tabbar', event , 31.500158 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(141, 17), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(459, 51), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_tabbar', event , 31.612663 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(134, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(454, 57), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0', event , 32.10565 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(102, 17), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(442, 76), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QHeaderView_1.qt_scrollarea_viewport', event , 32.200552 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(85, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(425, 94), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.AddFileButton_0', event , 32.634079 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(85, -18), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(425, 94), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.AddFileButton_0.QMenu_0', event , 32.762989 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(85, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(425, 112), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.AddFileButton_0.QMenu_0', event , 33.309309 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(84, 5), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(424, 117), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.AddFileButton_0.QMenu_0', event , 33.40058 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(83, 10), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(423, 122), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.AddFileButton_0.QMenu_0', event , 33.496245 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(83, 10), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(423, 122), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.AddFileButton_0.QMenu_0', event , 33.628747 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(83, 10), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(423, 122), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.AddFileButton_0.QMenu_0', event , 33.723875 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x43, Qt.NoModifier, """c""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 35.903131 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x55, Qt.NoModifier, """u""", False, 1)
    player.post_event( 'QListView_0', event , 35.998704 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x43, Qt.NoModifier, """c""", False, 1)
    player.post_event( 'QListView_0', event , 36.082943 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x55, Qt.NoModifier, """u""", False, 1)
    player.post_event( 'QListView_0', event , 36.163499 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x42, Qt.NoModifier, """b""", False, 1)
    player.post_event( 'QListView_0', event , 36.24417 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x42, Qt.NoModifier, """b""", False, 1)
    player.post_event( 'QListView_0', event , 36.325434 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'QListView_0', event , 36.403473 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'QListView_0', event , 36.484234 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1)
    player.post_event( 'QListView_0', event , 36.564306 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'QListView_0', event , 36.64119 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'QListView_0', event , 36.72437 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1)
    player.post_event( 'QListView_0', event , 36.808609 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4f, Qt.NoModifier, """o""", False, 1)
    player.post_event( 'QListView_0', event , 36.885547 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4f, Qt.NoModifier, """o""", False, 1)
    player.post_event( 'QListView_0', event , 36.969963 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x42, Qt.NoModifier, """b""", False, 1)
    player.post_event( 'QListView_0', event , 37.050262 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x42, Qt.NoModifier, """b""", False, 1)
    player.post_event( 'QListView_0', event , 37.128719 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4a, Qt.NoModifier, """j""", False, 1)
    player.post_event( 'QListView_0', event , 37.210847 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4a, Qt.NoModifier, """j""", False, 1)
    player.post_event( 'QListView_0', event , 37.294157 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'QListView_0', event , 37.3714 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x43, Qt.NoModifier, """c""", False, 1)
    player.post_event( 'QListView_0', event , 37.45347 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'QListView_0', event , 37.538672 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x43, Qt.NoModifier, """c""", False, 1)
    player.post_event( 'QListView_0', event , 37.618735 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'QListView_0', event , 37.702975 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'QListView_0', event , 37.784661 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x53, Qt.NoModifier, """s""", False, 1)
    player.post_event( 'QListView_0', event , 37.861609 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x53, Qt.NoModifier, """s""", False, 1)
    player.post_event( 'QListView_0', event , 37.94335 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1)
    player.post_event( 'QListView_0', event , 38.442363 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'QListView_0', event , 38.549648 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'QListView_0', event , 38.634817 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1)
    player.post_event( 'QListView_0', event , 38.805452 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x42, Qt.NoModifier, """b""", False, 1)
    player.post_event( 'QListView_0', event , 39.051438 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x42, Qt.NoModifier, """b""", False, 1)
    player.post_event( 'QListView_0', event , 39.13284 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x49, Qt.NoModifier, """i""", False, 1)
    player.post_event( 'QListView_0', event , 39.214464 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'QListView_0', event , 39.297179 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x49, Qt.NoModifier, """i""", False, 1)
    player.post_event( 'QListView_0', event , 39.379925 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'QListView_0', event , 39.459749 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'QListView_0', event , 39.53714 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x52, Qt.NoModifier, """r""", False, 1)
    player.post_event( 'QListView_0', event , 39.623413 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'QListView_0', event , 39.704131 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x52, Qt.NoModifier, """r""", False, 1)
    player.post_event( 'QListView_0', event , 39.781606 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x59, Qt.NoModifier, """y""", False, 1)
    player.post_event( 'QListView_0', event , 39.988292 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x59, Qt.NoModifier, """y""", False, 1)
    player.post_event( 'QListView_0', event , 40.106256 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2e, Qt.NoModifier, """.""", False, 1)
    player.post_event( 'QListView_0', event , 40.419322 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2e, Qt.NoModifier, """.""", False, 1)
    player.post_event( 'QListView_0', event , 40.533268 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'QListView_0', event , 40.634325 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'QListView_0', event , 40.714992 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x50, Qt.NoModifier, """p""", False, 1)
    player.post_event( 'QListView_0', event , 40.79394 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x50, Qt.NoModifier, """p""", False, 1)
    player.post_event( 'QListView_0', event , 40.879623 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x59, Qt.NoModifier, """y""", False, 1)
    player.post_event( 'QListView_0', event , 40.959956 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x59, Qt.NoModifier, """y""", False, 1)
    player.post_event( 'QListView_0', event , 41.043687 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000004, Qt.NoModifier, """""", False, 1)
    player.post_event( 'QListView_0', event , 41.129617 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000004, Qt.NoModifier, """""", False, 1)
    player.post_event( 'QListView_0', event , 41.248859 )

    ########################
    player.display_comment("""Select object features""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(188, 7), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(194, 219), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QAbstractButton_1', event , 43.143061 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(188, 7), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(194, 219), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QAbstractButton_1', event , 43.297075 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(171, 102), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(186, 224), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.containingWidget.label', event , 45.928284 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(171, 102), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(186, 224), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.containingWidget.label', event , 46.02546 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(172, 101), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(187, 223), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.containingWidget.label', event , 47.093927 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(189, 85), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(204, 207), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.containingWidget.label', event , 47.203354 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(215, 67), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(230, 189), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.containingWidget.label', event , 47.308982 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(227, 57), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(242, 179), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.containingWidget.label', event , 47.427011 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(228, 54), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(243, 176), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.containingWidget.label', event , 47.535604 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(228, 54), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(243, 176), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.containingWidget.label', event , 47.743954 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(228, 114), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(243, 176), -1560, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.containingWidget.label', event , 47.855977 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(172, 15), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(187, 149), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.containingWidget.selectFeaturesButton', event , 50.559305 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(172, 15), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(187, 149), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.containingWidget.selectFeaturesButton', event , 50.774006 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(54, 84), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(87, 140), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'FeatureSelectionDialog.treeWidget.qt_scrollarea_viewport', event , 54.784005 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(54, 85), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(87, 141), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'FeatureSelectionDialog.treeWidget.qt_scrollarea_viewport', event , 54.878987 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(54, 85), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(87, 141), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'FeatureSelectionDialog.treeWidget.qt_scrollarea_viewport', event , 54.97933 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(51, 221), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(84, 277), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'FeatureSelectionDialog.treeWidget.qt_scrollarea_viewport', event , 57.240872 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(51, 221), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(84, 277), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'FeatureSelectionDialog.treeWidget.qt_scrollarea_viewport', event , 57.337886 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(17, 7), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(374, 462), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'FeatureSelectionDialog.buttonBox.QPushButton_0', event , 58.682056 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(17, 7), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(374, 462), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'FeatureSelectionDialog.buttonBox.QPushButton_0', event , 58.800327 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(17, 7), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(374, 462), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'FeatureSelectionDialog.buttonBox.QPushButton_0', event , 58.955987 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(63, 146), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(374, 462), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter2.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 59.094568 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(61, 147), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(372, 463), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter2.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 60.499384 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(32, 133), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(343, 449), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter2.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 60.618604 )

    ########################
    player.display_comment("""Open Object Classification page""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(125, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(125, 0), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 61.744365 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(117, 57), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(122, 82), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar', event , 61.897262 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(131, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(137, 253), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QAbstractButton_2', event , 62.458708 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(131, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(137, 253), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QAbstractButton_2', event , 62.568804 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(165, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(180, 224), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.label', event , 69.590413 )

    ########################
    player.display_comment("""Add two label classes.""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(289, 5), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(289, 5), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 71.682406 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(277, 57), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(283, 199), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget', event , 72.168867 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(277, 117), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(283, 199), -1680, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget', event , 72.309964 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(145, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(265, 210), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.checkShowPredictions', event , 72.649718 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(202, 20), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(217, 201), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.AddLabelButton', event , 73.384058 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(202, 20), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(217, 201), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.AddLabelButton', event , 73.507152 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(189, 17), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(204, 198), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.AddLabelButton', event , 74.59194 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(189, 17), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(204, 198), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.AddLabelButton', event , 74.731872 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(113, 1), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(233, 211), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.checkShowPredictions', event , 75.339816 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(120, 6), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(240, 216), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.checkShowPredictions', event , 75.467685 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(132, 15), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(252, 225), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.checkShowPredictions', event , 75.615397 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(119, 19), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(239, 229), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.checkShowPredictions', event , 76.111526 )

    ########################
    player.display_comment("""Label some objects.  The two classes in this data are: (1) big light cubes and small dark ones, and (2) small light cubes and big dark ones.""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(114, 1), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(114, 1), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 76.931821 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(273, 5), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(279, 89), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QAbstractButton_1', event , 77.124799 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(5, 106), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(316, 133), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 77.267303 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(277, 174), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(283, 170), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget', event , 78.322548 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(277, 114), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(283, 170), 240, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget', event , 78.455815 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(189, 1), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(204, 213), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.label', event , 79.037898 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 45), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(286, 187), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget', event , 79.960418 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(55, 19), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(72, 191), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.QTableView_0.qt_scrollarea_viewport', event , 81.057452 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(55, 19), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(72, 191), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.QTableView_0.qt_scrollarea_viewport', event , 81.202688 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(5, 151), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(316, 178), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 81.661778 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(163, 118), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(474, 145), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 81.821189 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(165, 116), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(476, 143), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 81.988269 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(164, 113), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(475, 140), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 82.160146 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(165, 132), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(476, 159), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 82.321959 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(166, 141), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(477, 168), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 82.466736 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000022, (Qt.MetaModifier), """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3', event , 82.604569 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(166, 142), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(477, 169), Qt.NoButton, Qt.NoButton, (Qt.MetaModifier))
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 82.729557 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(166, 142), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(477, 169), 600, Qt.NoButton, (Qt.MetaModifier), 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 82.872515 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(166, 142), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(477, 169), 480, Qt.NoButton, (Qt.MetaModifier), 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 83.065058 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000022, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3', event , 84.035262 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000021, (Qt.ControlModifier), """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3', event , 84.185933 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(166, 142), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(477, 169), 120, Qt.NoButton, (Qt.ControlModifier), 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 84.45258 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(166, 142), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(477, 169), 840, Qt.NoButton, (Qt.ControlModifier), 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 84.628329 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(166, 142), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(477, 169), 240, Qt.NoButton, (Qt.ControlModifier), 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 84.797139 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(166, 142), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(477, 169), 120, Qt.NoButton, (Qt.ControlModifier), 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 85.320871 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(166, 142), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(477, 169), 240, Qt.NoButton, (Qt.ControlModifier), 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 85.502708 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000021, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3', event , 85.808022 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(160, 134), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(471, 161), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 85.955577 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(148, 125), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(459, 152), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 86.089432 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(143, 117), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(454, 144), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 86.258185 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(142, 115), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(453, 142), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 86.406486 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(142, 115), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(453, 142), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 88.038241 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(142, 115), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(453, 142), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 88.651951 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(143, 115), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(454, 142), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 89.557094 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(176, 116), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(487, 143), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 89.713461 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(176, 116), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(487, 143), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 90.515385 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(176, 116), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(487, 143), -960, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 90.703544 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(176, 116), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(487, 143), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 91.821929 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(176, 116), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(487, 143), -600, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 92.03237 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(176, 116), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(487, 143), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 93.196454 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(176, 116), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(487, 143), 360, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 93.394132 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(176, 116), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(487, 143), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 93.595657 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(176, 116), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(487, 143), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 94.204201 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(176, 116), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(487, 143), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 94.387859 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(176, 116), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(487, 143), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 94.85318 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(176, 116), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(487, 143), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 95.087322 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(176, 116), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(487, 143), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 95.344526 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(176, 116), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(487, 143), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 95.680991 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(176, 116), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(487, 143), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 96.28762 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(176, 116), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(487, 143), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 96.516104 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(176, 116), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(487, 143), 360, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 96.735511 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(176, 116), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(487, 143), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 96.929223 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(176, 116), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(487, 143), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 97.536641 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(176, 116), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(487, 143), 360, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 97.745984 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(176, 116), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(487, 143), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 97.955577 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(176, 116), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(487, 143), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 98.633868 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(176, 116), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(487, 143), 240, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 98.843297 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(176, 116), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(487, 143), 240, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 99.046212 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(176, 116), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(487, 143), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 99.468231 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(176, 116), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(487, 143), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 99.658613 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(176, 116), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(487, 143), 240, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 99.861745 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(176, 116), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(487, 143), 240, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 100.057543 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(176, 116), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(487, 143), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 100.580741 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(176, 116), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(487, 143), 480, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 100.783615 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(176, 116), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(487, 143), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 101.134282 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(176, 116), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(487, 143), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 101.353966 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(176, 116), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(487, 143), 240, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 101.562494 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(176, 116), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(487, 143), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 101.764275 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(176, 116), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(487, 143), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 101.964158 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(176, 116), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(487, 143), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 102.169058 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(176, 116), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(487, 143), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 102.781629 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(176, 116), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(487, 143), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 103.713182 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(176, 116), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(487, 143), 240, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 103.910592 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(176, 116), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(487, 143), 240, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 104.068437 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(176, 116), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(487, 143), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 105.035901 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(176, 116), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(487, 143), -360, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 105.233401 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(176, 116), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(487, 143), -840, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 105.380143 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(176, 116), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(487, 143), -240, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 105.70355 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(176, 116), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(487, 143), -240, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 105.920738 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(176, 116), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(487, 143), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 106.10408 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(176, 116), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(487, 143), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 106.282775 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(181, 113), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(492, 140), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 107.910874 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(265, 40), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(576, 67), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 108.07397 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(307, 32), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(618, 59), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 108.224447 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(13, 14), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(633, 45), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.ImageView2DHud_0.LabelButtons_6', event , 108.509754 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(-332, 14), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(633, 45), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.ImageView2DHud_0.LabelButtons_6', event , 108.70782 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(301, 110), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(612, 137), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 108.876754 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(304, 149), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(615, 176), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 109.014151 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(310, 149), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(619, 174), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 109.174085 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(308, 150), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(619, 177), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 109.752998 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(306, 169), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(617, 196), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 109.888008 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(306, 170), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(617, 197), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 110.051833 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(306, 178), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(617, 205), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 110.217099 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(306, 179), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(617, 206), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 110.530188 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(304, 188), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(615, 215), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 110.68955 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(303, 194), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(614, 221), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 110.824969 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000021, (Qt.ControlModifier), """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0', event , 111.987408 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(303, 194), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(614, 221), 120, Qt.NoButton, (Qt.ControlModifier), 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 112.248588 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(303, 194), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(614, 221), 120, Qt.NoButton, (Qt.ControlModifier), 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 112.894085 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(303, 194), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(614, 221), 240, Qt.NoButton, (Qt.ControlModifier), 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 113.087042 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(303, 194), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(614, 221), 240, Qt.NoButton, (Qt.ControlModifier), 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 113.242784 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000021, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0', event , 113.955806 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(303, 194), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(614, 221), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 114.43013 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(303, 194), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(614, 221), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 114.935318 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(303, 194), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(614, 221), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 115.263302 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(303, 194), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(614, 221), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 115.471598 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(303, 194), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(614, 221), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 115.669604 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(303, 194), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(614, 221), -240, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 115.849697 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(303, 194), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(614, 221), -240, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 116.041368 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(303, 194), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(614, 221), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 116.859058 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(303, 194), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(614, 221), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 117.081363 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(289, 201), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(600, 228), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 122.092859 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(21, 396), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(332, 423), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 122.234581 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(13, 11), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(25, 523), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_3_lane_0.layerWidget.qt_scrollarea_viewport.LayerItemWidget_Binary image.ToggleEye_0', event , 123.41785 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(13, 11), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(25, 523), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_3_lane_0.layerWidget.qt_scrollarea_viewport.LayerItemWidget_Binary image.ToggleEye_0', event , 123.721696 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(25, 369), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(336, 396), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 124.097861 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(151, 318), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(462, 345), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 124.253982 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(229, 296), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(540, 323), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 124.403515 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(273, 286), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(584, 313), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 124.575661 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 124.725559 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 125.015272 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), -840, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 125.201575 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), -600, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 125.361652 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 126.016921 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), -360, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 126.210225 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 126.418313 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), -240, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 126.573572 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 127.209253 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 127.407382 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), -240, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 127.535262 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), -240, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 127.735809 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 128.328068 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 128.594221 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 128.814006 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), -480, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 128.968534 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 129.168771 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 129.973546 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 130.206422 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 130.408813 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), -240, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 130.61771 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), -240, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 130.829571 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 131.255384 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 131.461778 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), -240, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 131.675246 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), -360, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 131.889837 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 132.484821 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 132.669547 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), -240, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 132.889813 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), -240, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 133.039992 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 133.236255 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 133.705362 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 133.906002 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), -240, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 134.114445 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), -360, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 134.271222 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 135.089796 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 135.304379 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 135.529958 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 135.692039 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 135.860176 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 135.99587 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 136.148253 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 137.836735 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), 360, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 138.03395 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 138.24427 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), 480, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 138.402691 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 138.99114 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 139.223029 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), 360, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 139.436179 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), 240, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 139.581572 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 140.258679 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 140.456567 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), 480, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 140.667601 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 140.880214 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 141.299213 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), 1440, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 141.510828 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 142.278492 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 142.491391 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 142.681314 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 142.861923 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 143.037434 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 143.232428 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 143.437059 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 143.640963 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 144.130032 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 144.327477 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), 240, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 144.533843 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 144.741391 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 144.947708 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 145.460101 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 145.632157 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), 240, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 145.853809 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(276, 285), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 312), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 146.068433 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(273, 282), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(584, 309), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 148.472939 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(255, 279), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(566, 306), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 148.619466 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(132, 245), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(443, 272), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 148.766347 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(15, 232), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(326, 259), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 148.927776 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(1, 221), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(310, 246), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0', event , 149.181738 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(168, 217), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(479, 244), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 149.341091 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(231, 222), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(542, 249), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 149.484102 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(240, 228), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(551, 255), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 149.655617 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(241, 228), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(552, 255), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 149.884761 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(204, 231), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(515, 258), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 150.045976 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(53, 48), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(70, 220), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.QTableView_0.qt_scrollarea_viewport', event , 150.650272 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(53, 48), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(70, 220), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.QTableView_0.qt_scrollarea_viewport', event , 150.796476 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(13, 220), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(324, 247), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 151.00117 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(268, 239), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(579, 266), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 151.156646 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(290, 237), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(601, 264), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 151.316789 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(302, 245), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(613, 272), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 151.464562 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(300, 245), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(611, 272), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 151.64881 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(300, 245), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(611, 272), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 153.492702 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(300, 245), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(611, 272), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 154.051583 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(298, 247), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(609, 274), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 154.281092 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(298, 248), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(609, 275), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 154.57372 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(281, 248), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(592, 275), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 154.735996 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(281, 247), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(592, 274), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 155.741514 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(291, 237), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(602, 264), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 155.882183 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(29, 170), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(340, 197), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 156.070087 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(49, 14), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(66, 186), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.QTableView_0.qt_scrollarea_viewport', event , 156.618697 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(49, 14), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(66, 186), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.QTableView_0.qt_scrollarea_viewport', event , 156.824139 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(72, 188), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(383, 215), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 156.960765 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(345, 183), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(656, 210), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 157.130717 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(373, 166), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(684, 193), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 157.280096 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(401, 156), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(712, 183), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 157.440498 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(402, 147), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(713, 174), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 157.61295 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(402, 147), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(713, 174), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 157.753452 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(402, 147), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(713, 174), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 157.920072 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(340, 215), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(651, 242), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 158.146374 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(297, 201), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(608, 228), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 158.312612 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 158.498772 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 159.377338 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 160.265531 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 160.463217 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 160.683685 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -240, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 160.899418 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 161.572042 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 161.789422 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 162.011841 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 162.754166 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 162.986426 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 163.208266 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 163.428189 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 163.637188 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 164.041381 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 164.299219 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 164.592564 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 164.819826 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 165.033713 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 165.274509 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 165.854498 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -360, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 166.060181 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -240, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 166.275517 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 166.934501 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 167.154742 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 167.371717 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 167.582218 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 167.791972 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 167.997751 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 168.208654 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 168.623462 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 168.858142 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 169.125362 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 169.374756 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 169.594488 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 169.813201 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 170.034138 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 170.434248 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 170.722473 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -480, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 170.927636 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 171.603277 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -360, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 171.796822 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 172.014639 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 172.656147 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 172.85373 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 173.613661 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), 2760, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 173.78411 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), 600, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 173.930515 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), 3480, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 174.144788 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), 600, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 174.305666 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), 3720, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 174.511508 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), 480, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 174.717334 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), 2520, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 174.851727 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), 480, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 175.037359 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 175.58667 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -240, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 175.779055 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 175.997852 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 176.200009 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 176.465186 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 176.67672 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -240, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 176.885449 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -240, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 177.087496 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 177.247013 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 177.987884 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 178.285767 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 178.568737 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 178.815634 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 179.309726 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 179.645576 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 180.271627 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 180.584441 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 180.876008 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 181.132235 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 181.386516 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 181.776551 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 182.379446 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 182.695238 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 183.020805 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 183.791535 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 184.150187 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 184.347628 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 184.596345 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 184.827828 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(280, 193), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 220), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 185.382716 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(261, 191), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(572, 218), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 187.273545 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(36, 186), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(347, 213), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 187.440659 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(10, 168), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(321, 195), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 188.368276 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(215, 130), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(526, 157), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 188.532656 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(277, 75), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(588, 102), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 188.691374 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(267, 77), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(578, 104), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 188.836975 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(248, 85), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(559, 112), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 189.010215 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(244, 85), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(555, 112), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 189.166033 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(240, 83), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(551, 110), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 189.310897 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(240, 81), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(551, 108), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 189.476032 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(240, 81), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(551, 108), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 189.609936 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(240, 81), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(551, 108), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 189.779856 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(219, 100), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(530, 127), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 189.920719 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(199, 103), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(510, 130), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 190.082122 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(197, 103), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(508, 130), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 190.546983 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(57, 105), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(368, 132), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 190.709687 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(19, 8), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(34, 160), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.label', event , 191.194763 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(62, 43), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(79, 215), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.QTableView_0.qt_scrollarea_viewport', event , 191.923234 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(62, 43), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(79, 215), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.QTableView_0.qt_scrollarea_viewport', event , 192.136604 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(3, 187), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(314, 214), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 192.341626 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(209, 176), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(520, 203), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 192.495028 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(269, 176), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(580, 203), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 192.660506 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(363, 176), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(674, 203), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 192.801838 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(379, 177), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(690, 204), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 192.985508 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(431, 176), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(742, 203), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 193.160096 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(444, 182), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(755, 209), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 193.298689 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(443, 185), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(754, 212), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 193.473476 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(445, 183), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(756, 210), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 193.639956 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(446, 183), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(757, 210), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 193.798612 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(446, 183), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(757, 210), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 193.954805 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(446, 183), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(757, 210), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 194.191054 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(446, 184), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(757, 211), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 194.439391 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(445, 185), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(756, 212), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 194.602473 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(442, 186), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(753, 213), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 194.747777 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(429, 187), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(740, 214), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 194.913194 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(399, 187), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(710, 214), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 195.070333 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(376, 188), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(687, 215), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 195.222279 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(70, 167), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(381, 194), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 195.398418 )

    ########################
    player.display_comment("""Well that took some time...""")
    ########################

    ########################
    player.display_comment("""Now live predict!""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(179, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(179, 12), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 196.16207 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(15, 59), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(303, 201), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_vcontainer.QScrollBar_0', event , 196.357503 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(2, 200), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(313, 227), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 196.490155 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(6, 70), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(294, 212), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_vcontainer.QScrollBar_0', event , 196.881049 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(6, 70), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(294, 212), -960, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_vcontainer.QScrollBar_0', event , 197.08687 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(156, 13), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(276, 223), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.checkShowPredictions', event , 197.55486 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(127, 13), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(247, 223), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.checkShowPredictions', event , 197.706636 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(116, 4), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(236, 214), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.checkShowPredictions', event , 197.845178 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(107, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(227, 210), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.checkShowPredictions', event , 198.096555 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(124, 17), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(244, 227), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.checkShowPredictions', event , 198.248849 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(279, 245), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(285, 241), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget', event , 198.430924 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(279, 245), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(285, 241), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget', event , 198.561573 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(19, 16), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(139, 226), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.checkShowPredictions', event , 198.897857 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(72, 11), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(87, 221), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.checkInteractive', event , 199.027504 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(65, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(80, 222), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.checkInteractive', event , 199.185128 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(62, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(77, 222), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.checkInteractive', event , 199.333398 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(62, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(77, 222), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.checkInteractive', event , 199.487887 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(62, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(77, 222), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.checkInteractive', event , 199.61765 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(61, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(76, 222), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.checkInteractive', event , 202.002136 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(59, 10), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(74, 220), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.checkInteractive', event , 202.135875 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(57, 9), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(72, 219), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.checkInteractive', event , 202.288077 )

    ########################
    player.display_comment("""We\'re done here.""")
    ########################

    player.display_comment("SCRIPT COMPLETE")
