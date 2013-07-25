
# Event Recording
# Started at: 2013-07-18 10:52:43.512931

def playback_events(player):
    import PyQt4.QtCore
    from PyQt4.QtCore import Qt, QEvent, QPoint
    import PyQt4.QtGui
    from ilastik.utility.gui.eventRecorder.objectNameUtils import get_named_object
    from ilastik.utility.gui.eventRecorder.eventRecorder import EventPlayer
    from ilastik.shell.gui.startShellGui import shell    

    player.display_comment("SCRIPT STARTING")


    ########################
    player.display_comment("""within this test i\'ll create and delete labels""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.startupPage' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(488, 669), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(493, 694), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 0.779318 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.startupPage' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(488, 669), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(493, 694), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 0.85308 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.startupPage.frame.CreateList.qt_scrollarea_viewport.scrollAreaWidgetContents.child_2_QToolButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(79, 6), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(390, 221), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 1.746246 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.startupPage.frame.CreateList.qt_scrollarea_viewport.scrollAreaWidgetContents.child_2_QToolButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(79, 6), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(390, 221), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 1.853011 )

    obj = get_named_object( 'MainWindow.QFileDialog.buttonBox.child_1_QPushButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(46, 6), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(771, 434), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 3.056423 )

    obj = get_named_object( 'MainWindow.QFileDialog.buttonBox.child_1_QPushButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(46, 6), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(771, 434), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 3.159385 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.appendButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(68, 14), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(388, 134), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 4.505026 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(68, -19), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(388, 134), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 4.613187 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(69, -1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(389, 152), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 4.979589 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(69, 0), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(389, 153), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 5.002315 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(69, 5), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(389, 158), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 5.020092 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(69, 7), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(389, 160), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 5.038442 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(69, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(389, 161), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 5.063084 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(69, 9), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(389, 162), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 5.079607 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(69, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(389, 163), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 5.097215 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(69, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(389, 165), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 5.115799 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(65, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(385, 168), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 5.133394 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(62, 18), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(382, 171), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 5.15047 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(62, 19), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(382, 172), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 5.167057 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(62, 19), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(382, 172), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 5.197791 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(62, 19), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(382, 172), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 5.27615 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(101, 31), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(397, 155), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 6.270934 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(101, 31), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(397, 155), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 6.357272 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(96, 43), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(392, 167), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 6.663627 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(96, 43), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(392, 167), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 6.759612 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonDblClick, PyQt4.QtCore.QPoint(96, 43), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(392, 167), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 6.824985 )

    ########################
    player.display_comment("""create a few labels """)
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_4_QScrollArea.qt_scrollarea_viewport.child_0_QStackedWidget.Form.instructionLabel' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(28, 124), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(43, 217), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 11.856449 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_4_QScrollArea.qt_scrollarea_viewport.child_0_QStackedWidget.Form.instructionLabel' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(28, 124), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(43, 217), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 12.093608 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(71, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(77, 369), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 13.406114 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(71, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(77, 369), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 13.507417 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.AddLabelButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(68, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(83, 271), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 16.375292 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.AddLabelButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(68, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(83, 271), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 16.620098 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.AddLabelButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(69, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(84, 271), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 17.289154 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.AddLabelButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(69, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(84, 271), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 17.39534 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.AddLabelButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(69, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(84, 271), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 17.769254 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.AddLabelButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(69, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(84, 271), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 17.877287 )

    ########################
    player.display_comment("""now i add them to thre image""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(214, 484), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(525, 511), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 19.278379 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(217, 479), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(528, 506), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 19.325131 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(217, 478), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(528, 505), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 19.602414 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(217, 478), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(528, 505), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 19.623042 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(159, 347), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(470, 374), 360, Qt.NoButton, Qt.NoModifier, 2), 19.658624 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(161, 348), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(472, 375), 120, Qt.NoButton, Qt.NoModifier, 2), 19.71276 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.child_3_QTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(55, 14), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(72, 167), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 20.715459 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.child_3_QTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(55, 14), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(72, 167), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 20.933388 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(335, 287), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(646, 314), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 21.420766 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(332, 290), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(643, 317), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 21.669508 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(310, 309), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(621, 336), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 21.689789 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(308, 310), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(619, 337), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 21.725599 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(305, 311), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(616, 338), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 21.8212 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(309, 311), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(620, 338), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 21.837053 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(316, 310), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(627, 337), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 21.921688 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(348, 296), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(659, 323), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 21.940643 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(351, 295), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(662, 322), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 21.95805 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(352, 295), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(663, 322), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 22.03297 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(351, 299), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(662, 326), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 22.051282 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(349, 302), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(660, 329), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 22.065102 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(340, 306), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(651, 333), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 22.156906 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(322, 314), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(633, 341), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 22.174925 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(322, 312), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(633, 339), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 22.195143 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(342, 303), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(653, 330), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 22.279751 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(358, 305), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(669, 332), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 22.30694 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(335, 318), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(646, 345), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 22.333607 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(305, 334), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(616, 361), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 22.412227 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(311, 326), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(622, 353), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 22.431764 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(318, 324), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(629, 351), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 22.459837 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(324, 323), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(635, 350), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 22.538214 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(318, 336), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(629, 363), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 22.561218 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(317, 335), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(628, 362), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 22.63875 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(333, 323), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(644, 350), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 22.673337 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(334, 323), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(645, 350), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 22.695805 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(330, 328), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(641, 355), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 22.778589 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(312, 343), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(623, 370), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 22.801302 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(313, 341), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(624, 368), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 22.871835 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(317, 334), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(628, 361), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 22.90251 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(317, 334), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(628, 361), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 22.925659 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.child_3_QTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(52, 50), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(69, 203), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 23.826871 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.child_3_QTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(52, 50), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(69, 203), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 24.061157 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(389, 373), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(700, 400), 120, Qt.NoButton, Qt.NoModifier, 2), 24.572427 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(389, 373), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(700, 400), 360, Qt.NoButton, Qt.NoModifier, 2), 24.588881 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(354, 364), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(665, 391), 120, Qt.NoButton, Qt.NoModifier, 2), 24.828356 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(354, 364), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(665, 391), 120, Qt.NoButton, Qt.NoModifier, 2), 24.858272 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(354, 364), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(665, 391), 120, Qt.NoButton, Qt.NoModifier, 2), 24.887851 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(354, 364), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(665, 391), 120, Qt.NoButton, Qt.NoModifier, 2), 24.912516 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(357, 310), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(668, 337), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 25.333405 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(345, 318), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(656, 345), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 25.370931 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(343, 322), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(654, 349), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 25.544496 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(331, 351), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(642, 378), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 25.586191 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(325, 354), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(636, 381), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 25.615412 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(324, 354), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(635, 381), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 25.691302 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(369, 334), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(680, 361), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 25.712848 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(377, 332), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(688, 359), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 25.739794 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(375, 333), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(686, 360), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 25.809333 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(338, 357), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(649, 384), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 25.830827 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(340, 357), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(651, 384), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 25.852436 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(397, 323), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(708, 350), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 25.942926 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(363, 332), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(674, 359), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 25.987021 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(356, 334), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(667, 361), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 26.003777 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(358, 330), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(669, 357), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 26.089585 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(364, 318), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(675, 345), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 26.111542 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(359, 321), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(670, 348), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 26.134132 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(357, 322), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(668, 349), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 26.198767 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(359, 319), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(670, 346), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 26.220799 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(363, 314), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(674, 341), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 26.302367 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(356, 319), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(667, 346), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 26.333339 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(355, 320), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(666, 347), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 26.357691 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(357, 320), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(668, 347), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 26.439496 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(364, 319), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(675, 346), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 26.466729 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(362, 320), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(673, 347), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 26.519303 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(355, 324), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(666, 351), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 26.555532 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(355, 325), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(666, 352), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 26.586255 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(357, 320), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(668, 347), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 26.671014 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(383, 306), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(694, 333), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 26.702047 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(381, 309), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(692, 336), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 26.724971 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(376, 315), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(687, 342), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 26.819316 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(376, 318), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(687, 345), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 26.845237 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(373, 317), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(684, 344), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 26.933619 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(373, 317), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(684, 344), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 26.9565 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.child_3_QTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(28, 69), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(45, 222), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 28.064731 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.child_3_QTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(31, 70), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(48, 223), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 28.296714 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.child_3_QTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(31, 70), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(48, 223), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 28.317683 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(322, 370), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(633, 397), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 29.076344 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(314, 367), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(625, 394), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 29.110923 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(310, 365), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(621, 392), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 29.135117 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(310, 351), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(621, 378), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 29.307398 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(300, 364), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(611, 391), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 29.329277 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(298, 364), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(609, 391), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 29.409418 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(292, 344), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(603, 371), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 29.426251 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(299, 340), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(610, 367), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 29.447338 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(305, 340), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(616, 367), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 29.536456 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(315, 360), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(626, 387), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 29.559444 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(311, 361), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(622, 388), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 29.578356 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(308, 361), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(619, 388), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 29.653057 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(311, 346), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(622, 373), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 29.673869 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(315, 345), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(626, 372), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 29.691914 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(317, 348), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(628, 375), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 29.765158 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(314, 365), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(625, 392), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 29.784033 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(310, 366), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(621, 393), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 29.804784 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(306, 364), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(617, 391), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 29.880236 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(311, 354), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(622, 381), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 29.897287 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(314, 354), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(625, 381), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 29.919482 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(319, 361), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(630, 388), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 30.011627 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(308, 376), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(619, 403), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 30.035505 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(305, 372), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(616, 399), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 30.051957 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(305, 364), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(616, 391), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 30.148636 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(317, 363), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(628, 390), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 30.178043 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(316, 371), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(627, 398), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 30.19867 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(308, 379), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(619, 406), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 30.278335 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(301, 369), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(612, 396), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 30.308965 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(306, 365), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(617, 392), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 30.326172 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(314, 362), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(625, 389), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 30.405464 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(326, 380), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(637, 407), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 30.428984 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(326, 384), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(637, 411), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 30.450845 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(321, 393), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(632, 420), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 30.550417 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(321, 393), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(632, 420), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 30.570109 )

    ########################
    player.display_comment("""now i will delete label 2""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.child_3_QTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(82, 42), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(99, 195), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 31.846212 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.child_3_QTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(82, 42), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(99, 195), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 31.874772 )

    ########################
    player.display_comment("""and re-add a label""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.AddLabelButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(83, 9), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(98, 272), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 36.478867 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.AddLabelButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(83, 9), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(98, 272), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 36.601608 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(356, 325), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(667, 352), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 39.40296 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(357, 326), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(668, 353), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 39.587905 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(362, 340), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(673, 367), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 39.616174 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(362, 342), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(673, 369), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 39.6359 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(362, 346), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(673, 373), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 39.713387 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(361, 357), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(672, 384), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 39.738931 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(359, 360), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(670, 387), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 39.760501 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(354, 366), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(665, 393), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 39.853291 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(330, 372), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(641, 399), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 39.888151 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(326, 372), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(637, 399), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 39.913218 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(324, 371), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(635, 398), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 39.995582 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(336, 351), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(647, 378), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 40.016186 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(352, 340), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(663, 367), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 40.040919 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(368, 328), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(679, 355), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 40.117802 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(372, 326), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(683, 353), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 40.148409 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(372, 325), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(683, 352), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 40.228023 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(366, 323), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(677, 350), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 40.26308 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(364, 323), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(675, 350), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 40.286678 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(361, 323), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(672, 350), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 40.364681 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(350, 329), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(661, 356), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 40.385876 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(348, 331), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(659, 358), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 40.407763 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(348, 333), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(659, 360), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 40.482561 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(363, 342), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(674, 369), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 40.513442 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(366, 344), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(677, 371), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 40.530438 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(366, 346), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(677, 373), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 40.608272 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(353, 366), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(664, 393), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 40.635747 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(349, 368), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(660, 395), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 40.658138 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(349, 369), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(660, 396), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 40.733643 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(348, 352), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(659, 379), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 40.757007 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(351, 347), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(662, 374), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 40.778007 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(360, 339), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(671, 366), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 40.865923 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(368, 334), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(679, 361), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 40.891885 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(364, 334), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(675, 361), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 40.97716 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(359, 334), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(670, 361), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 41.008079 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(359, 334), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(670, 361), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 41.030139 )

    ########################
    player.display_comment("""and we are done!""")
    ########################

    player.display_comment("SCRIPT COMPLETE")
