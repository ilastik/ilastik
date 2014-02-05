
# Event Recording
# Created by Stuart
# Started at: 2014-01-20 21:39:13.252014

def playback_events(player):
    import PyQt4.QtCore
    from PyQt4.QtCore import Qt, QEvent, QPoint
    import PyQt4.QtGui
    
    # The getMainWindow() function is provided by EventRecorderApp
    mainwin = PyQt4.QtGui.QApplication.instance().getMainWindow()

    player.display_comment("SCRIPT STARTING")


    event = PyQt4.QtGui.QResizeEvent(PyQt4.QtCore.QSize(1000, 650), PyQt4.QtCore.QSize(1000, 750))
    player.post_event( 'MainWindow', event , 0.640381 )

    ########################
    player.display_comment("""New Project (Layer Viewer)""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(191, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(191, 0), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 1.085583 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(95, 19), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(406, 320), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.startupPage.frame.CreateList.qt_scrollarea_viewport.scrollAreaWidgetContents.QToolButton_7', event , 1.785018 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(95, 19), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(406, 320), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.startupPage.frame.CreateList.qt_scrollarea_viewport.scrollAreaWidgetContents.QToolButton_7', event , 1.878707 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000004, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.QFileDialog.fileNameEdit', event , 3.384895 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000004, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.QFileDialog', event , 4.296722 )

    ########################
    player.display_comment("""Add raw data""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(45, 7), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(367, 91), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport.QWidget_0.AddFileButton_0', event , 4.877207 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(45, -19), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(367, 91), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 4.99824 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(45, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(367, 110), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 5.517488 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(45, 3), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(367, 113), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 5.581525 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(44, 5), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(366, 115), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 5.646348 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(44, 7), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(366, 117), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 5.710601 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(44, 8), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(366, 118), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 5.77277 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(43, 9), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(365, 119), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 5.834668 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(43, 9), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(365, 119), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 5.935056 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(43, 9), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(365, 119), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 6.000737 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2f, Qt.NoModifier, """/""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 8.695101 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2f, Qt.NoModifier, """/""", False, 1)
    player.post_event( 'QListView_0', event , 8.765378 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x48, Qt.NoModifier, """h""", False, 1)
    player.post_event( 'QListView_0', event , 9.52128 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x48, Qt.NoModifier, """h""", False, 1)
    player.post_event( 'QListView_0', event , 9.597416 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4f, Qt.NoModifier, """o""", False, 1)
    player.post_event( 'QListView_0', event , 9.687272 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4d, Qt.NoModifier, """m""", False, 1)
    player.post_event( 'QListView_0', event , 9.759429 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4f, Qt.NoModifier, """o""", False, 1)
    player.post_event( 'QListView_0', event , 9.822326 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'QListView_0', event , 9.877055 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4d, Qt.NoModifier, """m""", False, 1)
    player.post_event( 'QListView_0', event , 9.933105 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'QListView_0', event , 9.988712 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2f, Qt.NoModifier, """/""", False, 1)
    player.post_event( 'QListView_0', event , 10.042768 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2f, Qt.NoModifier, """/""", False, 1)
    player.post_event( 'QListView_0', event , 10.098594 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x56, Qt.NoModifier, """v""", False, 1)
    player.post_event( 'QListView_0', event , 10.305507 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x56, Qt.NoModifier, """v""", False, 1)
    player.post_event( 'QListView_0', event , 10.403442 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'QListView_0', event , 10.464902 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'QListView_0', event , 10.576867 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x47, Qt.NoModifier, """g""", False, 1)
    player.post_event( 'QListView_0', event , 10.631355 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x47, Qt.NoModifier, """g""", False, 1)
    player.post_event( 'QListView_0', event , 10.691366 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x52, Qt.NoModifier, """r""", False, 1)
    player.post_event( 'QListView_0', event , 10.748408 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'QListView_0', event , 10.821747 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x52, Qt.NoModifier, """r""", False, 1)
    player.post_event( 'QListView_0', event , 10.880459 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'QListView_0', event , 10.953934 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'QListView_0', event , 11.011319 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'QListView_0', event , 11.067296 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'QListView_0', event , 11.121746 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'QListView_0', event , 11.181005 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2f, Qt.NoModifier, """/""", False, 1)
    player.post_event( 'QListView_0', event , 11.250151 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2f, Qt.NoModifier, """/""", False, 1)
    player.post_event( 'QListView_0', event , 11.366325 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x46, Qt.NoModifier, """f""", False, 1)
    player.post_event( 'QListView_0', event , 11.928846 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x46, Qt.NoModifier, """f""", False, 1)
    player.post_event( 'QListView_0', event , 12.024036 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'QListView_0', event , 12.079463 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'QListView_0', event , 12.165113 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4b, Qt.NoModifier, """k""", False, 1)
    player.post_event( 'QListView_0', event , 12.350357 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'QListView_0', event , 12.429461 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4b, Qt.NoModifier, """k""", False, 1)
    player.post_event( 'QListView_0', event , 12.485774 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'QListView_0', event , 12.540665 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1)
    player.post_event( 'QListView_0', event , 12.61275 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'QListView_0', event , 12.70273 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1)
    player.post_event( 'QListView_0', event , 12.767432 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2d, Qt.NoModifier, """-""", False, 1)
    player.post_event( 'QListView_0', event , 12.824079 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'QListView_0', event , 12.975649 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'QListView_0', event , 13.034855 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'QListView_0', event , 13.122134 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'QListView_0', event , 13.180078 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x53, Qt.NoModifier, """s""", False, 1)
    player.post_event( 'QListView_0', event , 13.430668 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'QListView_0', event , 13.557965 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x53, Qt.NoModifier, """s""", False, 1)
    player.post_event( 'QListView_0', event , 13.614243 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'QListView_0', event , 13.66934 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1)
    player.post_event( 'QListView_0', event , 13.830619 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x3f, (Qt.ShiftModifier), """?""", False, 1)
    player.post_event( 'QListView_0', event , 13.934393 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(47, 56), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(365, 119), Qt.NoButton, Qt.NoButton, (Qt.ShiftModifier))
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport', event , 13.999371 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 14.061751 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2f, Qt.NoModifier, """/""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 14.12178 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x44, Qt.NoModifier, """d""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 14.181861 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x44, Qt.NoModifier, """d""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 14.243251 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 14.303615 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 14.363846 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 14.42695 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 14.490729 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 14.55243 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 14.612121 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000003, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 14.670668 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000003, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 14.728416 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000003, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 14.786695 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000003, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 14.838912 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000003, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 14.901121 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000003, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 14.958861 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000003, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 15.02724 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000003, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 15.107036 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000003, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 15.391731 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000003, Qt.NoModifier, """""", False, 1)
    player.post_event( 'QListView_0', event , 15.480886 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2f, Qt.NoModifier, """/""", False, 1)
    player.post_event( 'QListView_0', event , 15.918342 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2f, Qt.NoModifier, """/""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 15.973023 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x44, Qt.NoModifier, """d""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 16.094837 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x44, Qt.NoModifier, """d""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 16.170442 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 16.227575 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 16.284639 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 16.341945 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 16.398286 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 16.44949 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 16.512054 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000003, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 17.439184 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000003, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 17.499771 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000003, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 17.560006 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000003, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 17.620682 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000003, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 17.682356 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000003, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 17.739549 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000003, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 17.917577 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000003, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 17.97551 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000003, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 18.351743 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000003, Qt.NoModifier, """""", False, 1)
    player.post_event( 'QListView_0', event , 18.414841 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1)
    player.post_event( 'QListView_0', event , 18.612112 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'QListView_0', event , 18.676888 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'QListView_0', event , 18.735734 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1)
    player.post_event( 'QListView_0', event , 18.79339 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x44, Qt.NoModifier, """d""", False, 1)
    player.post_event( 'QListView_0', event , 18.950457 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x44, Qt.NoModifier, """d""", False, 1)
    player.post_event( 'QListView_0', event , 19.027611 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'QListView_0', event , 19.082472 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'QListView_0', event , 19.138741 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'QListView_0', event , 19.193857 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'QListView_0', event , 19.251693 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'QListView_0', event , 19.311312 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'QListView_0', event , 19.370175 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2f, Qt.NoModifier, """/""", False, 1)
    player.post_event( 'QListView_0', event , 19.441502 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2f, Qt.NoModifier, """/""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 19.497285 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000004, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 20.127929 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000004, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 20.186021 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x43, Qt.NoModifier, """c""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 21.45386 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x55, Qt.NoModifier, """u""", False, 1)
    player.post_event( 'QListView_0', event , 21.517688 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x55, Qt.NoModifier, """u""", False, 1)
    player.post_event( 'QListView_0', event , 21.577141 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x43, Qt.NoModifier, """c""", False, 1)
    player.post_event( 'QListView_0', event , 21.631259 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x42, Qt.NoModifier, """b""", False, 1)
    player.post_event( 'QListView_0', event , 21.685814 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x42, Qt.NoModifier, """b""", False, 1)
    player.post_event( 'QListView_0', event , 21.74497 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'QListView_0', event , 21.803875 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'QListView_0', event , 21.86212 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1)
    player.post_event( 'QListView_0', event , 21.981559 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'QListView_0', event , 22.036086 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'QListView_0', event , 22.112557 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1)
    player.post_event( 'QListView_0', event , 22.165957 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4f, Qt.NoModifier, """o""", False, 1)
    player.post_event( 'QListView_0', event , 22.251843 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4f, Qt.NoModifier, """o""", False, 1)
    player.post_event( 'QListView_0', event , 22.318672 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x42, Qt.NoModifier, """b""", False, 1)
    player.post_event( 'QListView_0', event , 22.410614 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x42, Qt.NoModifier, """b""", False, 1)
    player.post_event( 'QListView_0', event , 22.470207 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4a, Qt.NoModifier, """j""", False, 1)
    player.post_event( 'QListView_0', event , 22.551072 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'QListView_0', event , 22.60864 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x43, Qt.NoModifier, """c""", False, 1)
    player.post_event( 'QListView_0', event , 22.667764 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4a, Qt.NoModifier, """j""", False, 1)
    player.post_event( 'QListView_0', event , 22.72666 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'QListView_0', event , 22.783264 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x43, Qt.NoModifier, """c""", False, 1)
    player.post_event( 'QListView_0', event , 22.840074 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'QListView_0', event , 22.898644 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'QListView_0', event , 22.957805 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x53, Qt.NoModifier, """s""", False, 1)
    player.post_event( 'QListView_0', event , 23.014871 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x53, Qt.NoModifier, """s""", False, 1)
    player.post_event( 'QListView_0', event , 23.075271 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1)
    player.post_event( 'QListView_0', event , 23.131926 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'QListView_0', event , 23.190346 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'QListView_0', event , 23.254387 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1)
    player.post_event( 'QListView_0', event , 23.346101 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x52, Qt.NoModifier, """r""", False, 1)
    player.post_event( 'QListView_0', event , 24.44518 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'QListView_0', event , 24.513767 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x52, Qt.NoModifier, """r""", False, 1)
    player.post_event( 'QListView_0', event , 24.569873 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x57, Qt.NoModifier, """w""", False, 1)
    player.post_event( 'QListView_0', event , 24.624824 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'QListView_0', event , 24.68179 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x57, Qt.NoModifier, """w""", False, 1)
    player.post_event( 'QListView_0', event , 24.736888 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2e, Qt.NoModifier, """.""", False, 1)
    player.post_event( 'QListView_0', event , 24.79062 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2e, Qt.NoModifier, """.""", False, 1)
    player.post_event( 'QListView_0', event , 24.858914 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'QListView_0', event , 25.018708 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'QListView_0', event , 25.074833 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x50, Qt.NoModifier, """p""", False, 1)
    player.post_event( 'QListView_0', event , 25.159654 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x50, Qt.NoModifier, """p""", False, 1)
    player.post_event( 'QListView_0', event , 25.231239 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x59, Qt.NoModifier, """y""", False, 1)
    player.post_event( 'QListView_0', event , 25.321309 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x59, Qt.NoModifier, """y""", False, 1)
    player.post_event( 'QListView_0', event , 25.397921 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000004, Qt.NoModifier, """""", False, 1)
    player.post_event( 'QListView_0', event , 25.515884 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(47, 56), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(365, 119), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport', event , 25.59206 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(45, 62), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(365, 119), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1', event , 25.998494 )

    ########################
    player.display_comment("""Add binary data (start with the wrong file)""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(347, 3), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(347, 3), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 27.478252 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(78, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(418, 59), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.QHeaderView_1.qt_scrollarea_viewport', event , 27.566598 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(103, 22), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(443, 81), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.QHeaderView_1.qt_scrollarea_viewport', event , 27.651503 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(107, 6), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(447, 88), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport', event , 27.731939 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(113, 9), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(453, 91), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport', event , 27.819679 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(121, 10), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(461, 92), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport', event , 27.900884 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(122, 10), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(462, 92), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport', event , 28.26869 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(139, 13), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(479, 95), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport', event , 28.350037 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(149, 16), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(489, 98), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport', event , 28.438272 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(154, 16), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(494, 98), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport', event , 28.516788 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(158, 15), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(498, 97), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport', event , 28.602189 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(161, 21), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(501, 80), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.QHeaderView_1.qt_scrollarea_viewport', event , 28.685663 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(131, 10), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(449, 44), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_tabbar', event , 28.948535 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(131, 10), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(449, 44), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_tabbar', event , 29.046198 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(131, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(471, 59), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QHeaderView_1.qt_scrollarea_viewport', event , 29.299906 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(155, 21), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(495, 80), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QHeaderView_1.qt_scrollarea_viewport', event , 29.396574 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(155, 4), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(495, 86), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport', event , 29.480718 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(155, 6), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(495, 88), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport', event , 29.562252 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(155, 6), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(495, 88), (Qt.RightButton), (Qt.RightButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport', event , 29.741872 )

    event = PyQt4.QtGui.QContextMenuEvent(0, PyQt4.QtCore.QPoint(155, 6), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(495, 88), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport', event , 29.813475 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(495, 88), (Qt.RightButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_0', event , 29.907413 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(495, 88), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_0', event , 29.987913 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(-1, 1), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(494, 89), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_0', event , 30.261062 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(-1, 1), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(494, 89), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_0', event , 30.348199 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(-1, 1), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(494, 89), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_0', event , 30.43062 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(1, 2), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(496, 90), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_0', event , 30.507541 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(10, 17), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(505, 105), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_0', event , 30.588969 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(9, 17), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(504, 105), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_0', event , 31.16918 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(2, 19), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(497, 107), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_0', event , 31.251877 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(16, 27), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(511, 115), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_0', event , 31.331471 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(29, 32), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(524, 120), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_0', event , 31.429242 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(29, 32), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(524, 120), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_0', event , 31.550529 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(29, 32), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(524, 120), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_0', event , 31.625538 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x43, Qt.NoModifier, """c""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 33.02578 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x55, Qt.NoModifier, """u""", False, 1)
    player.post_event( 'QListView_0', event , 33.10495 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x55, Qt.NoModifier, """u""", False, 1)
    player.post_event( 'QListView_0', event , 33.180158 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x43, Qt.NoModifier, """c""", False, 1)
    player.post_event( 'QListView_0', event , 33.248307 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x42, Qt.NoModifier, """b""", False, 1)
    player.post_event( 'QListView_0', event , 33.316162 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x42, Qt.NoModifier, """b""", False, 1)
    player.post_event( 'QListView_0', event , 33.389202 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'QListView_0', event , 33.456189 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'QListView_0', event , 33.528134 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1)
    player.post_event( 'QListView_0', event , 33.733202 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'QListView_0', event , 33.860065 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'QListView_0', event , 33.927787 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1)
    player.post_event( 'QListView_0', event , 33.992092 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000003, Qt.NoModifier, """""", False, 1)
    player.post_event( 'QListView_0', event , 34.520311 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000003, Qt.NoModifier, """""", False, 1)
    player.post_event( 'QListView_0', event , 34.599984 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1)
    player.post_event( 'QListView_0', event , 35.189284 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'QListView_0', event , 35.263302 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'QListView_0', event , 35.333176 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1)
    player.post_event( 'QListView_0', event , 35.397614 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4f, Qt.NoModifier, """o""", False, 1)
    player.post_event( 'QListView_0', event , 35.463458 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4f, Qt.NoModifier, """o""", False, 1)
    player.post_event( 'QListView_0', event , 35.53042 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x42, Qt.NoModifier, """b""", False, 1)
    player.post_event( 'QListView_0', event , 35.660362 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x42, Qt.NoModifier, """b""", False, 1)
    player.post_event( 'QListView_0', event , 35.727432 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4a, Qt.NoModifier, """j""", False, 1)
    player.post_event( 'QListView_0', event , 35.816999 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4a, Qt.NoModifier, """j""", False, 1)
    player.post_event( 'QListView_0', event , 35.902294 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'QListView_0', event , 35.970099 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x43, Qt.NoModifier, """c""", False, 1)
    player.post_event( 'QListView_0', event , 36.040143 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'QListView_0', event , 36.107703 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x43, Qt.NoModifier, """c""", False, 1)
    player.post_event( 'QListView_0', event , 36.172507 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'QListView_0', event , 36.243427 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'QListView_0', event , 36.312535 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x53, Qt.NoModifier, """s""", False, 1)
    player.post_event( 'QListView_0', event , 36.377999 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x53, Qt.NoModifier, """s""", False, 1)
    player.post_event( 'QListView_0', event , 36.446859 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1)
    player.post_event( 'QListView_0', event , 37.047367 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'QListView_0', event , 37.160045 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'QListView_0', event , 37.270251 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1)
    player.post_event( 'QListView_0', event , 37.341164 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x52, Qt.NoModifier, """r""", False, 1)
    player.post_event( 'QListView_0', event , 37.794252 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'QListView_0', event , 37.886153 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x52, Qt.NoModifier, """r""", False, 1)
    player.post_event( 'QListView_0', event , 37.955975 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x57, Qt.NoModifier, """w""", False, 1)
    player.post_event( 'QListView_0', event , 38.020972 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'QListView_0', event , 38.088161 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2e, Qt.NoModifier, """.""", False, 1)
    player.post_event( 'QListView_0', event , 38.155548 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x57, Qt.NoModifier, """w""", False, 1)
    player.post_event( 'QListView_0', event , 38.225209 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2e, Qt.NoModifier, """.""", False, 1)
    player.post_event( 'QListView_0', event , 38.294035 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'QListView_0', event , 38.363926 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'QListView_0', event , 38.434061 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x50, Qt.NoModifier, """p""", False, 1)
    player.post_event( 'QListView_0', event , 38.517419 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x50, Qt.NoModifier, """p""", False, 1)
    player.post_event( 'QListView_0', event , 38.6234 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x59, Qt.NoModifier, """y""", False, 1)
    player.post_event( 'QListView_0', event , 38.701103 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x59, Qt.NoModifier, """y""", False, 1)
    player.post_event( 'QListView_0', event , 38.772882 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000004, Qt.NoModifier, """""", False, 1)
    player.post_event( 'QListView_0', event , 38.912192 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(181, 1), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(499, 127), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0', event , 40.579061 )

    ########################
    player.display_comment("""Now replace the incorrect file.""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(147, 18), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(487, 100), (Qt.RightButton), (Qt.RightButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport', event , 41.164264 )

    event = PyQt4.QtGui.QContextMenuEvent(0, PyQt4.QtCore.QPoint(147, 18), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(487, 100), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport', event , 41.255614 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(487, 100), (Qt.RightButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_1', event , 41.412788 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(487, 100), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_1', event , 41.517058 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(2, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(489, 100), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_1', event , 41.863245 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(17, 7), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(504, 107), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_1', event , 41.960614 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(21, 15), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(508, 115), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_1', event , 42.051171 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(23, 21), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(510, 121), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_1', event , 42.139551 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(23, 22), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(510, 122), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_1', event , 42.494664 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(23, 32), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(510, 132), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_1', event , 42.59051 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(23, 33), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(510, 133), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_1', event , 42.681414 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(23, 33), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(510, 133), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_1', event , 42.767832 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(23, 33), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(510, 133), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_1', event , 42.863085 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x43, Qt.NoModifier, """c""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 44.118167 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x55, Qt.NoModifier, """u""", False, 1)
    player.post_event( 'QListView_0', event , 44.207219 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x43, Qt.NoModifier, """c""", False, 1)
    player.post_event( 'QListView_0', event , 44.292859 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x55, Qt.NoModifier, """u""", False, 1)
    player.post_event( 'QListView_0', event , 44.364056 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x42, Qt.NoModifier, """b""", False, 1)
    player.post_event( 'QListView_0', event , 44.438453 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x42, Qt.NoModifier, """b""", False, 1)
    player.post_event( 'QListView_0', event , 44.518753 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'QListView_0', event , 44.590151 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'QListView_0', event , 44.66375 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1)
    player.post_event( 'QListView_0', event , 44.745476 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'QListView_0', event , 44.819012 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'QListView_0', event , 44.895621 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1)
    player.post_event( 'QListView_0', event , 44.977538 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4f, Qt.NoModifier, """o""", False, 1)
    player.post_event( 'QListView_0', event , 45.048299 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4f, Qt.NoModifier, """o""", False, 1)
    player.post_event( 'QListView_0', event , 45.121738 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x42, Qt.NoModifier, """b""", False, 1)
    player.post_event( 'QListView_0', event , 45.204566 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x42, Qt.NoModifier, """b""", False, 1)
    player.post_event( 'QListView_0', event , 45.278145 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4a, Qt.NoModifier, """j""", False, 1)
    player.post_event( 'QListView_0', event , 45.348857 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'QListView_0', event , 45.430134 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4a, Qt.NoModifier, """j""", False, 1)
    player.post_event( 'QListView_0', event , 45.503203 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x43, Qt.NoModifier, """c""", False, 1)
    player.post_event( 'QListView_0', event , 45.578652 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'QListView_0', event , 45.658523 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x43, Qt.NoModifier, """c""", False, 1)
    player.post_event( 'QListView_0', event , 45.730721 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'QListView_0', event , 45.801857 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'QListView_0', event , 45.881826 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x53, Qt.NoModifier, """s""", False, 1)
    player.post_event( 'QListView_0', event , 45.951996 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x53, Qt.NoModifier, """s""", False, 1)
    player.post_event( 'QListView_0', event , 46.024884 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1)
    player.post_event( 'QListView_0', event , 46.102184 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'QListView_0', event , 46.969548 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'QListView_0', event , 47.04759 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1)
    player.post_event( 'QListView_0', event , 47.198443 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x42, Qt.NoModifier, """b""", False, 1)
    player.post_event( 'QListView_0', event , 47.303069 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x42, Qt.NoModifier, """b""", False, 1)
    player.post_event( 'QListView_0', event , 47.388311 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x49, Qt.NoModifier, """i""", False, 1)
    player.post_event( 'QListView_0', event , 47.460145 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'QListView_0', event , 47.532877 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'QListView_0', event , 47.615376 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x49, Qt.NoModifier, """i""", False, 1)
    player.post_event( 'QListView_0', event , 47.68642 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'QListView_0', event , 47.758331 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x52, Qt.NoModifier, """r""", False, 1)
    player.post_event( 'QListView_0', event , 47.838279 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'QListView_0', event , 47.911255 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x59, Qt.NoModifier, """y""", False, 1)
    player.post_event( 'QListView_0', event , 47.98317 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x52, Qt.NoModifier, """r""", False, 1)
    player.post_event( 'QListView_0', event , 48.062431 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x59, Qt.NoModifier, """y""", False, 1)
    player.post_event( 'QListView_0', event , 48.134359 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2e, Qt.NoModifier, """.""", False, 1)
    player.post_event( 'QListView_0', event , 48.205997 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2e, Qt.NoModifier, """.""", False, 1)
    player.post_event( 'QListView_0', event , 48.287321 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'QListView_0', event , 48.358347 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'QListView_0', event , 48.437644 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x50, Qt.NoModifier, """p""", False, 1)
    player.post_event( 'QListView_0', event , 48.516044 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x50, Qt.NoModifier, """p""", False, 1)
    player.post_event( 'QListView_0', event , 48.590285 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x59, Qt.NoModifier, """y""", False, 1)
    player.post_event( 'QListView_0', event , 48.663874 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x59, Qt.NoModifier, """y""", False, 1)
    player.post_event( 'QListView_0', event , 48.749829 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000004, Qt.NoModifier, """""", False, 1)
    player.post_event( 'QListView_0', event , 49.747205 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000004, Qt.NoModifier, """""", False, 1)
    player.post_event( 'QListView_0', event , 49.88418 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(12, 17), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(483, 149), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.ImageView2DHud_0.LabelButtons_2', event , 51.361464 )

    ########################
    player.display_comment("""Edit binary data properties: axis order""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(152, 6), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(492, 88), (Qt.RightButton), (Qt.RightButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport', event , 51.784303 )

    event = PyQt4.QtGui.QContextMenuEvent(0, PyQt4.QtCore.QPoint(152, 6), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(492, 88), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport', event , 51.867759 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(492, 88), (Qt.RightButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_2', event , 52.046002 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(492, 88), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_2', event , 52.135926 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(1, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(493, 88), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_2', event , 52.446614 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(12, 7), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(504, 95), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_2', event , 52.532399 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(13, 9), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(505, 97), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_2', event , 52.625555 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(14, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(506, 100), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_2', event , 52.712172 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(14, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(506, 100), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_2', event , 52.896617 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(14, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(506, 100), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_2', event , 53.009705 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(32, 2), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(505, 136), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.rangeMaxSpinBox.qt_spinbox_lineedit', event , 53.934771 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(247, 16), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(510, 232), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.storageComboBox', event , 54.422286 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(247, -4), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(510, 232), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.storageComboBox.QFrame_0', event , 54.561666 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(150, -93), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(413, 143), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.storageComboBox.QFrame_0', event , 56.80826 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(122, -114), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(385, 122), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.storageComboBox.QFrame_0', event , 57.137243 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(122, -114), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(385, 122), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.storageComboBox.QFrame_0', event , 57.22388 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(126, 17), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(389, 119), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.axesEdit', event , 57.33506 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(126, 17), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(389, 119), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.axesEdit', event , 57.429504 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(80, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(343, 114), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.axesEdit', event , 57.524647 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(79, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(342, 114), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.axesEdit', event , 57.761108 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(79, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(342, 114), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.axesEdit', event , 57.851247 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(79, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(342, 114), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.axesEdit', event , 57.943055 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000003, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.axesEdit', event , 58.714595 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000003, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.axesEdit', event , 58.799484 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000003, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.axesEdit', event , 58.885117 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000003, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.axesEdit', event , 58.964804 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000003, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.axesEdit', event , 59.048571 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000003, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.axesEdit', event , 59.135807 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000003, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.axesEdit', event , 59.631802 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000003, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.axesEdit', event , 59.71548 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5a, Qt.NoModifier, """z""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.axesEdit', event , 60.007377 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x5a, Qt.NoModifier, """z""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.axesEdit', event , 60.115021 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x59, Qt.NoModifier, """y""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.axesEdit', event , 60.313058 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x59, Qt.NoModifier, """y""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.axesEdit', event , 60.404573 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x58, Qt.NoModifier, """x""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.axesEdit', event , 60.511331 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x58, Qt.NoModifier, """x""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.axesEdit', event , 60.603446 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(82, 14), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(345, 116), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.axesEdit', event , 61.863298 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(763, 560), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(856, 582), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1', event , 62.631627 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(763, 560), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(856, 582), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1', event , 62.714471 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(39, 11), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(858, 597), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.okButton', event , 62.965896 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(39, 11), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(858, 597), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.okButton', event , 63.106907 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(251, 526), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(344, 548), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1', event , 63.390394 )

    ########################
    player.display_comment("""Edit properties again: absolute link""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(193, 15), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(533, 97), (Qt.RightButton), (Qt.RightButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport', event , 63.953061 )

    event = PyQt4.QtGui.QContextMenuEvent(0, PyQt4.QtCore.QPoint(193, 15), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(533, 97), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport', event , 64.033369 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(0, 1), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(533, 98), Qt.NoButton, (Qt.RightButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_3', event , 64.197042 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(0, 1), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(533, 98), (Qt.RightButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_3', event , 64.283496 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(0, 1), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(533, 98), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_3', event , 64.388633 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(13, 3), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(546, 100), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_3', event , 64.475148 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(24, 10), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(557, 107), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_3', event , 64.578203 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(25, 15), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(558, 112), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_3', event , 64.66547 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(26, 19), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(559, 116), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_3', event , 64.754554 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(26, 19), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(559, 116), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_3', event , 64.847916 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(26, 19), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(559, 116), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_3', event , 64.934211 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(82, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(555, 134), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.rangeMaxSpinBox.qt_spinbox_lineedit', event , 65.77086 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(261, 8), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(524, 224), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.storageComboBox', event , 66.241642 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(261, -12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(524, 224), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.storageComboBox.QFrame_0', event , 66.377752 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(247, 1), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(512, 239), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.storageComboBox.QFrame_0.QListView_0.qt_scrollarea_viewport', event , 66.885705 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(243, 8), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(508, 246), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.storageComboBox.QFrame_0.QListView_0.qt_scrollarea_viewport', event , 66.9889 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(242, 11), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(507, 249), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.storageComboBox.QFrame_0.QListView_0.qt_scrollarea_viewport', event , 67.099016 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(238, 16), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(503, 254), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.storageComboBox.QFrame_0.QListView_0.qt_scrollarea_viewport', event , 67.199966 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(238, 18), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(503, 256), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.storageComboBox.QFrame_0.QListView_0.qt_scrollarea_viewport', event , 67.29121 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(237, 19), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(502, 257), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.storageComboBox.QFrame_0.QListView_0.qt_scrollarea_viewport', event , 67.420921 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(236, 20), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(501, 258), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.storageComboBox.QFrame_0.QListView_0.qt_scrollarea_viewport', event , 67.51439 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(236, 20), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(501, 258), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.storageComboBox.QFrame_0.QListView_0.qt_scrollarea_viewport', event , 67.612992 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(235, 21), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(500, 259), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.storageComboBox.QFrame_0.QListView_0.qt_scrollarea_viewport', event , 67.697469 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(235, 21), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(500, 259), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.storageComboBox.QFrame_0.QListView_0.qt_scrollarea_viewport', event , 67.808873 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(51, 14), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(870, 600), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.okButton', event , 70.073942 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(51, 14), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(870, 600), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.okButton', event , 70.197808 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(630, 552), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(723, 574), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1', event , 70.474271 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(630, 552), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(723, 574), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1', event , 70.574076 )

    ########################
    player.display_comment("""Edit raw data properties: absolute link""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(56, 8), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(374, 42), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_tabbar', event , 71.287662 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(56, 8), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(374, 42), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_tabbar', event , 71.455634 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(60, 3), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(400, 62), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.QHeaderView_1.qt_scrollarea_viewport', event , 71.803412 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(84, 18), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(424, 77), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.QHeaderView_1.qt_scrollarea_viewport', event , 71.896362 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(86, 19), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(426, 78), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.QHeaderView_1.qt_scrollarea_viewport', event , 71.991791 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(90, 6), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(430, 88), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport', event , 72.091328 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(11, 7), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(429, 94), (Qt.RightButton), (Qt.RightButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.ButtonOverlay_0', event , 72.254513 )

    event = PyQt4.QtGui.QContextMenuEvent(0, PyQt4.QtCore.QPoint(11, 7), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(429, 94), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.ButtonOverlay_0', event , 72.346071 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(11, 7), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(429, 94), (Qt.RightButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.ButtonOverlay_0', event , 72.439668 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(101, 14), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(441, 96), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport', event , 72.572668 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(130, 21), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(470, 103), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport', event , 72.6723 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(151, 17), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(491, 99), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport', event , 72.774569 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(152, 17), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(492, 99), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport', event , 72.875763 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(154, 15), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(494, 97), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport', event , 72.970844 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(154, 15), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(494, 97), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport', event , 73.061714 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(154, 15), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(494, 97), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport', event , 73.148092 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(153, 15), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(493, 97), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport', event , 73.476518 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(145, 14), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(485, 96), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport', event , 73.568205 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(144, 14), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(484, 96), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport', event , 73.665596 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(144, 14), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(484, 96), (Qt.RightButton), (Qt.RightButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport', event , 73.756109 )

    event = PyQt4.QtGui.QContextMenuEvent(0, PyQt4.QtCore.QPoint(144, 14), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(484, 96), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport', event , 73.838359 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(484, 96), (Qt.RightButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.QMenu_0', event , 73.950856 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(484, 96), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.QMenu_0', event , 74.044347 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(2, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(486, 96), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.QMenu_0', event , 74.145032 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(20, 4), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(504, 100), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.QMenu_0', event , 74.243079 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(23, 9), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(507, 105), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.QMenu_0', event , 74.337979 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(23, 10), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(507, 106), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.QMenu_0', event , 74.432082 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(23, 10), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(507, 106), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.QMenu_0', event , 74.526292 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(23, 11), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(507, 107), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.QMenu_0', event , 74.615529 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(23, 11), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(507, 107), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.QMenu_0', event , 74.708671 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(22, 3), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(495, 137), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.rangeMaxSpinBox.qt_spinbox_lineedit', event , 75.772832 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(222, 8), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(485, 224), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.storageComboBox', event , 76.563147 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(222, -12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(485, 224), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.storageComboBox.QFrame_0', event , 76.685792 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(209, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(474, 238), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.storageComboBox.QFrame_0.QListView_0.qt_scrollarea_viewport', event , 77.206977 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(207, 2), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(472, 240), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.storageComboBox.QFrame_0.QListView_0.qt_scrollarea_viewport', event , 77.304897 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(206, 4), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(471, 242), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.storageComboBox.QFrame_0.QListView_0.qt_scrollarea_viewport', event , 77.403373 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(205, 4), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(470, 242), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.storageComboBox.QFrame_0.QListView_0.qt_scrollarea_viewport', event , 77.594577 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(193, 25), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(458, 263), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.storageComboBox.QFrame_0.QListView_0.qt_scrollarea_viewport', event , 77.686401 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(192, 27), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(457, 265), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.storageComboBox.QFrame_0.QListView_0.qt_scrollarea_viewport', event , 77.785976 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(192, 26), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(457, 264), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.storageComboBox.QFrame_0.QListView_0.qt_scrollarea_viewport', event , 77.906835 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(192, 24), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(457, 262), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.storageComboBox.QFrame_0.QListView_0.qt_scrollarea_viewport', event , 78.003639 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(192, 24), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(457, 262), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.storageComboBox.QFrame_0.QListView_0.qt_scrollarea_viewport', event , 79.088915 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(192, 24), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(457, 262), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.storageComboBox.QFrame_0.QListView_0.qt_scrollarea_viewport', event , 79.200543 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(24, 16), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(843, 602), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.okButton', event , 81.733848 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(24, 16), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(843, 602), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.okButton', event , 81.873105 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(481, 457), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(799, 583), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0', event , 82.199401 )

    ########################
    player.display_comment("""Show summary tab""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(508, 2), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(508, 22), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout', event , 82.903614 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(508, 2), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(508, 22), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout', event , 83.052345 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(196, 5), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(514, 39), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_tabbar', event , 83.468684 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(196, 5), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(514, 39), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_tabbar', event , 83.568739 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(108, 11), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(448, 70), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.fileInfoTabWidgetPage1.laneSummaryTableView.QHeaderView_1.qt_scrollarea_viewport', event , 84.167569 )

    ########################
    player.display_comment("""Remove all.""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(481, 4), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(481, 4), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 84.928871 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(133, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(473, 59), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.fileInfoTabWidgetPage1.laneSummaryTableView.QHeaderView_1.qt_scrollarea_viewport', event , 85.030511 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(129, 18), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(469, 77), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.fileInfoTabWidgetPage1.laneSummaryTableView.QHeaderView_1.qt_scrollarea_viewport', event , 85.133198 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(116, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(456, 94), (Qt.RightButton), (Qt.RightButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.fileInfoTabWidgetPage1.laneSummaryTableView.qt_scrollarea_viewport', event , 85.506989 )

    event = PyQt4.QtGui.QContextMenuEvent(0, PyQt4.QtCore.QPoint(116, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(456, 94), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.fileInfoTabWidgetPage1.laneSummaryTableView.qt_scrollarea_viewport', event , 85.60369 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(456, 94), (Qt.RightButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.fileInfoTabWidgetPage1.laneSummaryTableView.QMenu_0', event , 85.714334 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(456, 94), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.fileInfoTabWidgetPage1.laneSummaryTableView.QMenu_0', event , 85.816521 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(1, 1), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(457, 95), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.fileInfoTabWidgetPage1.laneSummaryTableView.QMenu_0', event , 86.075608 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(15, 5), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(471, 99), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.fileInfoTabWidgetPage1.laneSummaryTableView.QMenu_0', event , 86.165917 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(17, 8), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(473, 102), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.fileInfoTabWidgetPage1.laneSummaryTableView.QMenu_0', event , 86.267161 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(18, 13), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(474, 107), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.fileInfoTabWidgetPage1.laneSummaryTableView.QMenu_0', event , 86.362702 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(18, 13), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(474, 107), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.fileInfoTabWidgetPage1.laneSummaryTableView.QMenu_0', event , 86.464237 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(18, 13), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(474, 107), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.fileInfoTabWidgetPage1.laneSummaryTableView.QMenu_0', event , 86.551167 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(35, 17), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(35, 17), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 88.839794 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(30, 8), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(30, 8), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 88.930536 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(29, 8), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(29, 8), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 89.016887 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(20, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(20, 0), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 89.107391 )

    player.display_comment("SCRIPT COMPLETE")
