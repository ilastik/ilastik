
# Event Recording
# Started at: 2013-07-18 10:17:56.131239

def playback_events(player):
    import PyQt4.QtCore
    from PyQt4.QtCore import Qt, QEvent, QPoint
    import PyQt4.QtGui
    from ilastik.utility.gui.eventRecorder.objectNameUtils import get_named_object
    from ilastik.utility.gui.eventRecorder.eventRecorder import EventPlayer
    from ilastik.shell.gui.startShellGui import shell    

    player.display_comment("SCRIPT STARTING")


    ########################
    player.display_comment("""try to change xyz to zxy  (last the the recordings did not have this change recorded)""")
    ########################

    ########################
    player.display_comment("""nex pixel classification project""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.startupPage.frame.CreateList.qt_scrollarea_viewport.scrollAreaWidgetContents.child_2_QToolButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(66, 5), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(377, 206), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 1.564968 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.startupPage.frame.CreateList.qt_scrollarea_viewport.scrollAreaWidgetContents.child_2_QToolButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(67, 5), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(378, 206), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 1.603247 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.startupPage.frame.CreateList.qt_scrollarea_viewport.scrollAreaWidgetContents.child_2_QToolButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(67, 6), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(378, 207), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 1.618484 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.startupPage.frame.CreateList.qt_scrollarea_viewport.scrollAreaWidgetContents.child_2_QToolButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(67, 6), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(378, 207), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 1.625088 )

    obj = get_named_object( 'MainWindow.QFileDialog.buttonBox.child_1_QPushButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(48, 13), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(773, 441), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 3.658454 )

    obj = get_named_object( 'MainWindow.QFileDialog.buttonBox.child_1_QPushButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(46, 14), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(771, 442), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 3.710336 )

    obj = get_named_object( 'MainWindow.QFileDialog.buttonBox.child_1_QPushButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(46, 14), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(771, 442), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 3.721305 )

    ########################
    player.display_comment("""add files
""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.appendButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(79, 14), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(399, 134), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 5.990654 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(81, -19), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(401, 134), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 6.057771 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(81, -19), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(401, 134), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 6.082684 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(65, -4), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(385, 149), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 6.13124 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(59, 2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(379, 155), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 6.150574 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(-424, 487), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(-104, 640), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 6.657798 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.appendButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(43, 28), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(363, 148), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 7.373822 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(44, -4), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(364, 149), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 7.484779 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(44, -4), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(364, 149), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 7.539729 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(54, -1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(374, 152), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 7.91874 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(55, 1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(375, 154), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 7.937706 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(60, 5), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(380, 158), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 7.952194 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(62, 5), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(382, 158), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 7.967759 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(62, 6), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(382, 159), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 8.025614 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(64, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(384, 161), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 8.041646 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(64, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(384, 164), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 8.058804 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(66, 13), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(386, 166), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 8.075029 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(67, 16), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(387, 169), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 8.09287 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(68, 17), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(388, 170), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 8.10825 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(69, 17), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(389, 170), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 8.12499 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(69, 17), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(389, 170), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 8.368972 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(69, 17), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(389, 170), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 8.439619 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(109, 59), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(405, 183), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 9.659496 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(109, 59), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(405, 183), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 9.766871 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(107, 60), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(403, 184), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 10.538372 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(107, 60), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(403, 184), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 10.633701 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonDblClick, PyQt4.QtCore.QPoint(107, 60), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(403, 184), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 10.714219 )

    ########################
    player.display_comment("""now we want to swap some axis""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(82, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(422, 97), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 14.416922 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(82, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(422, 97), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 14.634133 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonDblClick, PyQt4.QtCore.QPoint(82, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(422, 97), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 14.650864 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.datasetDetailTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(82, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(422, 97), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 14.754265 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.DatasetInfoEditorWidget_Role_0.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(82, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(407, 191), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 16.10381 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.DatasetInfoEditorWidget_Role_0.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(80, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(405, 191), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 16.14818 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.DatasetInfoEditorWidget_Role_0.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(70, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(395, 191), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 16.163955 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.DatasetInfoEditorWidget_Role_0.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(61, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(386, 189), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 16.180218 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.DatasetInfoEditorWidget_Role_0.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(13, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(338, 189), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 16.197042 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.DatasetInfoEditorWidget_Role_0.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(-29, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(296, 187), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 16.211403 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.DatasetInfoEditorWidget_Role_0.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(-48, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(277, 187), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 16.228661 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.DatasetInfoEditorWidget_Role_0.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(-95, 2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(230, 181), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 16.245238 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.DatasetInfoEditorWidget_Role_0.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(-115, 0), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(210, 179), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 16.265569 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.DatasetInfoEditorWidget_Role_0.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(-120, -1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(205, 178), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 16.321756 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.DatasetInfoEditorWidget_Role_0.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(-121, -1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(204, 178), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 16.337794 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.DatasetInfoEditorWidget_Role_0.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(-121, -2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(204, 177), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 16.408201 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.DatasetInfoEditorWidget_Role_0.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(-120, -2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(205, 177), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 16.476446 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.DatasetInfoEditorWidget_Role_0.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(-120, -3), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(205, 176), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 16.495014 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.DatasetInfoEditorWidget_Role_0.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(-120, -3), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(205, 176), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 16.51117 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.DatasetInfoEditorWidget_Role_0.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x5a, Qt.NoModifier, """z""", False, 1), 18.737175 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.DatasetInfoEditorWidget_Role_0.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x5a, Qt.NoModifier, """z""", False, 1), 18.80523 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.DatasetInfoEditorWidget_Role_0.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x58, Qt.NoModifier, """x""", False, 1), 19.400875 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.DatasetInfoEditorWidget_Role_0.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x58, Qt.NoModifier, """x""", False, 1), 19.494048 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.DatasetInfoEditorWidget_Role_0.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x59, Qt.NoModifier, """y""", False, 1), 19.66557 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.DatasetInfoEditorWidget_Role_0.widget.axesEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyRelease, 0x59, Qt.NoModifier, """y""", False, 1), 19.733799 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.DatasetInfoEditorWidget_Role_0.widget.okButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(43, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(725, 449), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 22.182483 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.DatasetInfoEditorWidget_Role_0.widget.okButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(43, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(725, 449), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 22.286932 )

    ########################
    player.display_comment("""now the axis are changed !! (visible while recording maybe not in playback)""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(277, 260), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(597, 421), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 24.367214 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(277, 260), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(597, 421), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 24.615648 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(275, 261), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(595, 422), 240, Qt.NoButton, Qt.NoModifier, 2), 24.794804 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(275, 261), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(595, 422), 120, Qt.NoButton, Qt.NoModifier, 2), 24.902226 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(275, 262), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(595, 423), 120, Qt.NoButton, Qt.NoModifier, 2), 24.945213 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(416, 257), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(736, 418), -120, Qt.NoButton, Qt.NoModifier, 2), 25.449534 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(416, 257), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(736, 418), -120, Qt.NoButton, Qt.NoModifier, 2), 25.542154 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(416, 257), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(736, 418), -360, Qt.NoButton, Qt.NoModifier, 2), 25.55921 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(346, 296), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(666, 457), -120, Qt.NoButton, Qt.NoModifier, 2), 25.969116 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(346, 296), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(666, 457), -120, Qt.NoButton, Qt.NoModifier, 2), 26.06147 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(346, 296), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(666, 457), -480, Qt.NoButton, Qt.NoModifier, 2), 26.082467 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(345, 296), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(665, 457), -120, Qt.NoButton, Qt.NoModifier, 2), 26.426261 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(345, 296), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(665, 457), -120, Qt.NoButton, Qt.NoModifier, 2), 26.508943 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(345, 296), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(665, 457), -480, Qt.NoButton, Qt.NoModifier, 2), 26.522947 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(345, 297), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(665, 458), -120, Qt.NoButton, Qt.NoModifier, 2), 26.880517 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(345, 297), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(665, 458), -120, Qt.NoButton, Qt.NoModifier, 2), 26.96224 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(345, 297), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(665, 458), -240, Qt.NoButton, Qt.NoModifier, 2), 26.987829 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(345, 297), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(665, 458), 120, Qt.NoButton, Qt.NoModifier, 2), 27.528918 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(345, 297), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(665, 458), 120, Qt.NoButton, Qt.NoModifier, 2), 27.622223 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(345, 297), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(665, 458), 600, Qt.NoButton, Qt.NoModifier, 2), 27.637102 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(345, 297), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(665, 458), 120, Qt.NoButton, Qt.NoModifier, 2), 27.8781 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(345, 297), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(665, 458), 360, Qt.NoButton, Qt.NoModifier, 2), 27.967144 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(345, 297), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(665, 458), 240, Qt.NoButton, Qt.NoModifier, 2), 27.983269 )

    ########################
    player.display_comment("""click a bit around and see if axis changes are visible is all modes (like feature selection)""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_4_QScrollArea.qt_scrollarea_viewport.child_0_QStackedWidget.Form.label' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(231, 216), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(246, 309), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 30.848124 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_4_QScrollArea.qt_scrollarea_viewport.child_0_QStackedWidget.Form.label' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(231, 216), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(246, 309), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 31.067126 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_5_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(191, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(197, 342), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 31.289586 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_5_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(190, 14), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(196, 344), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 31.311601 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_5_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(191, 14), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(197, 344), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 31.333517 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_5_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(192, 14), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(198, 344), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 31.344017 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_5_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(193, 13), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(199, 343), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 31.350462 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_5_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(193, 13), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(199, 343), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 31.381056 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(65, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(71, 370), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 34.184769 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(65, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(71, 370), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 34.283359 )

    ########################
    player.display_comment("""seems ok""")
    ########################

    ########################
    player.display_comment("""save the test =)""")
    ########################

    player.display_comment("SCRIPT COMPLETE")
