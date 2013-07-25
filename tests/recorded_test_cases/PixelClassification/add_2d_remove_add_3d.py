
# Event Recording
# Started at: 2013-07-18 11:12:27.116823

def playback_events(player):
    import PyQt4.QtCore
    from PyQt4.QtCore import Qt, QEvent, QPoint
    import PyQt4.QtGui
    from ilastik.utility.gui.eventRecorder.objectNameUtils import get_named_object
    from ilastik.utility.gui.eventRecorder.eventRecorder import EventPlayer
    from ilastik.shell.gui.startShellGui import shell    

    player.display_comment("SCRIPT STARTING")


    ########################
    player.display_comment("""play around and see if i can crash ilastik""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.startupPage' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(342, 589), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(347, 614), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 0.796855 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.startupPage' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(342, 589), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(347, 614), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 0.862215 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.startupPage.frame.CreateList.qt_scrollarea_viewport.scrollAreaWidgetContents.child_2_QToolButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(107, 5), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(418, 220), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 2.167564 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.startupPage.frame.CreateList.qt_scrollarea_viewport.scrollAreaWidgetContents.child_2_QToolButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(105, 5), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(416, 220), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 2.252938 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.startupPage.frame.CreateList.qt_scrollarea_viewport.scrollAreaWidgetContents.child_2_QToolButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(105, 5), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(416, 220), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 2.260165 )

    obj = get_named_object( 'MainWindow.QFileDialog.buttonBox.child_1_QPushButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(49, 16), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(774, 444), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 3.374266 )

    obj = get_named_object( 'MainWindow.QFileDialog.buttonBox.child_1_QPushButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(49, 17), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(774, 445), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 3.393688 )

    obj = get_named_object( 'MainWindow.QFileDialog.buttonBox.child_1_QPushButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(49, 17), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(774, 445), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 3.439197 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.appendButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(59, 5), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(379, 125), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 4.710221 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(62, -27), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(382, 126), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 4.793696 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(62, -27), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(382, 126), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 4.887418 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(-399, 506), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(-79, 659), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 5.677819 )

    ########################
    player.display_comment("""add 2d file""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.appendButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(75, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(395, 132), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 7.448837 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(76, -21), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(396, 132), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 7.528391 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(76, -21), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(396, 132), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 7.540783 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(107, 0), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(427, 153), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 7.898159 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(107, 1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(427, 154), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 7.912977 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(107, 2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(427, 155), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 7.993229 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(107, 3), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(427, 156), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 8.017741 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(107, 3), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(427, 156), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 8.046469 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(107, 4), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(427, 157), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 8.187225 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(107, 4), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(427, 157), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 8.306831 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(130, 43), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(426, 167), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 9.031594 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(130, 43), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(426, 167), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 9.123345 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonDblClick, PyQt4.QtCore.QPoint(130, 43), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(426, 167), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 9.198152 )

    ########################
    player.display_comment("""now (try to add 3d , should not work)""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.appendButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(84, 17), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(404, 137), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 11.592567 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(84, -16), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(404, 137), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 11.856552 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(83, -2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(403, 151), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 12.050047 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(83, 0), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(403, 153), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 12.075575 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(84, 4), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(404, 157), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 12.090656 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(84, 5), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(404, 158), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 12.11568 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(83, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(403, 161), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 12.148359 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(84, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(404, 164), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 12.16918 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(84, 13), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(404, 166), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 12.193146 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(84, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(404, 168), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 12.218586 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(84, 17), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(404, 170), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 12.243859 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(84, 18), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(404, 171), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 12.294728 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(85, 18), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(405, 171), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 12.309456 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(86, 18), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(406, 171), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 12.358898 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(87, 18), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(407, 171), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 12.391113 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(88, 17), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(408, 170), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 12.405812 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(89, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(409, 168), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 12.421217 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(90, 13), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(410, 166), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 12.440304 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(91, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(411, 165), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 12.466131 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(93, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(413, 165), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 12.492547 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(93, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(413, 165), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 12.509891 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(93, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(413, 165), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 12.566982 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(140, 60), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(436, 184), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 13.428946 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(140, 60), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(436, 184), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 13.52433 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonDblClick, PyQt4.QtCore.QPoint(140, 60), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(436, 184), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 13.598305 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.child_5_QMessageBox.qt_msgbox_buttonbox.child_1_QPushButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(34, 17), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(495, 345), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 15.120073 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.child_5_QMessageBox.qt_msgbox_buttonbox.child_1_QPushButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(34, 17), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(495, 345), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 15.220553 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.DatasetInfoEditorWidget_Role_0.widget.okButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(40, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(722, 446), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 16.389265 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.DatasetInfoEditorWidget_Role_0.widget.okButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(43, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(725, 448), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 16.461795 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.DatasetInfoEditorWidget_Role_0.widget.okButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(45, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(727, 449), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 16.471259 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.DatasetInfoEditorWidget_Role_0.widget.okButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(45, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(727, 449), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 16.482994 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.DatasetInfoEditorWidget_Role_0.child_1_QMessageBox.qt_msgbox_buttonbox.child_1_QPushButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(29, 24), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(489, 277), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 17.538175 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.DatasetInfoEditorWidget_Role_0.child_1_QMessageBox.qt_msgbox_buttonbox.child_1_QPushButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(31, 24), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(491, 277), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 17.554607 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.DatasetInfoEditorWidget_Role_0.child_1_QMessageBox.qt_msgbox_buttonbox.child_1_QPushButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(33, 24), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(493, 277), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 17.568402 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.DatasetInfoEditorWidget_Role_0.child_1_QMessageBox.qt_msgbox_buttonbox.child_1_QPushButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(36, 22), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(496, 275), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 17.581952 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.DatasetInfoEditorWidget_Role_0.child_1_QMessageBox.qt_msgbox_buttonbox.child_1_QPushButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(36, 22), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(496, 275), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 17.598065 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.DatasetInfoEditorWidget_Role_0.widget.cancelButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(57, 19), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(656, 457), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 18.406683 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.DatasetInfoEditorWidget_Role_0.widget.cancelButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(58, 19), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(657, 457), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 18.477101 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.DatasetInfoEditorWidget_Role_0.widget.cancelButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(58, 19), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(657, 457), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 18.490879 )

    ########################
    player.display_comment("""no we delete the 2d image
and try to add 3d then (should work)""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(210, 120), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(528, 154), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 21.540308 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(218, 126), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(536, 160), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 21.74976 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(218, 126), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(536, 160), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 21.765164 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.qt_splithandle_' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(201, 1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(519, 156), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 22.621199 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.qt_splithandle_' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(201, 3), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(519, 158), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 22.682744 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.qt_splithandle_' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(203, 9), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(521, 166), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 22.705339 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.qt_splithandle_' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(194, 48), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(512, 213), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 22.874763 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.qt_splithandle_' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(176, 116), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(494, 328), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 22.894659 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.qt_splithandle_' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(176, 1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(494, 328), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 22.916424 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(73, 19), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(413, 101), (Qt.RightButton), (Qt.RightButton), Qt.NoModifier), 23.566386 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QContextMenuEvent(0, PyQt4.QtCore.QPoint(73, 19), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(413, 101), Qt.NoModifier), 23.588292 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(20, 25), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(413, 101), (Qt.RightButton), Qt.NoButton, Qt.NoModifier), 23.767039 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(21, 24), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(414, 100), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 23.793946 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(22, 24), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(415, 100), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 24.008155 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(23, 23), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(416, 99), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 24.036171 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(24, 22), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(417, 98), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 24.074269 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(34, 25), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(427, 101), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 24.104249 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(40, 28), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(433, 104), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 24.133945 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(46, 33), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(439, 109), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 24.168751 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(52, 40), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(445, 116), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 24.191285 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(55, 43), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(448, 119), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 24.225758 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(58, 44), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(451, 120), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 24.25224 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(59, 45), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(452, 121), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 24.275179 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(60, 45), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(453, 121), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 24.360475 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(60, 46), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(453, 122), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 24.387306 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(60, 49), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(453, 125), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 24.408719 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(61, 50), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(454, 126), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 24.432467 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(62, 54), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(455, 130), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 24.457205 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(63, 56), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(456, 132), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 24.480387 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(63, 57), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(456, 133), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 24.506006 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(64, 59), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(457, 135), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 24.529837 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(65, 64), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(458, 140), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 24.553217 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(66, 69), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(459, 145), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 24.578954 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(66, 74), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(459, 150), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 24.615173 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(65, 81), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(458, 157), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 24.639016 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(65, 85), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(458, 161), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 24.661445 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(64, 84), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(457, 160), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 24.986248 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(62, 80), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(455, 156), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 25.008957 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(61, 78), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(454, 154), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 25.025052 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(61, 77), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(454, 153), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 25.041227 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(60, 77), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(453, 153), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 25.057423 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(60, 76), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(453, 152), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 25.079219 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(60, 76), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(453, 152), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 25.194364 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.child_8_QMenu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(60, 76), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(453, 152), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 25.264938 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.appendButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(60, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(380, 307), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 26.516006 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(61, -18), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(381, 307), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 26.64997 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(61, -18), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(381, 307), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 26.707548 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(75, -1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(395, 324), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 27.078686 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(76, 0), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(396, 325), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 27.10613 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(82, 2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(402, 327), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 27.130592 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(82, 3), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(402, 328), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 27.18577 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(83, 5), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(403, 330), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 27.210511 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(84, 6), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(404, 331), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 27.314148 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(84, 7), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(404, 332), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 27.337396 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(86, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(406, 336), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 27.358479 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(87, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(407, 336), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 27.377467 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(87, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(407, 336), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 27.395436 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(87, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(407, 336), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 27.474078 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(117, 60), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(413, 184), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 28.308913 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(117, 60), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(413, 184), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 28.391843 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonDblClick, PyQt4.QtCore.QPoint(117, 60), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(413, 184), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 28.453212 )

    ########################
    player.display_comment("""and we are done""")
    ########################

    player.display_comment("SCRIPT COMPLETE")
