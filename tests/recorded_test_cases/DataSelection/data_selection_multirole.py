###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
#		   http://ilastik.org/license.html
###############################################################################

# Event Recording
# Created by Stuart
# Started at: 2014-02-08 22:49:58.303250

def playback_events(player):
    import PyQt4.QtCore
    from PyQt4.QtCore import Qt, QEvent, QPoint
    import PyQt4.QtGui
    
    # The getMainWindow() function is provided by EventRecorderApp
    mainwin = PyQt4.QtGui.QApplication.instance().getMainWindow()

    player.display_comment("SCRIPT STARTING")


    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(701, 5), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(701, 5), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 1.692748 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(23, 15), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(23, 15), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 3.110433 )

    ########################
    player.display_comment("""New Project (Layer Viewer)""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(389, 4), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(389, 4), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 4.21428 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(101, 5), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(412, 309), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.startupPage.frame.CreateList.qt_scrollarea_viewport.scrollAreaWidgetContents.NewProjectButton_LayerViewerWorkflow', event , 6.826384 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(101, 5), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(412, 309), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.startupPage.frame.CreateList.qt_scrollarea_viewport.scrollAreaWidgetContents.NewProjectButton_LayerViewerWorkflow', event , 6.895344 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000004, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.QFileDialog.fileNameEdit', event , 8.220628 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000004, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.QFileDialog', event , 8.292645 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(67, 75), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(387, 132), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1', event , 9.293688 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(65, 30), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(387, 112), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport', event , 9.350567 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(64, 19), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(386, 103), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport.QWidget_0.AddFileButton_0', event , 9.6551 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(63, -8), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(385, 102), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 9.711432 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(63, -8), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(385, 102), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 9.764054 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(-344, 10), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(-22, 120), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 10.964833 )

    ########################
    player.display_comment("""Add raw data""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(395, 13), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(395, 13), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 11.602674 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(78, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(400, 59), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.QHeaderView_1.qt_scrollarea_viewport', event , 11.726516 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(73, 9), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(395, 68), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.QHeaderView_1.qt_scrollarea_viewport', event , 11.783653 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(68, 19), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(390, 78), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.QHeaderView_1.qt_scrollarea_viewport', event , 11.840977 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(60, 11), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(382, 95), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport.QWidget_0.AddFileButton_0', event , 12.913177 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(60, -15), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(382, 95), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 13.009026 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(56, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(378, 110), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 13.769713 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(54, 5), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(376, 115), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 13.821583 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(53, 8), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(375, 118), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 13.875465 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(52, 9), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(374, 119), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 13.929114 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(51, 15), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(373, 125), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 13.982159 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(51, 16), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(373, 126), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 14.034776 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(51, 16), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(373, 126), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 14.201508 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(51, 16), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(373, 126), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 14.293815 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2f, Qt.NoModifier, """/""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 16.477944 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2f, Qt.NoModifier, """/""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 16.533314 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x48, Qt.NoModifier, """h""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 16.604682 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x48, Qt.NoModifier, """h""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 16.667064 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4f, Qt.NoModifier, """o""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 16.743696 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4d, Qt.NoModifier, """m""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 16.835824 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4f, Qt.NoModifier, """o""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 16.885974 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 16.934867 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4d, Qt.NoModifier, """m""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 16.983078 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 17.031009 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2f, Qt.NoModifier, """/""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 17.080313 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2f, Qt.NoModifier, """/""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 17.129712 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x56, Qt.NoModifier, """v""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 17.7556 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x56, Qt.NoModifier, """v""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 17.84837 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 17.896087 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 17.978572 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x47, Qt.NoModifier, """g""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 18.026004 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x47, Qt.NoModifier, """g""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 18.074551 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x52, Qt.NoModifier, """r""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 18.123131 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x52, Qt.NoModifier, """r""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 18.202491 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 18.246837 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 18.299537 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 18.347712 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 18.396896 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 18.445755 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 18.492913 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2f, Qt.NoModifier, """/""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 18.542914 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2f, Qt.NoModifier, """/""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 18.592629 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x46, Qt.NoModifier, """f""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 19.736315 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x46, Qt.NoModifier, """f""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 19.818586 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 19.870125 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4b, Qt.NoModifier, """k""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 19.919155 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 19.968263 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4b, Qt.NoModifier, """k""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 20.017545 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 20.065488 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 20.11533 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 20.793298 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 20.867162 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 20.947902 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 20.994946 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 21.10686 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 21.165722 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 21.219874 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 21.267111 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x53, Qt.NoModifier, """s""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 21.355445 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 21.420022 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x53, Qt.NoModifier, """s""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 21.469015 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 21.518274 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 21.746434 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 21.970916 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 22.054255 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 22.107905 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x44, Qt.NoModifier, """d""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 22.218659 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x44, Qt.NoModifier, """d""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 22.321212 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 22.369628 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 22.418761 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 22.466728 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 22.549177 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 22.598795 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 22.648859 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000004, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 23.18714 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000004, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 23.23732 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x43, Qt.NoModifier, """c""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 24.601873 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x55, Qt.NoModifier, """u""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 24.691872 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x43, Qt.NoModifier, """c""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 24.74098 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x42, Qt.NoModifier, """b""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 24.790361 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x55, Qt.NoModifier, """u""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 24.840631 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x42, Qt.NoModifier, """b""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 24.890133 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 24.938311 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 24.986774 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 25.083874 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 25.13937 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 25.195518 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 25.264882 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4f, Qt.NoModifier, """o""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 25.667706 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4f, Qt.NoModifier, """o""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 25.738618 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x42, Qt.NoModifier, """b""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 25.93922 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x42, Qt.NoModifier, """b""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 25.995771 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4a, Qt.NoModifier, """j""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 26.100432 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 26.179853 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4a, Qt.NoModifier, """j""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 26.228298 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x43, Qt.NoModifier, """c""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 26.277768 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 26.327447 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x43, Qt.NoModifier, """c""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 26.374948 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 26.468339 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 26.570533 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x53, Qt.NoModifier, """s""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 26.628928 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x53, Qt.NoModifier, """s""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 26.678919 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 26.81949 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 26.947435 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 27.012139 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2d, Qt.NoModifier, """-""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 27.060502 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x52, Qt.NoModifier, """r""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 27.195437 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 27.292491 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x52, Qt.NoModifier, """r""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 27.341843 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x57, Qt.NoModifier, """w""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 27.390128 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 27.439859 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x57, Qt.NoModifier, """w""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 27.506009 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2e, Qt.NoModifier, """.""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 27.554317 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2e, Qt.NoModifier, """.""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 27.604425 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 27.699406 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 27.75591 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x50, Qt.NoModifier, """p""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 27.819332 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x50, Qt.NoModifier, """p""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 27.939913 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x59, Qt.NoModifier, """y""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 27.989165 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x59, Qt.NoModifier, """y""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 28.0424 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000004, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 28.101698 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(51, 44), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(373, 126), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport', event , 28.497923 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000004, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport.QWidget_0.AddFileButton_0', event , 28.571533 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(16, 44), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(338, 126), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.QHeaderView_0.qt_scrollarea_viewport', event , 29.898559 )

    ########################
    player.display_comment("""Add binary data (start with the wrong file)""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(403, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(403, 0), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 31.12451 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(423, 16), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(423, 16), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 31.195263 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(137, 10), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(455, 44), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_tabbar', event , 31.899052 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(137, 10), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(455, 44), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_tabbar', event , 31.99399 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(126, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(446, 57), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0', event , 32.788394 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(95, 8), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(435, 67), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QHeaderView_1.qt_scrollarea_viewport', event , 32.861244 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(84, 21), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(424, 80), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QHeaderView_1.qt_scrollarea_viewport', event , 32.936152 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(75, 14), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(415, 96), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.AddFileButton_0', event , 33.239864 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(75, -16), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(415, 96), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.AddFileButton_0.QMenu_0', event , 33.316147 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(73, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(413, 112), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.AddFileButton_0.QMenu_0', event , 34.187112 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(71, 4), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(411, 116), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.AddFileButton_0.QMenu_0', event , 34.254712 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(70, 7), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(410, 119), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.AddFileButton_0.QMenu_0', event , 34.325242 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(69, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(409, 124), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.AddFileButton_0.QMenu_0', event , 34.394166 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(66, 17), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(406, 129), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.AddFileButton_0.QMenu_0', event , 34.463172 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(66, 17), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(406, 129), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.AddFileButton_0.QMenu_0', event , 34.6126 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(66, 17), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(406, 129), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.AddFileButton_0.QMenu_0', event , 34.680147 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x43, Qt.NoModifier, """c""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 36.783969 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x55, Qt.NoModifier, """u""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 36.854153 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x43, Qt.NoModifier, """c""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 36.918666 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x55, Qt.NoModifier, """u""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 36.978408 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x42, Qt.NoModifier, """b""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 37.03739 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x42, Qt.NoModifier, """b""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 37.097598 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 37.156954 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 37.218979 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 37.391167 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 37.591405 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 37.670504 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 37.790889 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4f, Qt.NoModifier, """o""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 37.98259 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4f, Qt.NoModifier, """o""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 38.061334 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x42, Qt.NoModifier, """b""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 38.166483 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x42, Qt.NoModifier, """b""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 38.230601 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4a, Qt.NoModifier, """j""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 38.328889 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 38.400315 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4a, Qt.NoModifier, """j""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 38.460788 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x43, Qt.NoModifier, """c""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 38.522015 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 38.583748 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x43, Qt.NoModifier, """c""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 38.643344 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 38.702207 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x53, Qt.NoModifier, """s""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 38.765661 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 38.825439 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x53, Qt.NoModifier, """s""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 38.885426 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 39.558749 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 39.630154 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 39.73472 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 39.793588 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x52, Qt.NoModifier, """r""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 39.910203 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 39.990655 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x52, Qt.NoModifier, """r""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 40.049977 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x57, Qt.NoModifier, """w""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 40.107897 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 40.172588 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2e, Qt.NoModifier, """.""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 40.230944 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x57, Qt.NoModifier, """w""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 40.289394 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2e, Qt.NoModifier, """.""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 40.357719 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 40.416731 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 40.476127 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x50, Qt.NoModifier, """p""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 40.582297 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x50, Qt.NoModifier, """p""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 40.670756 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x59, Qt.NoModifier, """y""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 40.766538 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x59, Qt.NoModifier, """y""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 40.839326 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000004, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 40.934886 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000004, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 41.02278 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(14, 27), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(336, 109), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QHeaderView_0.qt_scrollarea_viewport', event , 42.443043 )

    ########################
    player.display_comment("""Now replace the incorrect file""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(400, 1), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(400, 1), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 43.815329 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(178, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(498, 57), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0', event , 43.997985 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(162, 8), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(502, 67), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QHeaderView_1.qt_scrollarea_viewport', event , 44.076799 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(161, 10), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(501, 69), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QHeaderView_1.qt_scrollarea_viewport', event , 44.163535 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(157, 14), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(497, 73), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QHeaderView_1.qt_scrollarea_viewport', event , 44.249089 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(153, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(493, 82), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport', event , 44.329792 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(151, 7), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(491, 89), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport', event , 44.41951 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(151, 14), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(491, 96), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport', event , 44.50748 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(151, 17), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(491, 99), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport', event , 44.587771 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(151, 17), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(491, 99), (Qt.RightButton), (Qt.RightButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport', event , 44.669591 )

    event = PyQt4.QtGui.QContextMenuEvent(0, PyQt4.QtCore.QPoint(151, 17), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(491, 99), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport', event , 44.749187 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(491, 99), (Qt.RightButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_0', event , 44.834172 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(491, 99), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_0', event , 44.916374 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(0, 2), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(491, 101), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_0', event , 45.61943 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(10, 19), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(501, 118), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_0', event , 45.695415 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(16, 30), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(507, 129), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_0', event , 45.776998 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(19, 34), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(510, 133), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_0', event , 45.859086 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(19, 36), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(510, 135), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_0', event , 45.936687 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(19, 36), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(510, 135), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_0', event , 46.314415 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(19, 36), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(510, 135), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_0', event , 46.390822 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x43, Qt.NoModifier, """c""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 47.831649 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x55, Qt.NoModifier, """u""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 47.929857 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x43, Qt.NoModifier, """c""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 47.997979 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x55, Qt.NoModifier, """u""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 48.063008 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x42, Qt.NoModifier, """b""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 48.135179 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x42, Qt.NoModifier, """b""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 48.201312 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 48.268069 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 48.34207 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 48.632673 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 48.696109 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 48.770586 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 48.83531 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4f, Qt.NoModifier, """o""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 48.898893 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4f, Qt.NoModifier, """o""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 48.973234 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x42, Qt.NoModifier, """b""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 49.040939 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x42, Qt.NoModifier, """b""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 49.106441 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4a, Qt.NoModifier, """j""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 49.193087 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 49.28021 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4a, Qt.NoModifier, """j""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 49.345281 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x43, Qt.NoModifier, """c""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 49.418202 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 49.485837 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x43, Qt.NoModifier, """c""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 49.551111 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 49.623905 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x53, Qt.NoModifier, """s""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 49.688356 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 49.753977 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x53, Qt.NoModifier, """s""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 49.828336 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 49.892796 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 49.958828 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 50.03474 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 50.101479 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x42, Qt.NoModifier, """b""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 50.256922 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x42, Qt.NoModifier, """b""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 50.343562 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x49, Qt.NoModifier, """i""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 50.408007 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 50.48013 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x49, Qt.NoModifier, """i""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 50.544493 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 50.612158 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 50.682932 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x52, Qt.NoModifier, """r""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 50.748245 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 50.813475 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x59, Qt.NoModifier, """y""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 50.885408 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x52, Qt.NoModifier, """r""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 50.952223 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x59, Qt.NoModifier, """y""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 51.01774 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2e, Qt.NoModifier, """.""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 51.091338 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2e, Qt.NoModifier, """.""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 51.15683 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 51.219877 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 51.296314 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x50, Qt.NoModifier, """p""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 51.361973 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x50, Qt.NoModifier, """p""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 51.427278 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x59, Qt.NoModifier, """y""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 51.500049 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x59, Qt.NoModifier, """y""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 51.567704 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000004, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 51.63259 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000004, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 51.752149 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(86, 74), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(406, 131), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0', event , 53.734886 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(10, 29), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(350, 111), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport', event , 53.842889 )

    ########################
    player.display_comment("""Edit binary data properties: axis order""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(510, 3), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(510, 3), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 55.142156 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(169, 1), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(509, 83), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport', event , 55.217537 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(166, 25), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(506, 107), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport', event , 55.49796 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(164, 11), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(504, 93), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport', event , 55.589242 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(164, 11), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(504, 93), (Qt.RightButton), (Qt.RightButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport', event , 55.8521 )

    event = PyQt4.QtGui.QContextMenuEvent(0, PyQt4.QtCore.QPoint(164, 11), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(504, 93), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport', event , 55.928786 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(504, 93), (Qt.RightButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_1', event , 56.021315 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(504, 93), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_1', event , 56.099078 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(2, -1), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(506, 92), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_1', event , 56.669477 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(2, -1), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(506, 92), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_1', event , 56.748299 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(21, -1), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(525, 92), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_1', event , 56.836718 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(23, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(527, 93), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_1', event , 56.914366 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(24, 7), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(528, 100), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_1', event , 56.988523 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(24, 8), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(528, 101), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_1', event , 57.081045 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(23, 8), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(527, 101), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_1', event , 57.156277 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(23, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(527, 105), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_1', event , 57.233086 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(22, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(526, 105), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_1', event , 57.318463 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(22, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(526, 105), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_1', event , 57.391933 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(22, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(526, 105), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_1', event , 57.464641 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(31, 11), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(504, 197), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.rangeMaxSpinBox.qt_spinbox_lineedit', event , 58.637608 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(127, 15), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(392, 201), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.rangeMinSpinBox.qt_spinbox_lineedit', event , 59.523693 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(122, 11), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(387, 197), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.rangeMinSpinBox.qt_spinbox_lineedit', event , 59.61238 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(121, 11), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(386, 197), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.rangeMinSpinBox.qt_spinbox_lineedit', event , 59.712159 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(71, 20), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(334, 174), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.axesEdit', event , 59.859373 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(65, 17), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(328, 171), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.axesEdit', event , 59.938367 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(57, 15), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(320, 169), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.axesEdit', event , 60.028047 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(57, 15), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(320, 169), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.axesEdit', event , 60.102414 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(57, 15), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(320, 169), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.axesEdit', event , 60.188999 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonDblClick, PyQt4.QtCore.QPoint(57, 15), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(320, 169), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.axesEdit', event , 60.273731 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(57, 15), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(320, 169), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.axesEdit', event , 60.348377 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5a, Qt.NoModifier, """z""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.axesEdit', event , 61.721115 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x5a, Qt.NoModifier, """z""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.axesEdit', event , 61.813522 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x59, Qt.NoModifier, """y""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.axesEdit', event , 62.635343 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x58, Qt.NoModifier, """x""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.axesEdit', event , 62.722763 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x59, Qt.NoModifier, """y""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.axesEdit', event , 62.795447 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x58, Qt.NoModifier, """x""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.axesEdit', event , 62.941147 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000004, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.axesEdit', event , 63.236037 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000004, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.axesEdit', event , 63.317482 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(57, 16), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(320, 170), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.axesEdit', event , 67.278968 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(57, 17), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(320, 171), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.axesEdit', event , 67.390641 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(57, 18), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(320, 172), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.axesEdit', event , 67.480231 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(55, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(320, 186), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.rangeMinSpinBox.qt_spinbox_lineedit', event , 67.56042 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(56, 1), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(321, 187), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.rangeMinSpinBox.qt_spinbox_lineedit', event , 67.63918 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(14, 13), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(833, 651), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.okButton', event , 69.336289 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(14, 13), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(833, 651), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.okButton', event , 69.437057 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(513, 510), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(833, 651), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 69.744076 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(510, 511), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(830, 652), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 70.683599 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(437, 482), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(757, 623), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 70.768024 )

    ########################
    player.display_comment("""Edit properties again: Absolute link""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(410, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(410, 0), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 71.751088 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(224, 21), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(564, 80), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QHeaderView_1.qt_scrollarea_viewport', event , 71.828598 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(184, 28), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(524, 110), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport', event , 72.302749 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(182, 21), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(522, 103), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport', event , 72.3966 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(182, 19), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(522, 101), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport', event , 72.47959 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(182, 19), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(522, 101), (Qt.RightButton), (Qt.RightButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport', event , 72.808837 )

    event = PyQt4.QtGui.QContextMenuEvent(0, PyQt4.QtCore.QPoint(182, 19), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(522, 101), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport', event , 72.882409 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(522, 101), (Qt.RightButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_2', event , 72.964764 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(522, 101), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_2', event , 73.056188 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(7, 2), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(529, 103), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_2', event , 73.135333 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(22, 10), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(544, 111), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_2', event , 73.211038 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(23, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(545, 113), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_2', event , 73.298096 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(26, 16), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(548, 117), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_2', event , 73.375967 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(26, 17), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(548, 118), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_2', event , 73.451858 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(26, 17), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(548, 118), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_2', event , 73.614629 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(26, 17), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(548, 118), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QMenu_2', event , 73.688291 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(277, 13), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(540, 281), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.storageComboBox', event , 76.287741 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(277, -7), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(540, 281), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.storageComboBox.QFrame_0', event , 76.407452 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(273, 1), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(538, 291), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.storageComboBox.QFrame_0.QListView_0.qt_scrollarea_viewport', event , 76.891372 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(269, 11), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(534, 301), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.storageComboBox.QFrame_0.QListView_0.qt_scrollarea_viewport', event , 76.971426 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(266, 19), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(531, 309), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.storageComboBox.QFrame_0.QListView_0.qt_scrollarea_viewport', event , 77.051993 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(264, 22), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(529, 312), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.storageComboBox.QFrame_0.QListView_0.qt_scrollarea_viewport', event , 77.140145 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(263, 22), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(528, 312), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.storageComboBox.QFrame_0.QListView_0.qt_scrollarea_viewport', event , 77.218669 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(263, 22), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(528, 312), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.storageComboBox.QFrame_0.QListView_0.qt_scrollarea_viewport', event , 77.754499 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(263, 22), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(528, 312), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.storageComboBox.QFrame_0.QListView_0.qt_scrollarea_viewport', event , 77.833729 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(23, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(842, 650), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.okButton', event , 79.557231 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(23, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(842, 650), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_1.okButton', event , 79.644914 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(522, 509), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(842, 650), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 79.973903 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(521, 508), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(841, 649), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 80.784824 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(109, 232), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(429, 373), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 80.885878 )

    ########################
    player.display_comment("""Edit raw data properties: absolute link""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(487, 4), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(487, 4), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 82.58908 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(133, 5), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(473, 64), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QHeaderView_1.qt_scrollarea_viewport', event , 82.692706 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(133, 22), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(473, 81), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QHeaderView_1.qt_scrollarea_viewport', event , 82.775555 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(133, 25), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(473, 107), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport', event , 82.93121 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(132, 26), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(472, 108), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport', event , 83.012873 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(33, 9), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(351, 43), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_tabbar', event , 83.677776 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(33, 9), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(351, 43), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_tabbar', event , 83.785235 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(21, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(361, 59), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.QHeaderView_1.qt_scrollarea_viewport', event , 84.310377 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(23, 16), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(363, 75), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.QHeaderView_1.qt_scrollarea_viewport', event , 84.404871 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(23, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(363, 82), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport', event , 84.487687 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(23, 6), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(363, 88), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport', event , 84.570015 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(23, 17), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(363, 99), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport', event , 84.666703 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(23, 17), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(363, 99), (Qt.RightButton), (Qt.RightButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport', event , 84.835449 )

    event = PyQt4.QtGui.QContextMenuEvent(0, PyQt4.QtCore.QPoint(23, 17), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(363, 99), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport', event , 84.922041 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(363, 99), (Qt.RightButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.QMenu_0', event , 85.005919 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(363, 99), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.QMenu_0', event , 85.086303 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(0, 2), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(363, 101), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.QMenu_0', event , 85.362873 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(4, 10), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(367, 109), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.QMenu_0', event , 85.44342 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(6, 14), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(369, 113), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.QMenu_0', event , 85.524094 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(7, 16), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(370, 115), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.QMenu_0', event , 85.610119 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(10, 16), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(373, 115), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.QMenu_0', event , 85.686875 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(13, 16), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(376, 115), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.QMenu_0', event , 85.76322 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(13, 16), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(376, 115), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.QMenu_0', event , 85.916564 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(13, 16), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(376, 115), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.QMenu_0', event , 85.992818 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(109, 1), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(372, 155), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.axesEdit', event , 87.412105 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(107, 8), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(372, 194), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.rangeMinSpinBox.qt_spinbox_lineedit', event , 87.50688 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(109, 10), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(372, 278), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.storageComboBox', event , 88.931804 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(109, -10), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(372, 278), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.storageComboBox.QFrame_0', event , 89.028983 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(107, 2), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(372, 292), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.storageComboBox.QFrame_0.QListView_0.qt_scrollarea_viewport', event , 90.08741 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(113, 26), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(378, 316), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.storageComboBox.QFrame_0.QListView_0.qt_scrollarea_viewport', event , 90.181089 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(113, 27), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(378, 317), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.storageComboBox.QFrame_0.QListView_0.qt_scrollarea_viewport', event , 90.266024 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(113, 28), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(378, 318), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.storageComboBox.QFrame_0.QListView_0.qt_scrollarea_viewport', event , 90.34739 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(113, 27), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(378, 317), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.storageComboBox.QFrame_0.QListView_0.qt_scrollarea_viewport', event , 90.582925 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(113, 26), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(378, 316), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.storageComboBox.QFrame_0.QListView_0.qt_scrollarea_viewport', event , 90.926595 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(113, 26), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(378, 316), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.storageComboBox.QFrame_0.QListView_0.qt_scrollarea_viewport', event , 91.003933 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(113, 26), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(378, 316), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.storageComboBox.QFrame_0.QListView_0.qt_scrollarea_viewport', event , 91.082644 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(25, 15), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(844, 653), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.okButton', event , 94.299157 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(25, 15), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(844, 653), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.DatasetInfoEditorWidget_Role_0.okButton', event , 94.389637 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(524, 512), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(844, 653), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 94.701486 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(523, 512), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(843, 653), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 95.322719 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(336, 426), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(656, 567), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 95.423186 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(55, 269), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(375, 410), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 95.510198 )

    ########################
    player.display_comment("""Show summary tab""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(434, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(434, 0), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 96.84615 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(440, 8), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(440, 8), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 96.92353 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(459, 17), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(459, 17), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 96.999615 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(214, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(532, 46), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_tabbar', event , 98.09937 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(214, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(532, 46), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_tabbar', event , 98.26204 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(482, 19), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(482, 19), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 99.400979 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(283, 5), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(283, 5), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 99.547883 )

    ########################
    player.display_comment("""Remove all""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(445, 5), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(445, 5), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 100.731601 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(98, 2), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(438, 61), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.fileInfoTabWidgetPage1.laneSummaryTableView.QHeaderView_1.qt_scrollarea_viewport', event , 100.953926 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(94, 19), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(434, 78), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.fileInfoTabWidgetPage1.laneSummaryTableView.QHeaderView_1.qt_scrollarea_viewport', event , 101.047981 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(92, 22), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(432, 81), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.fileInfoTabWidgetPage1.laneSummaryTableView.QHeaderView_1.qt_scrollarea_viewport', event , 101.129913 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(65, 14), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(405, 96), (Qt.RightButton), (Qt.RightButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.fileInfoTabWidgetPage1.laneSummaryTableView.qt_scrollarea_viewport', event , 101.609176 )

    event = PyQt4.QtGui.QContextMenuEvent(0, PyQt4.QtCore.QPoint(65, 14), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(405, 96), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.fileInfoTabWidgetPage1.laneSummaryTableView.qt_scrollarea_viewport', event , 101.69397 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(405, 96), (Qt.RightButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.fileInfoTabWidgetPage1.laneSummaryTableView.QMenu_0', event , 101.778428 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(405, 96), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.fileInfoTabWidgetPage1.laneSummaryTableView.QMenu_0', event , 101.856302 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(0, 1), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(405, 97), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.fileInfoTabWidgetPage1.laneSummaryTableView.QMenu_0', event , 102.602344 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(12, 8), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(417, 104), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.fileInfoTabWidgetPage1.laneSummaryTableView.QMenu_0', event , 102.679632 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(15, 10), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(420, 106), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.fileInfoTabWidgetPage1.laneSummaryTableView.QMenu_0', event , 102.757432 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(15, 10), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(420, 106), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.fileInfoTabWidgetPage1.laneSummaryTableView.QMenu_0', event , 103.111947 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(15, 10), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(420, 106), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.fileInfoTabWidgetPage1.laneSummaryTableView.QMenu_0', event , 103.187935 )

    player.display_comment("SCRIPT COMPLETE")
