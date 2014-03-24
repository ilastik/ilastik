
# Event Recording
# Created by Stuart
# Started at: 2014-02-18 19:37:42.227052

def playback_events(player):
    import PyQt4.QtCore
    from PyQt4.QtCore import Qt, QEvent, QPoint
    import PyQt4.QtGui
    
    # The getMainWindow() function is provided by EventRecorderApp
    mainwin = PyQt4.QtGui.QApplication.instance().getMainWindow()

    player.display_comment("SCRIPT STARTING")


    ########################
    player.display_comment("""In this recording, we\'ll create a new carving project and run preprocessing (but nothing more).""")
    ########################

    ########################
    player.display_comment("""New Project (Carving)""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(535, 2), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(535, 2), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 1.925241 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(82, 15), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(393, 151), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.startupPage.frame.CreateList.qt_scrollarea_viewport.scrollAreaWidgetContents.NewProjectButton_CarvingWorkflow', event , 2.900445 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(82, 15), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(393, 151), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.startupPage.frame.CreateList.qt_scrollarea_viewport.scrollAreaWidgetContents.NewProjectButton_CarvingWorkflow', event , 2.947955 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(13, 7), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(741, 519), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.QFileDialog.buttonBox.QPushButton_0', event , 5.849772 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(13, 7), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(741, 519), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QFileDialog.buttonBox.QPushButton_0', event , 5.929996 )

    ########################
    player.display_comment("""Select input file (real data)""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(447, 6), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(447, 6), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 7.847024 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(81, 1), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(403, 60), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QHeaderView_1.qt_scrollarea_viewport', event , 7.954721 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(71, 14), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(393, 73), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QHeaderView_1.qt_scrollarea_viewport', event , 8.011081 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(65, 20), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(387, 79), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QHeaderView_1.qt_scrollarea_viewport', event , 8.066579 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(51, 11), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(373, 95), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.QWidget_0.AddFileButton_0', event , 8.266655 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(51, -15), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(373, 95), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 8.338111 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(53, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(375, 110), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 8.548558 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(55, 8), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(377, 118), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 8.599118 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(55, 10), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(377, 120), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 8.651417 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(55, 10), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(377, 120), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 8.821745 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(55, 10), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(377, 120), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 8.883853 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2f, Qt.NoModifier, """/""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 9.958288 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2f, Qt.NoModifier, """/""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 10.014726 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x48, Qt.NoModifier, """h""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 10.215437 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x48, Qt.NoModifier, """h""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 10.282691 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4f, Qt.NoModifier, """o""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 10.372253 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4d, Qt.NoModifier, """m""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 10.441473 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4f, Qt.NoModifier, """o""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 10.497776 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 10.555471 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4d, Qt.NoModifier, """m""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 10.61244 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 10.669513 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2f, Qt.NoModifier, """/""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 10.727226 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2f, Qt.NoModifier, """/""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 10.784815 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x56, Qt.NoModifier, """v""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 10.841002 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x56, Qt.NoModifier, """v""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 10.899667 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 10.95596 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 11.013461 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x47, Qt.NoModifier, """g""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 11.072082 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x47, Qt.NoModifier, """g""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 11.130413 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x52, Qt.NoModifier, """r""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 11.221915 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x52, Qt.NoModifier, """r""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 11.299555 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 11.356109 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 11.426047 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 11.481994 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 11.533323 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 11.595767 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 11.652564 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2f, Qt.NoModifier, """/""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 11.709147 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2f, Qt.NoModifier, """/""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 11.766302 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x52, Qt.NoModifier, """r""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 12.126169 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 12.200057 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x52, Qt.NoModifier, """r""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 12.251967 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 12.305004 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 12.358485 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 12.413319 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4c, Qt.NoModifier, """l""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 12.466954 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4c, Qt.NoModifier, """l""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 12.522021 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 12.576443 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 12.631373 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2b, (Qt.ShiftModifier), """+""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 12.686284 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 12.741404 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2b, (Qt.ShiftModifier), """+""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 12.796129 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 12.850215 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000003, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 13.346396 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000003, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 13.399765 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 13.910055 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 13.959729 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 14.003863 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 14.058365 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x53, Qt.NoModifier, """s""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 14.106783 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 14.156919 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x53, Qt.NoModifier, """s""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 14.208718 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 14.261251 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 14.31393 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 14.368109 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 14.422869 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2d, Qt.NoModifier, """-""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 14.476726 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x44, Qt.NoModifier, """d""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 14.531665 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x44, Qt.NoModifier, """d""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 14.586714 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 14.641215 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 14.696265 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 14.751823 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 14.806879 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 14.863284 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 14.918149 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000004, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 15.23684 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000004, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 15.294465 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x44, Qt.NoModifier, """d""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 17.937906 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 17.992144 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x44, Qt.NoModifier, """d""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 18.047273 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 18.094415 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 18.143807 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4b, Qt.NoModifier, """k""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 18.211498 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 18.259227 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4b, Qt.NoModifier, """k""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 18.308798 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 18.854387 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 18.961085 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 19.016784 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2d, Qt.NoModifier, """-""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 19.065632 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x52, Qt.NoModifier, """r""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 19.249993 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 19.330167 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x52, Qt.NoModifier, """r""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 19.378317 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x57, Qt.NoModifier, """w""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 19.427462 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 19.476647 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x57, Qt.NoModifier, """w""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 19.524024 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2e, Qt.NoModifier, """.""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 19.574719 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2e, Qt.NoModifier, """.""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 19.623421 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x48, Qt.NoModifier, """h""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 20.411897 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x35, Qt.NoModifier, """5""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 20.460844 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x48, Qt.NoModifier, """h""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 20.51008 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x35, Qt.NoModifier, """5""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 20.559431 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000004, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 20.609191 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000004, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog', event , 20.692505 )

    ########################
    player.display_comment("""Open Preprocessing Applet""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(156, 5), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(162, 393), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QAbstractButton_1', event , 22.604913 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(156, 5), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(162, 393), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QAbstractButton_1', event , 22.604913 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(23, 5), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(268, 482), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.PreprocessDrawer.sigmaSpin.qt_spinbox_lineedit', event , 23.809994 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(20, 6), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(265, 483), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.PreprocessDrawer.sigmaSpin.qt_spinbox_lineedit', event , 23.914699 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(19, 6), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(264, 483), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.PreprocessDrawer.sigmaSpin.qt_spinbox_lineedit', event , 24.190625 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(56, 6), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(205, 429), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.PreprocessDrawer.filter4', event , 24.306025 )

    ########################
    player.display_comment("""Select parameters (\"dark lines\", sigma=2.0)""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(340, 4), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(474, 89), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 25.052522 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(193, 17), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(342, 224), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.PreprocessDrawer.label_2', event , 25.194826 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(131, 90), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(280, 297), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.PreprocessDrawer.label_2', event , 25.283625 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(28, 19), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(177, 390), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.PreprocessDrawer.filter2', event , 25.376713 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(3, 5), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(152, 376), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.PreprocessDrawer.filter2', event , 25.706167 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(8, 8), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(157, 379), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.PreprocessDrawer.filter2', event , 25.808691 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(16, 9), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(165, 380), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.PreprocessDrawer.filter2', event , 25.917216 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(11, 8), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(160, 379), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.PreprocessDrawer.filter2', event , 26.013497 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(1, 8), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(150, 379), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.PreprocessDrawer.filter2', event , 26.120977 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(2, 9), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(151, 380), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.PreprocessDrawer.filter2', event , 26.309632 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(7, 9), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(156, 380), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.PreprocessDrawer.filter2', event , 26.397294 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(7, 9), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(156, 380), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.PreprocessDrawer.filter2', event , 26.479231 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(7, 9), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(156, 380), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.PreprocessDrawer.filter2', event , 26.598318 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(8, 9), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(157, 380), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.PreprocessDrawer.filter2', event , 26.961966 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(61, 11), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(210, 434), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.PreprocessDrawer.filter4', event , 27.064633 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(105, 17), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(254, 466), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.PreprocessDrawer.filter5', event , 27.15913 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(21, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(266, 477), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.PreprocessDrawer.sigmaSpin.qt_spinbox_lineedit', event , 27.402782 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(19, 4), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(264, 481), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.PreprocessDrawer.sigmaSpin.qt_spinbox_lineedit', event , 27.498316 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(19, 6), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(264, 483), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.PreprocessDrawer.sigmaSpin.qt_spinbox_lineedit', event , 27.595925 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(18, 8), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(263, 485), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.PreprocessDrawer.sigmaSpin.qt_spinbox_lineedit', event , 27.689888 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(18, 9), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(263, 486), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.PreprocessDrawer.sigmaSpin.qt_spinbox_lineedit', event , 27.788365 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(19, 9), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(264, 486), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.PreprocessDrawer.sigmaSpin.qt_spinbox_lineedit', event , 27.881766 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(20, 9), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(265, 486), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.PreprocessDrawer.sigmaSpin.qt_spinbox_lineedit', event , 28.088315 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(20, 9), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(265, 486), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.PreprocessDrawer.sigmaSpin.qt_spinbox_lineedit', event , 28.649388 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(20, 9), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(265, 486), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.PreprocessDrawer.sigmaSpin.qt_spinbox_lineedit', event , 28.727799 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonDblClick, PyQt4.QtCore.QPoint(20, 9), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(265, 486), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.PreprocessDrawer.sigmaSpin.qt_spinbox_lineedit', event , 28.815596 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(20, 9), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(265, 486), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.PreprocessDrawer.sigmaSpin.qt_spinbox_lineedit', event , 28.894035 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(20, 9), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(265, 486), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.PreprocessDrawer.sigmaSpin.qt_spinbox_lineedit', event , 28.98039 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(20, 9), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(265, 486), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.PreprocessDrawer.sigmaSpin.qt_spinbox_lineedit', event , 29.073453 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x32, Qt.NoModifier, """2""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.PreprocessDrawer.sigmaSpin', event , 31.112218 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x32, Qt.NoModifier, """2""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.PreprocessDrawer.sigmaSpin', event , 31.198699 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2e, Qt.NoModifier, """.""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.PreprocessDrawer.sigmaSpin', event , 31.275648 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2e, Qt.NoModifier, """.""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.PreprocessDrawer.sigmaSpin', event , 31.344829 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x30, Qt.NoModifier, """0""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.PreprocessDrawer.sigmaSpin', event , 31.423784 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x30, Qt.NoModifier, """0""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.PreprocessDrawer.sigmaSpin', event , 31.512188 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(18, 6), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(263, 483), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.PreprocessDrawer.sigmaSpin.qt_spinbox_lineedit', event , 33.07389 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(5, 13), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(154, 358), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.PreprocessDrawer.filter1', event , 33.157056 )

    ########################
    player.display_comment("""Hit \"Run\"""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(21, 50), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(466, 162), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 34.048625 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(7, 274), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(429, 472), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_vcontainer.QScrollBar_0', event , 36.796245 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(7, 274), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(429, 472), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_vcontainer.QScrollBar_0', event , 36.878088 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(107, 20), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(256, 439), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.PreprocessDrawer.runButton', event , 37.927246 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(107, 20), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(256, 439), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.PreprocessDrawer.runButton', event , 38.021307 )

    ########################
    player.display_comment(""".... waiting a bit here to make sure we aren\'t too sensitive to timing...""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(137, 295), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(582, 407), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 428.384786 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(51, 272), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(496, 384), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 428.47437 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(67, 18), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(216, 306), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.PreprocessDrawer.filter2', event , 428.557144 )

    ########################
    player.display_comment("""View the filtered data""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(370, 4), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(504, 89), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 429.636441 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(196, 14), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(345, 302), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.PreprocessDrawer.filter2', event , 429.709873 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(10, 15), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(156, 591), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_2_lane_0.layerWidget.qt_scrollarea_viewport.LayerItemWidget_Filtered Data.ToggleEye_0', event , 430.478042 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(10, 15), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(156, 591), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_2_lane_0.layerWidget.qt_scrollarea_viewport.LayerItemWidget_Filtered Data.ToggleEye_0', event , 430.678375 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(22, 2), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(267, 396), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.PreprocessDrawer.sigmaSpin.qt_spinbox_lineedit', event , 434.979167 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(56, 15), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(205, 355), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.PreprocessDrawer.filter4', event , 435.065639 )

    ########################
    player.display_comment("""View the watershed.""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(357, 10), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(491, 95), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 435.909645 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(236, 127), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(385, 251), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.PreprocessDrawer.label_2', event , 435.984338 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(11, 14), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(157, 548), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_2_lane_0.layerWidget.qt_scrollarea_viewport.LayerItemWidget_Watershed.ToggleEye_0', event , 436.885586 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(11, 14), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(157, 548), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_2_lane_0.layerWidget.qt_scrollarea_viewport.LayerItemWidget_Watershed.ToggleEye_0', event , 437.038327 )

    ########################
    player.display_comment("""Save the project.""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(302, 2), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(436, 87), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 444.322004 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(180, 17), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(314, 102), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 444.417005 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(66, 19), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(200, 104), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 444.683135 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(38, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(172, 97), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 444.76861 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(31, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(165, 97), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 444.870278 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(29, 11), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(163, 96), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 444.954706 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(29, 11), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(163, 96), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 445.033086 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(29, -8), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(163, 96), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.project_menu', event , 445.141896 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(30, -7), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(164, 97), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.project_menu', event , 446.029279 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(30, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(175, 121), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 446.098986 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(32, -3), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(166, 101), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.project_menu', event , 446.184904 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(32, 16), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(181, 138), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 446.258496 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(34, 3), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(168, 107), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.project_menu', event , 446.331042 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(47, 38), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(181, 142), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.project_menu', event , 446.419381 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(47, 38), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(181, 142), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.project_menu', event , 446.542439 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(47, 38), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(181, 142), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.project_menu', event , 446.649785 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(0, 92), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(149, 216), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.PreprocessDrawer.label_2', event , 453.415626 )

    ########################
    player.display_comment("""We\'re done.""")
    ########################

    player.display_comment("SCRIPT COMPLETE")
