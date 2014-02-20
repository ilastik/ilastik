# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Copyright 2011-2014, the ilastik developers


# Event Recording
# Created by Stuart
# Started at: 2014-02-09 21:33:02.224095

def playback_events(player):
    import PyQt4.QtCore
    from PyQt4.QtCore import Qt, QEvent, QPoint
    import PyQt4.QtGui
    
    # The getMainWindow() function is provided by EventRecorderApp
    mainwin = PyQt4.QtGui.QApplication.instance().getMainWindow()

    player.display_comment("SCRIPT STARTING")


    ########################
    player.display_comment("""In this recording, we\'ll create an object classification project and add (generated) data to it and do some basic labeling and training.""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(93, 2), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(93, 2), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 2.544991 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(36, 13), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(36, 13), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 2.600382 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(326, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(326, 0), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 7.427202 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(323, 1), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(323, 1), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 7.482101 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(322, 1), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(322, 1), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 7.537225 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(319, 3), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(319, 3), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 7.590121 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(306, 8), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(306, 8), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 7.643776 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(232, 15), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(232, 15), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 7.698017 )

    ########################
    player.display_comment("""New Project (Object Classification from binary image)""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(350, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(350, 0), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 9.225622 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(66, 10), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(377, 510), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.startupPage.frame.CreateList.qt_scrollarea_viewport.scrollAreaWidgetContents.NewProjectButton_ObjectClassificationWorkflowBinary', event , 11.608376 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(66, 10), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(377, 510), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.startupPage.frame.CreateList.qt_scrollarea_viewport.scrollAreaWidgetContents.NewProjectButton_ObjectClassificationWorkflowBinary', event , 11.692058 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000004, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.QFileDialog.fileNameEdit', event , 13.143786 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000004, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.QFileDialog', event , 13.201951 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(6, 16), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(6, 16), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 14.3916 )

    ########################
    player.display_comment("""Add raw data""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(74, 75), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(394, 132), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1', event , 15.166633 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(71, 41), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(393, 123), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport', event , 15.230149 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(68, 20), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(390, 104), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport.QWidget_0.AddFileButton_0', event , 15.576261 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(68, -6), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(390, 104), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 15.648941 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(70, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(392, 110), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 16.069169 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(71, 11), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(393, 121), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 16.128544 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(71, 18), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(393, 128), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 16.187173 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(70, 18), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(392, 128), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 16.510665 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(70, 18), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(392, 128), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 16.569781 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(70, 18), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(392, 128), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport.QWidget_0.AddFileButton_0.QMenu_0', event , 16.62968 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2f, Qt.NoModifier, """/""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 17.934572 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2f, Qt.NoModifier, """/""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 17.997316 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x48, Qt.NoModifier, """h""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 18.14836 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x48, Qt.NoModifier, """h""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 18.203484 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4f, Qt.NoModifier, """o""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 18.286533 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4d, Qt.NoModifier, """m""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 18.367509 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4f, Qt.NoModifier, """o""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 18.422714 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 18.476345 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4d, Qt.NoModifier, """m""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 18.53169 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 18.584924 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2f, Qt.NoModifier, """/""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 18.638257 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2f, Qt.NoModifier, """/""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 18.69195 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x56, Qt.NoModifier, """v""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 19.284288 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x56, Qt.NoModifier, """v""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 19.348955 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 19.404381 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 19.500145 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x47, Qt.NoModifier, """g""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 19.553188 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x47, Qt.NoModifier, """g""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 19.606782 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x52, Qt.NoModifier, """r""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 19.668372 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 19.740354 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x52, Qt.NoModifier, """r""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 19.793788 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 19.848959 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 19.903724 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 19.957406 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 20.012262 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 20.066322 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2f, Qt.NoModifier, """/""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 20.12035 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2f, Qt.NoModifier, """/""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 20.176262 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x46, Qt.NoModifier, """f""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 20.786745 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x46, Qt.NoModifier, """f""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 20.874862 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 20.928364 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 20.982676 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4b, Qt.NoModifier, """k""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 21.035986 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4b, Qt.NoModifier, """k""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 21.090577 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 21.145857 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 21.201507 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 21.256347 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 21.33665 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 21.40371 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 21.562569 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 21.75353 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 21.830364 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 21.885134 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 21.940226 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x53, Qt.NoModifier, """s""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 22.013657 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 22.068879 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x53, Qt.NoModifier, """s""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 22.123434 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x53, Qt.NoModifier, """s""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 22.176858 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 22.227545 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x53, Qt.NoModifier, """s""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 22.286715 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000003, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 22.788386 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000003, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 22.86004 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 22.913544 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 22.972954 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x29, (Qt.ShiftModifier), """)""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 23.027487 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x29, (Qt.ShiftModifier), """)""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 23.081148 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 23.138527 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 23.191755 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000003, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 23.612748 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000003, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 23.679862 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000003, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 23.811844 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000003, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 23.906916 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2f, Qt.NoModifier, """/""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 24.053198 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2f, Qt.NoModifier, """/""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 24.114379 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x44, Qt.NoModifier, """d""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 24.283801 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x44, Qt.NoModifier, """d""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 24.362752 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 24.41825 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 24.474349 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 24.530024 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 24.586927 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 24.643383 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 24.699472 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000003, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 25.580333 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000003, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 25.636747 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000003, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 25.694213 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000003, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 25.750955 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000003, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 25.856261 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000003, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 25.912354 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000003, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 25.970083 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000003, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 26.027358 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000003, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 26.084663 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000003, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 26.144352 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 26.852873 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 26.924245 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 26.987592 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 27.040785 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x44, Qt.NoModifier, """d""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 27.094933 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x44, Qt.NoModifier, """d""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 27.156981 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 27.212262 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 27.267518 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 27.321127 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 27.376357 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 27.428018 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 27.486217 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000004, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 27.539376 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000004, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 27.594332 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x43, Qt.NoModifier, """c""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 29.269266 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x43, Qt.NoModifier, """c""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 29.359749 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x55, Qt.NoModifier, """u""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 29.413148 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x55, Qt.NoModifier, """u""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 29.46642 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x42, Qt.NoModifier, """b""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 29.522232 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x42, Qt.NoModifier, """b""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 29.576823 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 29.631512 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 29.687043 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 29.740697 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 29.966988 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 31.467622 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 31.556353 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 31.634669 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 31.687397 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4f, Qt.NoModifier, """o""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 32.115394 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4f, Qt.NoModifier, """o""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 32.195758 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x42, Qt.NoModifier, """b""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 32.276372 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x42, Qt.NoModifier, """b""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 32.333227 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4a, Qt.NoModifier, """j""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 32.420276 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4a, Qt.NoModifier, """j""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 32.531148 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 32.585415 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x43, Qt.NoModifier, """c""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 32.639421 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 32.6953 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x43, Qt.NoModifier, """c""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 32.748384 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 32.840444 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 32.947299 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x53, Qt.NoModifier, """s""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 33.001571 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x53, Qt.NoModifier, """s""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 33.056966 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 33.367172 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 33.507695 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 33.602538 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 33.690785 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x52, Qt.NoModifier, """r""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 35.393752 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 35.484293 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x52, Qt.NoModifier, """r""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 35.538831 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x57, Qt.NoModifier, """w""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 35.593348 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 35.647625 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x57, Qt.NoModifier, """w""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 35.701578 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2e, Qt.NoModifier, """.""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 35.755962 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2e, Qt.NoModifier, """.""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 35.859164 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 35.940444 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 35.99538 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x50, Qt.NoModifier, """p""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 36.074863 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x50, Qt.NoModifier, """p""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 36.170851 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x59, Qt.NoModifier, """y""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 36.243489 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x59, Qt.NoModifier, """y""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 36.29799 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000004, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 36.380273 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(70, 46), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(392, 128), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.qt_scrollarea_viewport', event , 36.85158 )

    ########################
    player.display_comment("""Add binary data""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(396, 7), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(396, 7), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 38.992417 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(225, 1), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(545, 58), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1', event , 39.243047 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(210, 14), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(550, 73), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.QHeaderView_1.qt_scrollarea_viewport', event , 39.331147 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(208, 13), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(548, 72), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.QHeaderView_1.qt_scrollarea_viewport', event , 39.415688 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(188, 1), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(528, 60), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1.QHeaderView_1.qt_scrollarea_viewport', event , 39.499047 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(195, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(515, 57), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_1', event , 39.588607 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(165, 13), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(483, 47), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_tabbar', event , 40.000914 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(165, 13), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(483, 47), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_tabbar', event , 40.092315 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(146, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(466, 57), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0', event , 40.680261 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(102, 15), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(442, 74), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.QHeaderView_1.qt_scrollarea_viewport', event , 40.76579 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(78, 8), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(418, 90), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.AddFileButton_0', event , 41.21683 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(78, -22), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(418, 90), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.AddFileButton_0.QMenu_0', event , 41.309356 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(79, 1), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(419, 113), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.AddFileButton_0.QMenu_0', event , 41.995607 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(78, 17), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(418, 129), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.AddFileButton_0.QMenu_0', event , 42.07244 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(77, 17), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(417, 129), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.AddFileButton_0.QMenu_0', event , 42.258057 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(77, 17), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(417, 129), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.AddFileButton_0.QMenu_0', event , 42.335097 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(77, 17), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(417, 129), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0.qt_scrollarea_viewport.AddFileButton_0.QMenu_0', event , 42.420241 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x43, Qt.NoModifier, """c""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 44.420167 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x55, Qt.NoModifier, """u""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 44.502957 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x43, Qt.NoModifier, """c""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 44.57855 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x55, Qt.NoModifier, """u""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 44.65218 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x42, Qt.NoModifier, """b""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 44.72367 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x42, Qt.NoModifier, """b""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 44.794942 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 44.869245 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 44.940249 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 45.158387 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 45.242415 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 45.32152 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 45.391665 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4f, Qt.NoModifier, """o""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 45.461545 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4f, Qt.NoModifier, """o""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 45.53623 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x42, Qt.NoModifier, """b""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 45.607915 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x42, Qt.NoModifier, """b""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 45.680446 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4a, Qt.NoModifier, """j""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 45.757546 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4a, Qt.NoModifier, """j""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 45.864604 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x43, Qt.NoModifier, """c""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 45.935903 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x43, Qt.NoModifier, """c""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 46.025646 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000003, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 46.578525 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 46.664615 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000003, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 46.737814 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x43, Qt.NoModifier, """c""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 46.809745 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x45, Qt.NoModifier, """e""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 46.887015 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x43, Qt.NoModifier, """c""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 46.958301 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 47.029794 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x53, Qt.NoModifier, """s""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 47.104897 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x54, Qt.NoModifier, """t""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 47.175917 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x53, Qt.NoModifier, """s""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 47.247418 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000020, (Qt.ShiftModifier), """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 47.799311 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 47.869771 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x5f, (Qt.ShiftModifier), """_""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 47.94647 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000020, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 48.017285 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x42, Qt.NoModifier, """b""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 48.087885 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x42, Qt.NoModifier, """b""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 48.16385 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x49, Qt.NoModifier, """i""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 48.554333 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 48.630069 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x49, Qt.NoModifier, """i""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 48.703341 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 48.77282 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 48.849526 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x52, Qt.NoModifier, """r""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 48.920707 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x41, Qt.NoModifier, """a""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 48.992838 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x59, Qt.NoModifier, """y""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 49.069054 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x52, Qt.NoModifier, """r""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 49.141062 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x59, Qt.NoModifier, """y""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 49.211961 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x2e, Qt.NoModifier, """.""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 49.288042 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x2e, Qt.NoModifier, """.""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 49.360557 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 49.441056 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 49.516359 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x59, Qt.NoModifier, """y""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 49.762765 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x59, Qt.NoModifier, """y""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 49.83494 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000003, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.fileNameEdit', event , 50.466332 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000003, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 50.550352 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000003, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 50.622771 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000003, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 50.694763 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 51.547256 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x4e, Qt.NoModifier, """n""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 51.619973 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x50, Qt.NoModifier, """p""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 52.097439 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x50, Qt.NoModifier, """p""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 52.169123 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x59, Qt.NoModifier, """y""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 52.369887 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x59, Qt.NoModifier, """y""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 52.460471 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000004, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 52.555796 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000004, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_0_lane_-1.QFileDialog.fileNameEdit', event , 52.662065 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(66, 74), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(386, 131), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DatasetDetailedInfoTableView_0', event , 53.804989 )

    ########################
    player.display_comment("""Select object features""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(272, 7), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(272, 7), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 54.656801 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(223, 9), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(229, 281), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QAbstractButton_1', event , 55.57177 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(223, 9), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(229, 281), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QAbstractButton_1', event , 55.651692 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(214, 16), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(229, 264), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.containingWidget.selectFeaturesButton', event , 60.122946 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(214, 16), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(229, 264), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.containingWidget.selectFeaturesButton', event , 60.308773 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(283, 7), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(102, 378), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'FeatureSelectionDialog.treeWidget.QHeaderView_0.qt_scrollarea_viewport', event , 61.259462 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(50, 88), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(-131, 482), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'FeatureSelectionDialog.treeWidget.qt_scrollarea_viewport', event , 62.723249 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(50, 88), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(-131, 482), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'FeatureSelectionDialog.treeWidget.qt_scrollarea_viewport', event , 62.813988 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(48, 216), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(-133, 610), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'FeatureSelectionDialog.treeWidget.qt_scrollarea_viewport', event , 64.80822 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(48, 216), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(-133, 610), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'FeatureSelectionDialog.treeWidget.qt_scrollarea_viewport', event , 64.926264 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(47, 18), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(190, 811), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'FeatureSelectionDialog.buttonBox.QPushButton_0', event , 66.678869 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(47, 18), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(190, 811), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'FeatureSelectionDialog.buttonBox.QPushButton_0', event , 66.774089 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(178, 73), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(193, 195), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.containingWidget.label', event , 69.734898 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(189, 51), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(204, 173), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.containingWidget.label', event , 69.838585 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(190, 49), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(205, 171), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.containingWidget.label', event , 69.931056 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(191, 49), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(206, 171), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.containingWidget.label', event , 70.035642 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(180, 41), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(195, 163), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.containingWidget.label', event , 71.223703 )

    ########################
    player.display_comment("""Open Object Classification page""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(332, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(332, 0), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 72.321667 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(236, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(251, 134), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.containingWidget.label', event , 72.437495 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(191, 113), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(206, 235), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_2.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.containingWidget.label', event , 72.531928 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(166, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(172, 313), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QAbstractButton_2', event , 73.432186 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(166, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(172, 313), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QAbstractButton_2', event , 73.51957 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(293, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(293, 0), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 78.862149 )

    ########################
    player.display_comment("""Add two label classes""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(352, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(352, 0), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 83.800253 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(164, 2), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(179, 214), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.label', event , 87.513626 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(160, 14), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(175, 226), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.label', event , 87.643064 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(254, 10), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(269, 240), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.QLabel_0', event , 91.289898 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(254, 70), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(269, 240), -1560, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.QLabel_0', event , 91.407503 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(237, 14), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(252, 255), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.AddLabelButton', event , 92.732739 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(237, 14), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(252, 255), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.AddLabelButton', event , 92.848716 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(237, 14), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(252, 255), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.AddLabelButton', event , 94.659924 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(237, 14), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(252, 255), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.AddLabelButton', event , 94.788803 )

    ########################
    player.display_comment("""Hide binary image (show raw data underneath)""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(334, 8), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(334, 8), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 97.427577 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(76, 8), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(196, 278), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.checkShowPredictions', event , 97.555486 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(9, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(21, 629), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_3_lane_0.layerWidget.qt_scrollarea_viewport.LayerItemWidget_Binary image.ToggleEye_0', event , 99.581691 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(9, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(21, 629), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_3_lane_0.layerWidget.qt_scrollarea_viewport.LayerItemWidget_Binary image.ToggleEye_0', event , 99.758531 )

    ########################
    player.display_comment("""Label some objects.  The two classes in this data are: (1) big light cubes and small dark ones, and (2) small light cubes and big dark ones.""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(360, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(360, 0), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 102.160007 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(48, 34), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(359, 61), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 102.294204 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(96, 117), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(407, 144), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 102.423862 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(103, 122), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(414, 149), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 102.56849 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(146, 143), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(457, 170), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 102.689649 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(156, 150), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(467, 177), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 102.838189 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(158, 151), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(469, 178), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 102.962191 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000021, (Qt.ControlModifier), """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_3_lane_0.layerWidget', event , 103.099856 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000021, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_3_lane_0.layerWidget', event , 103.207 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000021, (Qt.ControlModifier), """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_3_lane_0.layerWidget', event , 103.663079 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(158, 151), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(469, 178), 120, Qt.NoButton, (Qt.ControlModifier), 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 104.124521 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(158, 151), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(469, 178), 2640, Qt.NoButton, (Qt.ControlModifier), 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 104.27255 )

    event = PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x1000021, Qt.NoModifier, """""", False, 1)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.viewerControlStack.viewerControls_applet_3_lane_0.layerWidget', event , 106.336498 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(370, 7), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(370, 7), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 107.455126 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(59, 14), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(76, 160), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.QTableView_0.qt_scrollarea_viewport', event , 108.031675 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(58, 13), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(75, 159), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.QTableView_0.qt_scrollarea_viewport', event , 108.14035 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(58, 13), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(75, 159), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.QTableView_0.qt_scrollarea_viewport', event , 108.27054 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(0, 111), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(309, 136), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0', event , 108.869721 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(72, 112), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(383, 139), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 108.992379 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(92, 115), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(403, 142), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 109.139349 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(96, 114), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(407, 141), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 109.262864 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(107, 111), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(418, 138), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 109.410261 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(108, 110), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(419, 137), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 109.69088 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(109, 110), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(420, 137), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 110.240456 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(109, 110), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(420, 137), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 110.527128 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(109, 110), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(420, 137), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 111.099207 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(108, 110), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(419, 137), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 111.545722 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(84, 115), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(395, 142), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 111.692669 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(59, 46), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(76, 192), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.QTableView_0.qt_scrollarea_viewport', event , 112.400666 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(59, 46), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(76, 192), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.QTableView_0.qt_scrollarea_viewport', event , 112.547438 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(20, 124), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(331, 151), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 113.042483 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(141, 121), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(452, 148), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 113.196013 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(185, 124), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(496, 151), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 113.322592 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(195, 119), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(506, 146), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 113.471438 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(192, 115), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(503, 142), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 113.595862 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(188, 113), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(499, 140), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 113.745037 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(185, 113), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(496, 140), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 113.86951 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(228, 111), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(539, 138), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 114.020855 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(237, 110), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(548, 137), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 114.144537 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(248, 111), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(559, 138), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 114.29856 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(251, 111), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(562, 138), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 114.421144 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(250, 111), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(561, 138), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 114.634633 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(250, 110), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(561, 137), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 114.89345 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(249, 110), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(560, 137), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 115.04163 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(249, 110), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(560, 137), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 115.161412 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(249, 110), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(560, 137), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 115.549926 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(248, 114), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(559, 141), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 115.895676 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(248, 115), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(559, 142), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 116.024188 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(244, 115), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(555, 142), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 116.459578 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(119, 132), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(430, 159), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 116.608191 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(59, 18), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(76, 164), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.QTableView_0.qt_scrollarea_viewport', event , 117.479143 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(59, 18), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(76, 164), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.QTableView_0.qt_scrollarea_viewport', event , 117.631615 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(1, 143), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(312, 170), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 118.016143 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(103, 146), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(414, 173), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 118.146189 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(131, 150), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(442, 177), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 118.296905 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(131, 150), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(442, 177), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 120.596162 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(131, 150), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(442, 177), 600, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 120.756694 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(131, 150), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(442, 177), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 121.904227 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(131, 150), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(442, 177), 480, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 122.06303 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(131, 148), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(442, 175), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 123.403256 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(129, 138), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(440, 165), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 123.54786 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(128, 138), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(439, 165), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 123.682927 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(121, 145), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(432, 172), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 123.827638 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(121, 148), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(432, 175), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 123.962884 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(145, 150), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(456, 177), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 124.10909 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(191, 149), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(502, 176), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 124.241631 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(217, 149), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(528, 176), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 124.392555 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(220, 149), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(531, 176), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 124.526355 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(220, 149), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(531, 176), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 126.800443 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(220, 149), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(531, 176), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 127.062544 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(218, 149), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(529, 176), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 127.596076 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(62, 148), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(373, 175), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 127.728666 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(34, 47), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(51, 193), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.QTableView_0.qt_scrollarea_viewport', event , 128.33937 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(34, 47), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(51, 193), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.QTableView_0.qt_scrollarea_viewport', event , 128.491943 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(1, 164), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(312, 191), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 129.011304 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(71, 156), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(382, 183), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 129.160157 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(75, 156), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(386, 183), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 129.290184 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(80, 153), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(391, 180), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 129.438854 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(81, 152), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(392, 179), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 129.571532 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(82, 149), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(393, 176), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 129.723192 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(82, 149), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(393, 176), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 129.847039 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(82, 149), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(393, 176), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 130.006241 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(81, 148), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(392, 175), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 130.987542 )

    ########################
    player.display_comment("""Now live predict!""")
    ########################

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(361, 3), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(361, 3), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.QMenuBar_0', event , 132.006071 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(59, 0), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(179, 270), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.checkShowPredictions', event , 132.554884 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(38, 16), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(158, 286), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.checkShowPredictions', event , 132.694055 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(99, 17), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(114, 287), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.checkInteractive', event , 132.94454 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(81, 16), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(96, 286), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.checkInteractive', event , 133.084442 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(63, 12), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(78, 282), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.checkInteractive', event , 133.201093 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(55, 9), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(70, 279), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.checkInteractive', event , 133.342392 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(55, 9), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(70, 279), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.checkInteractive', event , 133.489002 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(55, 9), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(70, 279), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.checkInteractive', event , 133.63869 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(53, 8), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(68, 278), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.QScrollArea_3.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.checkInteractive', event , 136.079533 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(9, 178), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(320, 205), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 136.671799 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(14, 175), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(325, 202), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 136.802822 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(29, 174), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(340, 201), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 136.95656 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(86, 174), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(397, 201), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 137.089937 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(133, 168), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(444, 195), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 137.243174 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(133, 168), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(444, 195), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 137.940648 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(133, 168), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(444, 195), -840, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 138.105618 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(133, 168), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(444, 195), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 139.327013 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(133, 168), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(444, 195), -360, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 139.494255 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(133, 168), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(444, 195), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 140.46444 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(133, 168), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(444, 195), -600, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 140.699734 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(133, 168), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(444, 195), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 142.300815 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(133, 168), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(444, 195), -1080, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 142.46865 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(133, 168), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(444, 195), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 143.484363 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(133, 168), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(444, 195), -600, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 143.712406 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(133, 168), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(444, 195), -120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 144.792406 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(133, 168), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(444, 195), -960, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 145.023987 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(133, 167), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(444, 194), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 148.146538 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(135, 159), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(446, 186), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 148.321048 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(134, 159), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(445, 186), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 148.478492 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(120, 160), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(431, 187), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 148.629383 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(108, 157), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(419, 184), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 148.798107 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(108, 157), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(419, 184), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 149.889885 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(108, 157), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(419, 184), 360, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 150.066535 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(108, 157), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(419, 184), 240, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 150.38904 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(108, 157), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(419, 184), 120, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 151.399331 )

    event = PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(108, 157), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(419, 184), 240, Qt.NoButton, Qt.NoModifier, 2)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 151.580555 )

    event = PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(102, 157), mainwin.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(413, 184), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    player.post_event( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.QuadView_0.QSplitter_0.splitter1.ImageView2DDockWidget_1.ImageView2D_0.QWidget_0', event , 152.900183 )

    ########################
    player.display_comment("""We\'re done here""")
    ########################

    player.display_comment("SCRIPT COMPLETE")
