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
# Started at: 2014-02-09 21:26:53.073497

def playback_events(player):
    import PyQt4.QtCore
    from PyQt4.QtCore import Qt, QEvent, QPoint
    import PyQt4.QtGui
    
    # The getMainWindow() function is provided by EventRecorderApp
    mainwin = PyQt4.QtGui.QApplication.instance().getMainWindow()

    player.display_comment("SCRIPT STARTING")


    ########################
    player.display_comment("""In this test, we\'ll add multiple images (we\'ll just use the same image over and over), and then label on some of them.""")
    ########################

    ########################
    player.display_comment("""New Project (PixelClassification)""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(497, 4), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(497, 4), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 1.397589 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(105, 9), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(416, 117), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.startupPage.frame.CreateList.qt_scrollarea_viewport.scrollAreaWidgetContents.NewProjectButton_PixelClassificationWorkflow', event , 1.947473 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(105, 9), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(416, 117), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.startupPage.frame.CreateList.qt_scrollarea_viewport.scrollAreaWidgetContents.NewProjectButton_PixelClassificationWorkflow', event , 2.032105 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(44, 15), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(772, 527), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QFileDialog.buttonBox.QPushButton_0', event , 2.724406 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(44, 15), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(772, 527), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QFileDialog.buttonBox.QPushButton_0', event , 2.724406 )

    ########################
    player.display_comment("""Add a file""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(340, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(340, 0), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 3.921633 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(340, 10), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(340, 10), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 3.980572 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(12, 3), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(334, 62), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QHeaderView_1.qt_scrollarea_viewport', event , 4.105052 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(11, 20), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(333, 79), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QHeaderView_1.qt_scrollarea_viewport', event , 4.16702 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(14, 14), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(336, 98), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.QWidget_0.AddFileButton_0', event , 4.509873 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(15, -11), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(337, 99), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 4.570182 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(15, -11), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(337, 99), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 4.628257 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(25, 3), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(347, 113), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 4.939026 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(29, 9), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(351, 119), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 4.996128 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(30, 11), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(352, 121), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 5.054553 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(30, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(352, 122), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 5.150067 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(30, 15), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(352, 125), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 5.208323 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(30, 15), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(352, 125), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 5.300575 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(30, 15), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(352, 125), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 5.37921 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2f, Qt.NoModifier, """/""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 7.745704 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2f, Qt.NoModifier, """/""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 7.828609 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x48, Qt.NoModifier, """h""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 8.192473 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x48, Qt.NoModifier, """h""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 8.252084 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4f, Qt.NoModifier, """o""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 8.346806 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4d, Qt.NoModifier, """m""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 8.408111 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4f, Qt.NoModifier, """o""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 8.461439 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 8.514065 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4d, Qt.NoModifier, """m""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 8.567537 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 8.62146 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2f, Qt.NoModifier, """/""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 8.673495 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2f, Qt.NoModifier, """/""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 8.726031 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x56, Qt.NoModifier, """v""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 9.244919 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x56, Qt.NoModifier, """v""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 9.350234 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 9.408166 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x47, Qt.NoModifier, """g""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 9.485032 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 9.537786 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x47, Qt.NoModifier, """g""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 9.588112 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x52, Qt.NoModifier, """r""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 9.642279 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x52, Qt.NoModifier, """r""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 9.69536 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 9.749452 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 9.802733 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 9.85574 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 9.907984 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 9.960931 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 10.013154 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2f, Qt.NoModifier, """/""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 10.736913 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2f, Qt.NoModifier, """/""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 10.823508 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x46, Qt.NoModifier, """f""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 12.169265 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x46, Qt.NoModifier, """f""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 12.255531 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 12.307507 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 12.361973 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4b, Qt.NoModifier, """k""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 12.41392 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4b, Qt.NoModifier, """k""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 12.46812 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 12.518705 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 12.574909 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 12.628172 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 12.912422 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 12.999612 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 13.13441 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 13.240119 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 13.342166 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 13.395666 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 13.448954 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x53, Qt.NoModifier, """s""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 13.501842 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 13.559559 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x53, Qt.NoModifier, """s""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 13.612917 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 13.665786 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 13.767594 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 13.881563 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 13.959178 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2d, Qt.NoModifier, """-""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 14.011504 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x44, Qt.NoModifier, """d""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 14.100013 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x44, Qt.NoModifier, """d""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 14.182889 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 14.236606 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 14.297735 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 14.350138 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 14.403399 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 14.456343 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 14.510202 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000004, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 14.937381 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000004, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 14.99067 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x52, Qt.NoModifier, """r""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 16.415554 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x52, Qt.NoModifier, """r""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 16.503523 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 16.555841 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 16.640905 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 16.693568 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x44, Qt.NoModifier, """d""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 16.747264 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 16.800825 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x44, Qt.NoModifier, """d""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 16.853695 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 16.905368 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 16.991961 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 17.072224 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 17.191047 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x55, Qt.NoModifier, """u""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 17.384944 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x49, Qt.NoModifier, """i""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 17.448302 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x55, Qt.NoModifier, """u""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 17.501211 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x49, Qt.NoModifier, """i""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 17.553236 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 17.605173 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 17.65794 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 17.711128 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 17.765491 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x38, Qt.NoModifier, """8""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 19.952284 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x38, Qt.NoModifier, """8""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 20.040148 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 20.584323 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 20.688165 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 20.768806 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 20.880083 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x32, Qt.NoModifier, """2""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 23.298403 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x44, Qt.NoModifier, """d""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 23.361747 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x32, Qt.NoModifier, """2""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 23.422421 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x44, Qt.NoModifier, """d""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 23.474452 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2e, Qt.NoModifier, """.""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 23.561232 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2e, Qt.NoModifier, """.""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 23.671553 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 23.752704 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 23.818462 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x50, Qt.NoModifier, """p""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 23.903977 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x50, Qt.NoModifier, """p""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 23.964181 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x59, Qt.NoModifier, """y""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 24.052722 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x59, Qt.NoModifier, """y""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 24.128932 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000004, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 25.703384 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(30, 43), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(352, 125), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport', event , 26.170449 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000004, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.QWidget_0.AddFileButton_0', event , 26.249384 )

    ########################
    player.display_comment("""Repeat 4 more times""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(393, 3), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(393, 3), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 28.028339 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(78, 75), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(398, 132), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0', event , 31.453669 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(57, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(397, 126), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.QWidget_0.AddFileButton_0', event , 31.548766 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(56, -14), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(396, 126), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 31.630476 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(56, -14), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(396, 126), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 31.707461 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(56, -9), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(396, 131), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 32.324312 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(54, -2), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(394, 138), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 32.403298 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(52, 3), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(392, 143), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 32.481896 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(50, 11), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(390, 151), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 32.555965 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(50, 11), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(390, 151), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 32.938037 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(50, 11), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(390, 151), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 33.01349 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x52, Qt.NoModifier, """r""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 34.620161 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 34.704511 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x52, Qt.NoModifier, """r""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 34.774989 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 34.843492 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 34.918559 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x44, Qt.NoModifier, """d""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 34.986675 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 35.047436 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x44, Qt.NoModifier, """d""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 35.125558 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 35.256436 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 35.385503 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 35.494068 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 35.564531 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x55, Qt.NoModifier, """u""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 35.867458 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x49, Qt.NoModifier, """i""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 35.96416 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x55, Qt.NoModifier, """u""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 36.037533 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x49, Qt.NoModifier, """i""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 36.103863 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 36.171363 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 36.243384 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 36.309911 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 36.377828 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x38, Qt.NoModifier, """8""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 36.448484 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x38, Qt.NoModifier, """8""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 36.516059 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 36.86274 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 36.930921 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 36.999273 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2d, Qt.NoModifier, """-""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 37.070818 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x32, Qt.NoModifier, """2""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 37.20192 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x32, Qt.NoModifier, """2""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 37.282718 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x44, Qt.NoModifier, """d""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 37.537915 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x44, Qt.NoModifier, """d""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 37.617217 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2e, Qt.NoModifier, """.""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 37.705129 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2e, Qt.NoModifier, """.""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 37.830292 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 37.900436 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 37.967885 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x50, Qt.NoModifier, """p""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 38.03807 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x50, Qt.NoModifier, """p""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 38.109762 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x59, Qt.NoModifier, """y""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 38.177914 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x59, Qt.NoModifier, """y""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 38.246946 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000004, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 38.318997 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000004, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 38.414915 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(70, 10), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(390, 151), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 39.059274 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(70, 10), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(390, 151), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.viewerStack.DatasetViewer_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 39.224158 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(73, 9), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(393, 150), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.viewerStack.DatasetViewer_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 39.854098 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(100, 3), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(420, 144), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.viewerStack.DatasetViewer_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 39.961264 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(102, 2), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(422, 143), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.viewerStack.DatasetViewer_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 40.067788 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(105, 1), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(425, 142), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.viewerStack.DatasetViewer_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 40.176876 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(122, 75), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(442, 132), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0', event , 40.314983 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(117, 39), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(457, 121), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport', event , 40.417466 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(123, 34), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(463, 116), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport', event , 40.525705 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(123, 34), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(463, 116), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport', event , 40.806186 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(123, 4), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(463, 116), -1560, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.QWidget_0', event , 40.914871 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(63, 19), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(403, 122), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.QWidget_0.AddFileButton_0', event , 42.444399 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(63, -7), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(403, 122), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 42.555544 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(63, 1), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(403, 130), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 43.233545 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(61, 5), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(401, 134), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 43.326635 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(59, 8), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(399, 137), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 43.430938 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(59, 10), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(399, 139), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 43.527072 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(59, 11), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(399, 140), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 43.628804 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(59, 11), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(399, 140), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 44.111201 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(59, 11), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(399, 140), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 44.205217 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x52, Qt.NoModifier, """r""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 45.347177 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 45.441129 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x52, Qt.NoModifier, """r""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 45.534867 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 45.619151 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 45.703677 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x44, Qt.NoModifier, """d""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 45.791512 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 45.875078 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x44, Qt.NoModifier, """d""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 45.957771 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 46.047188 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 46.129327 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 46.212307 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 46.301218 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x55, Qt.NoModifier, """u""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 46.384283 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x49, Qt.NoModifier, """i""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 46.46759 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x55, Qt.NoModifier, """u""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 46.557827 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x49, Qt.NoModifier, """i""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 46.638758 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 46.720405 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 46.812049 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 46.892205 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 46.975103 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x38, Qt.NoModifier, """8""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 47.064388 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x38, Qt.NoModifier, """8""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 47.143534 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 47.230476 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 47.319354 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 47.402772 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 47.485089 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x32, Qt.NoModifier, """2""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 48.027741 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x44, Qt.NoModifier, """d""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 48.112747 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x32, Qt.NoModifier, """2""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 48.203381 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x44, Qt.NoModifier, """d""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 48.283768 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2e, Qt.NoModifier, """.""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 48.364707 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2e, Qt.NoModifier, """.""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 48.452775 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 48.533844 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 48.61529 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x50, Qt.NoModifier, """p""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 48.704053 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x50, Qt.NoModifier, """p""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 48.786568 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x59, Qt.NoModifier, """y""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 48.870465 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x59, Qt.NoModifier, """y""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 48.959818 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000004, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 49.040607 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(81, 1), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(399, 140), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0', event , 49.484313 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(81, 1), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(399, 140), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0', event , 50.049191 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(78, 75), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(398, 132), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0', event , 50.289518 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(190, 29), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(530, 111), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport', event , 51.070104 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(197, 29), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(537, 111), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport', event , 51.187592 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(190, 4), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(530, 116), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.QWidget_0', event , 52.023611 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(190, 15), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(530, 116), -1680, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.QWidget_0', event , 52.163238 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(190, 15), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(530, 116), -1680, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.QWidget_0', event , 52.283166 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(61, 14), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(401, 117), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.QWidget_0.AddFileButton_0', event , 53.315669 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(61, -12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(401, 117), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 53.449883 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(60, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(400, 129), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 53.941594 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(60, 10), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(400, 139), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 54.069394 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(58, 14), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(398, 143), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 54.179086 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(58, 14), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(398, 143), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 54.307227 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(58, 14), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(398, 143), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 54.41818 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x52, Qt.NoModifier, """r""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 55.683636 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 55.812537 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x52, Qt.NoModifier, """r""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 55.912785 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 56.026807 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 56.122759 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x44, Qt.NoModifier, """d""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 56.234015 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 56.331505 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x44, Qt.NoModifier, """d""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 56.443659 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 56.539924 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 56.651326 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 56.747784 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 56.862082 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x55, Qt.NoModifier, """u""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 56.959136 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x49, Qt.NoModifier, """i""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 57.068852 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x55, Qt.NoModifier, """u""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 57.164615 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x49, Qt.NoModifier, """i""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 57.272476 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 57.368816 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 57.482728 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 57.578924 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 57.691472 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x38, Qt.NoModifier, """8""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 57.789129 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x38, Qt.NoModifier, """8""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 57.898874 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 57.99493 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 58.102225 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 58.198886 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 58.306757 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x32, Qt.NoModifier, """2""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 58.404241 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x32, Qt.NoModifier, """2""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 58.515161 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x44, Qt.NoModifier, """d""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 58.613911 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x44, Qt.NoModifier, """d""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 58.725857 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2e, Qt.NoModifier, """.""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 58.956473 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2e, Qt.NoModifier, """.""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 59.091295 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 59.197705 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 59.295469 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x50, Qt.NoModifier, """p""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 59.40388 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x50, Qt.NoModifier, """p""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 59.500193 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x59, Qt.NoModifier, """y""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 59.607587 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x59, Qt.NoModifier, """y""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 59.706557 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000004, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 59.814953 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000004, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 59.979415 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(119, 26), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(459, 108), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport', event , 61.246776 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(128, 25), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(468, 107), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport', event , 61.398806 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(119, 22), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(459, 104), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport', event , 61.551856 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(151, 22), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(491, 104), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport', event , 61.702833 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(153, 22), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(493, 104), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport', event , 61.844357 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(153, 22), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(493, 104), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport', event , 62.051556 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(153, 3), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(493, 104), -1680, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.QWidget_0', event , 62.209733 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(153, 3), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(493, 104), -3120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.QWidget_0', event , 62.344862 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(69, 15), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(409, 118), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.QWidget_0.AddFileButton_0', event , 63.341916 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(69, -11), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(409, 118), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 63.506449 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(73, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(413, 129), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 64.368531 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(75, 6), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(415, 135), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 64.519908 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(74, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(414, 141), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 64.647336 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(73, 16), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(413, 145), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 64.798118 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(73, 16), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(413, 145), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 65.09089 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(73, 16), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(413, 145), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 65.243632 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x52, Qt.NoModifier, """r""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 66.324815 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 66.472425 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x52, Qt.NoModifier, """r""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 66.592761 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 66.722766 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 66.833017 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x44, Qt.NoModifier, """d""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 66.958569 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 67.069385 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x44, Qt.NoModifier, """d""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 67.195843 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 67.306877 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 67.435642 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 67.54725 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 67.672462 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x55, Qt.NoModifier, """u""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 67.783411 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x49, Qt.NoModifier, """i""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 67.911281 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x55, Qt.NoModifier, """u""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 68.022653 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x49, Qt.NoModifier, """i""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 68.148476 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 68.258567 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 68.387437 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 68.499279 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 68.625994 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x38, Qt.NoModifier, """8""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 68.73703 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x38, Qt.NoModifier, """8""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 68.864526 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 68.980288 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 69.105093 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 69.217934 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 69.343971 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x32, Qt.NoModifier, """2""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 69.45399 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x44, Qt.NoModifier, """d""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 69.581753 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x32, Qt.NoModifier, """2""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 69.69261 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x44, Qt.NoModifier, """d""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 69.819767 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2e, Qt.NoModifier, """.""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 69.929116 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2e, Qt.NoModifier, """.""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 70.056096 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 70.166195 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 70.293922 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x50, Qt.NoModifier, """p""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 70.405795 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x50, Qt.NoModifier, """p""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 70.531609 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x59, Qt.NoModifier, """y""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 70.640204 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x59, Qt.NoModifier, """y""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 70.768211 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000004, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 70.87991 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000004, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 71.096535 )

    ########################
    player.display_comment("""Select some features""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(328, 9), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(328, 9), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 74.888191 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(133, 10), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(139, 311), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QAbstractButton_1', event , 75.602485 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(133, 10), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(139, 311), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QAbstractButton_1', event , 75.771287 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(148, 5), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(154, 133), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.Form.SelectFeaturesButton', event , 77.921567 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(148, 5), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(154, 133), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.Form.SelectFeaturesButton', event , 78.107766 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(2, 11), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(473, 234), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.FeaureDlg.featureTableWidget.QHeaderView_1.qt_scrollarea_viewport', event , 79.144749 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(36, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(507, 247), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.FeaureDlg.featureTableWidget.qt_scrollarea_viewport', event , 79.33823 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(39, 4), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(510, 251), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.FeaureDlg.featureTableWidget.qt_scrollarea_viewport', event , 79.539604 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(40, 6), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(511, 253), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.FeaureDlg.featureTableWidget.qt_scrollarea_viewport', event , 79.730253 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(40, 6), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(511, 253), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.FeaureDlg.featureTableWidget.qt_scrollarea_viewport', event , 79.910485 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(40, 7), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(511, 254), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.FeaureDlg.featureTableWidget.qt_scrollarea_viewport', event , 80.071512 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(40, 7), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(511, 254), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.FeaureDlg.featureTableWidget.qt_scrollarea_viewport', event , 80.259551 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(79, 10), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(550, 257), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.FeaureDlg.featureTableWidget.qt_scrollarea_viewport', event , 80.449927 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(79, 10), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(550, 257), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.FeaureDlg.featureTableWidget.qt_scrollarea_viewport', event , 80.628154 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(79, 10), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(550, 257), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.FeaureDlg.featureTableWidget.qt_scrollarea_viewport', event , 80.793602 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(78, 33), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(549, 280), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.FeaureDlg.featureTableWidget.qt_scrollarea_viewport', event , 80.985075 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(78, 33), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(549, 280), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.FeaureDlg.featureTableWidget.qt_scrollarea_viewport', event , 81.170637 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(78, 33), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(549, 280), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.FeaureDlg.featureTableWidget.qt_scrollarea_viewport', event , 81.321486 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(21, 9), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(662, 511), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.FeaureDlg.ok', event , 82.016122 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(21, 9), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(662, 511), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.FeaureDlg.ok', event , 82.207948 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(22, 32), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(662, 511), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.FeaureDlg.ok', event , 82.609082 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(351, 484), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(662, 511), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 82.802652 )

    ########################
    player.display_comment("""Open training page""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(408, 8), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(408, 8), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 84.529822 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(127, 9), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(133, 339), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QAbstractButton_2', event , 85.367615 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(127, 9), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(133, 339), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QAbstractButton_2', event , 85.58022 )

    ########################
    player.display_comment("""Add 2 label classes""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(310, 1), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(310, 1), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 88.837555 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(135, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(150, 278), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.AddLabelButton', event , 89.700599 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(135, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(150, 278), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.AddLabelButton', event , 89.941065 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(110, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(125, 278), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.AddLabelButton', event , 93.568698 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(110, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(125, 278), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.AddLabelButton', event , 93.832317 )

    ########################
    player.display_comment("""Draw some labels for both classes""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(297, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(297, 0), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 95.703662 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(60, 11), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(77, 164), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.QTableView_0.qt_scrollarea_viewport', event , 96.576656 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(60, 11), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(77, 164), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.QTableView_0.qt_scrollarea_viewport', event , 96.852513 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(11, 219), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(322, 246), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 97.195336 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(262, 296), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(573, 323), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 97.517612 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(303, 301), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(614, 328), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 97.817167 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(312, 321), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(623, 348), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 98.123153 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(312, 330), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(623, 357), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 98.426907 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000021, (Qt.ControlModifier), """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3', event , 98.702645 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(312, 330), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(623, 357), 2760, Qt.NoButton, (Qt.ControlModifier), 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 98.965935 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(312, 330), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(623, 357), 120, Qt.NoButton, (Qt.ControlModifier), 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 99.943144 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(312, 330), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(623, 357), 2280, Qt.NoButton, (Qt.ControlModifier), 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 100.245575 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(312, 330), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(623, 357), -120, Qt.NoButton, (Qt.ControlModifier), 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 101.419414 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(312, 330), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(623, 357), -600, Qt.NoButton, (Qt.ControlModifier), 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 101.724222 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(312, 330), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(623, 357), -120, Qt.NoButton, (Qt.ControlModifier), 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 102.968297 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(312, 330), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(623, 357), -120, Qt.NoButton, (Qt.ControlModifier), 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 104.362928 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000021, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3', event , 105.739509 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(147, 230), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(458, 257), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 106.012402 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(94, 153), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(405, 180), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 106.311513 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(74, 150), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(385, 177), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 106.614515 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(67, 175), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(378, 202), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 106.913324 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(66, 177), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(377, 204), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 107.217414 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(66, 177), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(377, 204), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 107.522057 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(108, 147), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(419, 174), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 107.833258 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(140, 122), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(451, 149), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 108.122789 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(140, 123), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(451, 150), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 108.668702 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(150, 284), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(461, 311), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 108.963009 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(152, 401), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(463, 428), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 109.264142 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(155, 459), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(466, 486), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 109.555389 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(155, 459), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(466, 486), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 110.974887 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(110, 461), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(421, 488), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 111.285636 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(87, 461), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(398, 488), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 111.59537 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(87, 461), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(398, 488), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 111.907057 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(95, 461), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(406, 488), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 112.394827 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(190, 463), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(501, 490), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 112.688038 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(194, 462), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(505, 489), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 112.99033 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(194, 462), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(505, 489), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 113.642587 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(70, 39), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(87, 192), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.QTableView_0.qt_scrollarea_viewport', event , 114.406377 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(70, 39), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(87, 192), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.QTableView_0.qt_scrollarea_viewport', event , 114.702097 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(263, 160), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(574, 187), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 114.98533 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(380, 157), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(691, 184), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 115.293309 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(336, 157), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(647, 184), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 115.592567 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(337, 176), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(648, 203), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 115.898596 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(337, 178), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(648, 205), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 116.308296 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(335, 178), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(646, 205), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 116.603567 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(335, 178), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(646, 205), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 116.90074 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(353, 133), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(664, 160), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 117.210392 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(411, 109), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(722, 136), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 117.502491 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(453, 139), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(764, 166), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 117.803101 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(460, 175), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(771, 202), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 118.094085 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(456, 250), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(767, 277), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 118.397655 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(440, 306), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(751, 333), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 118.693986 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(424, 348), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(735, 375), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 118.998711 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(398, 390), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(709, 417), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 119.29661 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(365, 415), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(676, 442), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 119.600706 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(335, 437), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(646, 464), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 119.894122 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(322, 445), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(633, 472), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 120.19242 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(334, 445), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(645, 472), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 120.691475 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(386, 445), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(697, 472), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 120.991566 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(449, 445), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(760, 472), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 121.286162 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(492, 443), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(803, 470), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 121.588909 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(492, 443), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(803, 470), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 122.421146 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(489, 443), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(800, 470), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 123.458285 )

    ########################
    player.display_comment("""Now switch images""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(356, 15), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(356, 15), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 124.77527 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(43, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(201, 496), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_3_lane_0.checkShowSegmentation', event , 125.071136 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(185, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(284, 457), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo', event , 125.81613 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(185, -8), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(284, 457), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.QFrame_0', event , 126.111594 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(143, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(244, 467), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.QFrame_0.QListView_0.qt_scrollarea_viewport', event , 127.836689 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(116, 16), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(217, 483), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.QFrame_0.QListView_0.qt_scrollarea_viewport', event , 128.109705 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(109, 25), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(210, 492), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.QFrame_0.QListView_0.qt_scrollarea_viewport', event , 128.381984 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(105, 29), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(206, 496), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.QFrame_0.QListView_0.qt_scrollarea_viewport', event , 128.649946 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(105, 30), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(206, 497), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.QFrame_0.QListView_0.qt_scrollarea_viewport', event , 129.003341 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(103, 34), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(204, 501), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.QFrame_0.QListView_0.qt_scrollarea_viewport', event , 129.275542 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(98, 28), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(199, 495), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.QFrame_0.QListView_0.qt_scrollarea_viewport', event , 129.552874 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(95, 25), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(196, 492), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.QFrame_0.QListView_0.qt_scrollarea_viewport', event , 129.822719 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(95, 25), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(196, 492), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.QFrame_0.QListView_0.qt_scrollarea_viewport', event , 130.375465 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(95, 25), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(196, 492), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.QFrame_0.QListView_0.qt_scrollarea_viewport', event , 130.644753 )

    ########################
    player.display_comment("""Draw more labels""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(116, 19), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(427, 46), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_1.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 136.661693 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(200, 273), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(511, 300), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_1.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 136.99752 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(250, 312), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(561, 339), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_1.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 137.319083 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000021, (Qt.ControlModifier), """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo', event , 137.616488 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(251, 313), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(562, 340), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier))
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_1.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 138.390908 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(256, 345), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(567, 372), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier))
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_1.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 138.704065 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(261, 356), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(572, 383), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier))
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_1.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 139.015482 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(262, 356), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(573, 383), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier))
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_1.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 139.328145 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(262, 356), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(573, 383), 120, Qt.NoButton, (Qt.ControlModifier), 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_1.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 140.545676 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(262, 356), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(573, 383), 2040, Qt.NoButton, (Qt.ControlModifier), 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_1.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 140.867536 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(262, 356), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(573, 383), 120, Qt.NoButton, (Qt.ControlModifier), 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_1.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 142.055815 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(262, 356), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(573, 383), 1080, Qt.NoButton, (Qt.ControlModifier), 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_1.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 142.384393 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000021, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo', event , 143.217615 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(95, 290), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(406, 317), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_1.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 143.514399 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(55, 17), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(72, 170), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_1.QWidget_1.labelListView.QTableView_0.qt_scrollarea_viewport', event , 144.02892 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(55, 17), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(72, 170), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_1.QWidget_1.labelListView.QTableView_0.qt_scrollarea_viewport', event , 144.348279 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(162, 156), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(473, 183), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_1.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 144.654939 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(298, 156), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(609, 183), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_1.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 144.976588 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(386, 139), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(697, 166), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_1.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 145.310824 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(196, 108), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(507, 135), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_1.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 145.628678 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(311, 96), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(622, 123), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_1.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 145.96034 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(288, 89), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(599, 116), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_1.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 146.278712 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(287, 89), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(598, 116), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_1.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 146.612871 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(287, 89), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(598, 116), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_1.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 146.924415 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(344, 52), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(655, 79), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_1.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 147.252531 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(344, 53), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(655, 80), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_1.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 147.958826 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(329, 161), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(640, 188), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_1.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 148.276634 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(329, 163), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(640, 190), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_1.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 148.599877 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(329, 163), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(640, 190), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_1.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 148.986746 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(269, 163), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(580, 190), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_1.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 149.320307 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(269, 163), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(580, 190), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_1.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 149.659092 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(439, 164), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(750, 191), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_1.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 149.981825 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(439, 164), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(750, 191), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_1.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 150.299215 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(39, 49), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(56, 202), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_1.QWidget_1.labelListView.QTableView_0.qt_scrollarea_viewport', event , 150.952535 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(39, 49), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(56, 202), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_1.QWidget_1.labelListView.QTableView_0.qt_scrollarea_viewport', event , 151.273722 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(215, 249), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(526, 276), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_1.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 151.581405 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(229, 273), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(540, 300), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_1.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 151.907929 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(225, 289), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(536, 316), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_1.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 152.239248 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(275, 357), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(586, 384), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_1.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 152.56245 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(266, 361), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(577, 388), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_1.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 152.891377 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(266, 361), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(577, 388), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_1.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 153.216144 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(310, 324), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(621, 351), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_1.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 153.54714 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(349, 344), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(660, 371), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_1.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 153.861619 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(358, 413), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(669, 440), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_1.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 154.19598 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(324, 475), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(635, 502), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_1.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 154.517614 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(275, 508), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(586, 535), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_1.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 154.84716 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(232, 501), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(543, 528), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_1.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 155.16252 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(233, 490), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(544, 517), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_1.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 155.490781 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(266, 493), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(577, 520), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_1.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 155.81132 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(280, 503), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(591, 530), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_1.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 156.139544 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(299, 511), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(610, 538), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_1.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 156.458023 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(353, 509), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(664, 536), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_1.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 156.781573 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(386, 486), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(697, 513), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_1.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 157.096846 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(385, 477), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(696, 504), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_1.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 157.418717 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(385, 477), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(696, 504), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_1.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 157.765611 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(359, 475), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(670, 502), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_1.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 158.102194 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(352, 473), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(663, 500), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_1.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 158.438712 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(217, 441), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(528, 468), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_1.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 158.771188 )

    ########################
    player.display_comment("""Live update""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(328, 5), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(328, 5), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 160.596015 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(145, 7), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(160, 329), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_1.QWidget_1.liveUpdateButton', event , 161.670773 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(145, 7), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(160, 329), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_1.QWidget_1.liveUpdateButton', event , 161.984312 )

    ########################
    player.display_comment("""We\'re done here""")
    ########################

    player.display_comment("SCRIPT COMPLETE")
