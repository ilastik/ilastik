
# Event Recording
# Started at: 2013-07-18 11:04:23.052952

def playback_events(player):
    import PyQt4.QtCore
    from PyQt4.QtCore import Qt, QEvent, QPoint
    import PyQt4.QtGui
    from ilastik.utility.gui.eventRecorder.objectNameUtils import get_named_object
    from ilastik.utility.gui.eventRecorder.eventRecorder import EventPlayer
    from ilastik.shell.gui.startShellGui import shell    

    player.display_comment("SCRIPT STARTING")


    ########################
    player.display_comment("""try to reproduce a bug that recordings are not playable""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.startupPage.frame.CreateList.qt_scrollarea_viewport.scrollAreaWidgetContents' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(404, 91), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(706, 260), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 0.940996 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.startupPage.frame.CreateList.qt_scrollarea_viewport.scrollAreaWidgetContents' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(405, 91), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(707, 260), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 0.970955 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.startupPage.frame.CreateList.qt_scrollarea_viewport.scrollAreaWidgetContents' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(405, 91), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(707, 260), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 1.001342 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.startupPage.frame.CreateList.qt_scrollarea_viewport.scrollAreaWidgetContents.child_2_QToolButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(127, 16), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(438, 231), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 1.436962 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.startupPage.frame.CreateList.qt_scrollarea_viewport.scrollAreaWidgetContents.child_2_QToolButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(127, 16), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(438, 231), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 1.505038 )

    obj = get_named_object( 'MainWindow.QFileDialog.buttonBox.child_1_QPushButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(48, 17), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(773, 445), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 2.7219 )

    obj = get_named_object( 'MainWindow.QFileDialog.buttonBox.child_1_QPushButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(48, 17), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(773, 445), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 2.809105 )

    ########################
    player.display_comment("""add 2d then 3d""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.viewerStack.page_2' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(117, 365), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(435, 524), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 5.253302 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.viewerStack.page_2' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(118, 365), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(436, 524), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 5.271689 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.viewerStack.page_2' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(118, 365), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(436, 524), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 5.313927 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.appendButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(62, 9), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(382, 129), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 5.954229 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(63, -24), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(383, 129), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 6.073768 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(63, -24), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(383, 129), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 6.130629 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(70, -1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(390, 152), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 6.508479 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(68, 0), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(388, 153), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 6.528562 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(67, 0), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(387, 153), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 6.544243 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(66, 0), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(386, 153), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 6.560441 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(64, 0), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(384, 153), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 6.577374 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(64, 1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(384, 154), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 6.593638 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(63, 2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(383, 155), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 6.678299 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(62, 4), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(382, 157), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 6.695558 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(60, 9), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(380, 162), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 6.722903 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(59, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(379, 164), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 6.73936 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(59, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(379, 165), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 6.756577 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(58, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(378, 165), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 6.799354 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(58, 13), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(378, 166), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 6.815946 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(58, 13), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(378, 166), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 6.849584 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(58, 13), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(378, 166), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 6.920676 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(84, 40), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(380, 164), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 8.063414 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(84, 40), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(380, 164), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 8.147481 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonDblClick, PyQt4.QtCore.QPoint(84, 40), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(380, 164), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 8.178869 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.appendButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(80, 9), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(400, 129), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 9.763357 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(81, -24), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(401, 129), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 9.841262 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(81, -24), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(401, 129), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 9.874379 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(81, -1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(401, 152), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 10.344031 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(81, 0), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(401, 153), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 10.368673 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(80, 3), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(400, 156), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 10.390335 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(80, 5), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(400, 158), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 10.414937 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(76, 7), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(396, 160), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 10.446961 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(70, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(390, 164), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 10.473016 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(69, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(389, 165), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 10.496865 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(69, 13), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(389, 166), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 10.526602 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(69, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(389, 168), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 10.54369 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(70, 17), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(390, 170), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 10.558069 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(71, 17), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(391, 170), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 10.576551 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(71, 17), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(391, 170), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 10.600987 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(72, 17), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(392, 170), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 10.661895 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(72, 17), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(392, 170), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 10.687526 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(112, 55), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(408, 179), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 11.776722 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(112, 55), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(408, 179), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 11.864831 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonDblClick, PyQt4.QtCore.QPoint(113, 55), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(409, 179), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 11.8991 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.child_5_QMessageBox.qt_msgbox_buttonbox.child_1_QPushButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(11, 26), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(472, 354), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 13.342442 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.child_5_QMessageBox.qt_msgbox_buttonbox.child_1_QPushButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(11, 26), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(472, 354), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 13.408912 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.DatasetInfoEditorWidget_Role_0.widget.okButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(60, 7), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(742, 445), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 14.764363 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.DatasetInfoEditorWidget_Role_0.widget.okButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(61, 7), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(743, 445), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 14.840747 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.DatasetInfoEditorWidget_Role_0.widget.okButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(61, 7), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(743, 445), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 14.852132 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.DatasetInfoEditorWidget_Role_0.child_1_QMessageBox.qt_msgbox_buttonbox.child_1_QPushButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(38, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(498, 264), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 15.83787 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.DatasetInfoEditorWidget_Role_0.child_1_QMessageBox.qt_msgbox_buttonbox.child_1_QPushButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(38, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(498, 264), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 15.992942 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.DatasetInfoEditorWidget_Role_0.widget.cancelButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(28, 4), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(627, 442), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 16.979951 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.DatasetInfoEditorWidget_Role_0.widget.cancelButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(29, 4), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(628, 442), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 17.045619 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.DatasetInfoEditorWidget_Role_0.widget.cancelButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(30, 5), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(629, 443), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 17.056099 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.DatasetInfoEditorWidget_Role_0.widget.cancelButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(30, 5), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(629, 443), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 17.071264 )

    ########################
    player.display_comment("""and save is""")
    ########################

    player.display_comment("SCRIPT COMPLETE")
