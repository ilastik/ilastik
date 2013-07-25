
# Event Recording
# Started at: 2013-07-18 10:54:47.389254

def playback_events(player):
    import PyQt4.QtCore
    from PyQt4.QtCore import Qt, QEvent, QPoint
    import PyQt4.QtGui
    from ilastik.utility.gui.eventRecorder.objectNameUtils import get_named_object
    from ilastik.utility.gui.eventRecorder.eventRecorder import EventPlayer
    from ilastik.shell.gui.startShellGui import shell    

    player.display_comment("SCRIPT STARTING")


    ########################
    player.display_comment("""within this test we add features and then redo the feature selection""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.startupPage.frame.CreateList.qt_scrollarea_viewport.scrollAreaWidgetContents.child_2_QToolButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(53, 0), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(364, 215), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 1.023702 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.startupPage.frame.CreateList.qt_scrollarea_viewport.scrollAreaWidgetContents.child_2_QToolButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(54, 0), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(365, 215), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 1.039295 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.startupPage.frame.CreateList.qt_scrollarea_viewport.scrollAreaWidgetContents.child_2_QToolButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(54, 0), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(365, 215), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 1.109327 )

    obj = get_named_object( 'MainWindow.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(78, 108), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(374, 232), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 2.232628 )

    obj = get_named_object( 'MainWindow.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(78, 108), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(374, 232), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 2.336426 )

    obj = get_named_object( 'MainWindow.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonDblClick, PyQt4.QtCore.QPoint(78, 108), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(374, 232), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 2.393656 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.appendButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(50, 22), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(370, 142), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 4.038961 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(50, -11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(370, 142), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 4.163501 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(57, -2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(377, 151), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 4.451882 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(57, 1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(377, 154), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 4.474187 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(64, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(384, 165), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 4.490086 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(66, 13), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(386, 166), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 4.5059 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(66, 14), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(386, 167), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 4.567263 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(68, 14), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(388, 167), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 4.584467 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(69, 14), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(389, 167), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 4.600905 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(70, 14), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(390, 167), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 4.617505 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(70, 14), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(390, 167), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 4.735132 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(70, 14), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(390, 167), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 4.79725 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(91, 35), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(387, 159), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 5.868316 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(91, 35), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(387, 159), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 5.961053 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonDblClick, PyQt4.QtCore.QPoint(91, 35), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(387, 159), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 6.016082 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_5_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(17, 13), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(23, 343), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 8.212255 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_5_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(17, 13), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(23, 343), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 8.461876 )

    ########################
    player.display_comment("""now we select some features""")
    ########################

    ########################
    player.display_comment("""let\'s use 2 features""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_6_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.Form.SelectFeaturesButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(96, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(102, 138), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 15.620379 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_6_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.Form.SelectFeaturesButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(96, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(102, 138), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 15.925399 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.Dialog.featureTableWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(7, 14), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(459, 164), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 17.885637 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.Dialog.featureTableWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(7, 14), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(459, 164), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 17.968693 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.Dialog.featureTableWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(148, 71), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(600, 221), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 18.968312 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.Dialog.featureTableWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(148, 71), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(600, 221), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 19.047014 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.Dialog.ok' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(36, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(676, 414), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 19.933477 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.Dialog.ok' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(36, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(676, 414), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 20.019217 )

    ########################
    player.display_comment("""now we do some live prediction and then we change the selected features""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(197, 511), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(508, 538), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 23.863489 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(197, 511), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(508, 538), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 24.10738 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(92, 18), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(98, 377), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 25.549594 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(92, 18), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(98, 377), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 25.657836 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.AddLabelButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(52, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(67, 271), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 27.317215 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.AddLabelButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(53, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(68, 271), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 27.535308 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.AddLabelButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(53, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(68, 271), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 27.558076 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.AddLabelButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonDblClick, PyQt4.QtCore.QPoint(56, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(71, 275), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 27.818985 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.AddLabelButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(56, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(71, 275), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 27.876144 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(380, 409), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(691, 436), 480, Qt.NoButton, Qt.NoModifier, 2), 28.680513 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(344, 351), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(655, 378), 120, Qt.NoButton, Qt.NoModifier, 2), 28.94626 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(344, 351), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(655, 378), 120, Qt.NoButton, Qt.NoModifier, 2), 28.970856 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(344, 351), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(655, 378), 120, Qt.NoButton, Qt.NoModifier, 2), 28.997044 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(355, 286), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(666, 313), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 29.28398 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(354, 287), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(665, 314), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 29.467667 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(343, 302), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(654, 329), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 29.490994 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(342, 303), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(653, 330), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 29.514684 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(341, 305), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(652, 332), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 29.59178 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(332, 316), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(643, 343), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 29.631225 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(330, 318), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(641, 345), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 29.651688 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(327, 322), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(638, 349), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 29.745067 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(317, 331), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(628, 358), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 29.768608 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(314, 334), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(625, 361), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 29.793541 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(312, 336), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(623, 363), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 29.896198 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(311, 336), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(622, 363), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 29.923927 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(305, 337), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(616, 364), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 29.945831 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(305, 337), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(616, 364), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 30.031414 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.child_3_QTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(45, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(62, 165), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 30.991132 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.child_3_QTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(45, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(62, 165), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 31.019017 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(369, 319), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(680, 346), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 31.731 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(366, 320), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(677, 347), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 31.771981 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(364, 322), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(675, 349), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 31.936737 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(351, 340), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(662, 367), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 31.969529 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(349, 343), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(660, 370), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 31.994217 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(346, 347), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(657, 374), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 32.078876 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(326, 362), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(637, 389), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 32.115825 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(323, 363), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(634, 390), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 32.141451 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(320, 364), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(631, 391), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 32.239691 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(319, 364), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(630, 391), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 32.264308 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(319, 364), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(630, 391), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 32.287645 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.liveUpdateButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(61, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(76, 330), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 33.142453 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.liveUpdateButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(61, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(76, 330), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 33.367422 )

    ########################
    player.display_comment("""ok,live update is done for the first time
now we re-change the features""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(98, 387), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(409, 414), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 35.739336 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(99, 387), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(410, 414), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 35.781604 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(99, 387), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(410, 414), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 35.813512 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_5_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(37, 13), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(43, 97), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 36.498154 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_5_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(37, 13), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(43, 97), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 36.593643 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_6_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.Form.SelectFeaturesButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(215, 21), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(221, 149), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 37.633054 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_6_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.Form.SelectFeaturesButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(215, 20), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(221, 148), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 37.890738 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_6_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.Form.SelectFeaturesButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(215, 20), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(221, 148), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 37.903978 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.Dialog.featureTableWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(155, 66), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(607, 216), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 40.022856 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.Dialog.featureTableWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(157, 67), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(609, 217), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 40.036061 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.Dialog.featureTableWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(157, 67), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(609, 217), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 40.0536 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.Dialog.featureTableWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(159, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(611, 162), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 40.996699 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.Dialog.featureTableWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(159, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(611, 162), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 41.063049 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.Dialog.featureTableWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(168, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(620, 161), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 42.526636 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.Dialog.featureTableWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(164, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(616, 162), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 42.549688 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.Dialog.featureTableWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(164, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(616, 162), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 42.569481 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.Dialog.featureTableWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(49, 66), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(501, 216), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 43.334917 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.Dialog.featureTableWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(47, 63), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(499, 213), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 43.352803 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.Dialog.featureTableWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(47, 63), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(499, 213), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 43.375509 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.Dialog.featureTableWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(28, 39), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(480, 189), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 43.919874 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.Dialog.featureTableWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(28, 39), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(480, 189), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 43.996686 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.Dialog.ok' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(21, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(661, 415), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 44.810602 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.Dialog.ok' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(22, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(662, 415), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 44.887577 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.Dialog.ok' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(22, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(662, 415), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 44.910801 )

    ########################
    player.display_comment("""and now we do some live updates again""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_6_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.Form' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(257, 154), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(263, 267), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 48.25445 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_6_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.Form' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(255, 154), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(261, 267), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 48.34932 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_6_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.Form' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(254, 155), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(260, 268), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 48.361439 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_6_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.Form' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(254, 155), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(260, 268), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 48.373353 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(59, 9), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(65, 368), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 48.74785 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(59, 9), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(65, 368), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 48.823655 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(332, 287), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(643, 314), 120, Qt.NoButton, Qt.NoModifier, 2), 52.469548 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(332, 287), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(643, 314), 120, Qt.NoButton, Qt.NoModifier, 2), 52.504955 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(332, 287), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(643, 314), 120, Qt.NoButton, Qt.NoModifier, 2), 52.527809 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(356, 323), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(667, 350), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 53.224461 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(354, 323), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(665, 350), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 53.323052 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(345, 329), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(656, 356), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 53.351856 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(343, 331), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(654, 358), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 53.375571 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(337, 333), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(648, 360), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 53.455714 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(323, 344), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(634, 371), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 53.480148 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(320, 348), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(631, 375), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 53.508851 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(317, 350), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(628, 377), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 53.585808 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(317, 358), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(628, 385), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 53.607432 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(320, 358), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(631, 385), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 53.629288 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(323, 359), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(634, 386), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 53.70821 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(342, 362), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(653, 389), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 53.732292 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(345, 362), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(656, 389), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 53.752384 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(346, 362), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(657, 389), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 53.83293 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(354, 348), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(665, 375), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 53.854423 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(356, 345), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(667, 372), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 53.876481 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(357, 342), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(668, 369), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 53.963949 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(359, 337), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(670, 364), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 53.993058 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(359, 337), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(670, 364), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 54.014715 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(373, 326), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(684, 353), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 55.11616 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(362, 316), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(673, 343), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 55.153245 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(360, 316), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(671, 343), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 55.175875 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(355, 318), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(666, 345), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 55.270392 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(346, 336), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(657, 363), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 55.302707 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(347, 339), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(658, 366), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 55.328903 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(352, 345), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(663, 372), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 55.411693 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(363, 353), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(674, 380), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 55.43331 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(363, 353), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(674, 380), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 55.525985 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.child_3_QTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(56, 48), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(73, 201), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 56.408968 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.child_3_QTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(56, 48), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(73, 201), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 56.643673 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(355, 304), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(666, 331), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 57.225612 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(335, 304), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(646, 331), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 57.266775 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(328, 304), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(639, 331), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 57.286062 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(318, 304), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(629, 331), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 57.457979 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(306, 304), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(617, 331), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 57.481407 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(306, 304), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(617, 331), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 57.51252 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(354, 297), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(665, 324), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 58.578328 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(347, 310), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(658, 337), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 58.622886 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(343, 317), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(654, 344), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 58.701892 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(330, 335), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(641, 362), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 58.745316 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(328, 338), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(639, 365), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 58.765428 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(324, 343), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(635, 370), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 58.844918 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(321, 348), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(632, 375), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 58.869573 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(320, 349), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(631, 376), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 58.951346 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(320, 349), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(631, 376), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 58.974857 )

    ########################
    player.display_comment("""and we are done""")
    ########################

    player.display_comment("SCRIPT COMPLETE")
