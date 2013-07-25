
# Event Recording
# Started at: 2013-07-18 10:58:55.505755

def playback_events(player):
    import PyQt4.QtCore
    from PyQt4.QtCore import Qt, QEvent, QPoint
    import PyQt4.QtGui
    from ilastik.utility.gui.eventRecorder.objectNameUtils import get_named_object
    from ilastik.utility.gui.eventRecorder.eventRecorder import EventPlayer
    from ilastik.shell.gui.startShellGui import shell    

    player.display_comment("SCRIPT STARTING")


    ########################
    player.display_comment("""add multiple images (we will use the same image over and over)
and do primitve labeling""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.startupPage.frame.CreateList.qt_scrollarea_viewport.scrollAreaWidgetContents.child_2_QToolButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(52, 7), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(363, 222), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 1.060198 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.startupPage.frame.CreateList.qt_scrollarea_viewport.scrollAreaWidgetContents.child_2_QToolButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(52, 6), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(363, 221), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 1.084728 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.startupPage.frame.CreateList.qt_scrollarea_viewport.scrollAreaWidgetContents.child_2_QToolButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(52, 6), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(363, 221), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 1.100379 )

    obj = get_named_object( 'MainWindow.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(75, 112), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(371, 236), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 2.258163 )

    obj = get_named_object( 'MainWindow.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(75, 112), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(371, 236), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 2.343206 )

    obj = get_named_object( 'MainWindow.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonDblClick, PyQt4.QtCore.QPoint(75, 112), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(371, 236), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 2.418409 )

    obj = get_named_object( 'MainWindow.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(75, 112), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(371, 236), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 2.512582 )

    obj = get_named_object( 'MainWindow.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(83, 107), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(379, 231), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 3.050754 )

    obj = get_named_object( 'MainWindow.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(83, 107), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(379, 231), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 3.130207 )

    obj = get_named_object( 'MainWindow.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonDblClick, PyQt4.QtCore.QPoint(83, 107), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(379, 231), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 3.201071 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.appendButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(90, 13), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(410, 133), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 4.305941 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(90, -20), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(410, 133), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 4.391827 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(98, 0), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(418, 153), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 4.950493 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(98, 1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(418, 154), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 4.964685 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(98, 2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(418, 155), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 4.980346 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(97, 4), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(417, 157), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 4.995857 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(98, 6), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(418, 159), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 5.011081 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(99, 6), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(419, 159), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 5.038614 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(99, 7), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(419, 160), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 5.054302 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(99, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(419, 161), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 5.069392 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(99, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(419, 163), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 5.083368 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(100, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(420, 164), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 5.100778 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(101, 13), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(421, 166), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 5.115794 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(101, 14), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(421, 167), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 5.179027 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(101, 14), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(421, 167), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 5.188296 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(102, 14), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(422, 167), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 5.24556 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(102, 14), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(422, 167), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 5.269303 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(119, 39), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(415, 163), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 7.800076 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(118, 39), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(414, 163), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 7.813816 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(118, 39), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(414, 163), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 7.903306 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonDblClick, PyQt4.QtCore.QPoint(118, 39), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(414, 163), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 7.908928 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.appendButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(72, 21), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(392, 141), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 9.167941 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(72, -12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(392, 141), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 9.269897 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(68, -5), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(388, 148), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 9.354473 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(68, -1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(388, 152), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 9.384604 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(68, 1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(388, 154), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 9.406672 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(70, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(390, 163), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 9.432824 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(71, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(391, 164), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 9.456342 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(71, 14), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(391, 167), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 9.486039 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(73, 19), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(393, 172), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 9.509672 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(75, 22), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(395, 175), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 9.533438 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(75, 24), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(395, 177), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 9.557295 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(75, 25), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(395, 178), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 9.581655 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(75, 24), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(395, 177), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 9.749567 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(75, 21), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(395, 174), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 9.770302 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(75, 18), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(395, 171), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 9.798619 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(75, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(395, 168), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 9.822647 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(75, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(395, 168), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 9.846657 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(75, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(395, 168), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 10.014189 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(102, 32), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(398, 156), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 10.777819 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(102, 32), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(398, 156), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 10.878309 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonDblClick, PyQt4.QtCore.QPoint(102, 32), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(398, 156), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 10.970138 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.appendButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(80, 20), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(400, 140), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 11.682801 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(80, -13), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(400, 140), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 11.804542 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(75, -1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(395, 152), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 11.99817 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(75, 0), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(395, 153), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 12.023124 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(75, 7), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(395, 160), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 12.051014 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(75, 9), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(395, 162), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 12.069892 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(76, 9), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(396, 162), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 12.142091 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(77, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(397, 165), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 12.161945 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(78, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(398, 165), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 12.196155 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(78, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(398, 165), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 12.223226 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(78, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(398, 165), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 12.300576 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(100, 37), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(396, 161), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 13.015786 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(100, 37), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(396, 161), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 13.106674 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonDblClick, PyQt4.QtCore.QPoint(101, 37), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(397, 161), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 13.137912 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.appendButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(82, 21), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(402, 141), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 13.759099 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(82, -12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(402, 141), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 13.822471 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(82, 0), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(402, 153), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 14.11025 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(82, 5), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(402, 158), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 14.134105 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(82, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(402, 164), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 14.155843 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(83, 13), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(403, 166), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 14.178692 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(83, 14), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(403, 167), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 14.250113 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(83, 14), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(403, 167), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 14.43923 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(83, 14), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(403, 167), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 14.516577 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(106, 41), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(402, 165), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 15.179646 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(106, 41), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(402, 165), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 15.262548 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonDblClick, PyQt4.QtCore.QPoint(106, 41), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(402, 165), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 15.34389 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.appendButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(84, 25), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(404, 145), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 16.17567 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(84, -8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(404, 145), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 16.302815 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(87, -1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(407, 152), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 16.529088 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(87, 0), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(407, 153), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 16.557348 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(87, 9), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(407, 162), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 16.579854 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(87, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(407, 164), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 16.604015 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(87, 13), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(407, 166), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 16.637361 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(87, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(407, 168), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 16.665373 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(87, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(407, 168), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 16.824314 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(87, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(407, 168), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 16.900996 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(96, 35), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(392, 159), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 17.984124 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(96, 35), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(392, 159), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 18.07076 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonDblClick, PyQt4.QtCore.QPoint(96, 35), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(392, 159), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 18.152594 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(167, 143), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(487, 304), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 20.401426 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(167, 143), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(487, 304), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 20.68333 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(222, 0), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(542, 161), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 22.799981 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(223, 1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(543, 162), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 22.861961 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(224, 1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(544, 162), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 22.885348 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(225, 2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(545, 163), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 22.90141 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(226, 4), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(546, 165), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 22.922307 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(227, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(547, 169), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 22.936478 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(230, 21), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(550, 182), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 22.964122 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(233, 40), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(553, 201), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 22.990097 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(236, 44), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(556, 205), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 23.008396 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(236, 47), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(556, 208), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 23.027567 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(236, 49), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(556, 210), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 23.049586 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(239, 50), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(559, 211), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 23.068295 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(242, 53), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(562, 214), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 23.09362 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(242, 55), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(562, 216), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 23.107433 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(243, 59), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(563, 220), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 23.122788 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(243, 61), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(563, 222), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 23.137424 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(243, 62), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(563, 223), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 23.159091 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(241, 61), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(561, 222), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 23.222715 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.viewerStack.Form.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(241, 61), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(561, 222), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 23.24965 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.qt_splithandle_' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(258, 1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(576, 156), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 24.169742 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.qt_splithandle_' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(259, 1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(577, 156), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 24.229018 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.qt_splithandle_' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(260, 5), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(578, 160), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 24.242699 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.qt_splithandle_' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(261, 6), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(579, 165), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 24.263315 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.qt_splithandle_' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(264, 16), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(582, 180), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 24.42096 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.qt_splithandle_' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(263, 27), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(581, 206), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 24.437578 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.qt_splithandle_' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(263, 3), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(581, 208), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 24.460046 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.qt_splithandle_' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(261, 13), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(579, 220), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 24.638497 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.qt_splithandle_' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(257, 45), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(575, 264), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 24.660781 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.qt_splithandle_' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(255, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(573, 273), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 24.680049 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.qt_splithandle_' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(253, 18), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(571, 290), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 24.884792 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.qt_splithandle_' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(247, 54), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(565, 343), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 24.915137 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.qt_splithandle_' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(249, 13), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(567, 355), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 24.936145 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.qt_splithandle_' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(248, 26), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(566, 380), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 25.123403 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.qt_splithandle_' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(248, 2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(566, 381), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 25.324996 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.qt_splithandle_' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(247, 2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(565, 382), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 25.344583 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.qt_splithandle_' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(247, 1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(565, 382), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 25.36608 )

    ########################
    player.display_comment("""now he have 5 images""")
    ########################

    ########################
    player.display_comment("""we add a few features""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_4_QScrollArea.qt_scrollarea_viewport.child_0_QStackedWidget.Form.instructionLabel' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(98, 179), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(113, 272), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 28.439955 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_4_QScrollArea.qt_scrollarea_viewport.child_0_QStackedWidget.Form.instructionLabel' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(98, 179), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(113, 272), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 28.652402 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_5_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(59, 16), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(65, 346), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 29.386908 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_5_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(59, 16), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(65, 346), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 29.448594 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_6_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.Form.SelectFeaturesButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(133, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(139, 138), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 31.116573 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_6_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.Form.SelectFeaturesButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(133, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(139, 138), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 31.341047 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.Dialog.featureTableWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(16, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(468, 162), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 32.543548 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.Dialog.featureTableWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(20, 13), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(472, 163), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 32.561854 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.Dialog.featureTableWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(20, 13), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(472, 163), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 32.590856 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.Dialog.featureTableWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(88, 34), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(540, 184), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 33.060591 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.Dialog.featureTableWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(95, 35), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(547, 185), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 33.079037 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.Dialog.featureTableWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(95, 35), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(547, 185), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 33.159326 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.Dialog.featureTableWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(149, 64), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(601, 214), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 33.499189 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.Dialog.featureTableWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(150, 64), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(602, 214), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 33.575806 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.Dialog.featureTableWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(150, 64), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(602, 214), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 33.599187 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.Dialog.ok' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(51, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(691, 419), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 34.316428 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.Dialog.ok' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(52, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(692, 419), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 34.39826 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.Dialog.ok' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(52, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(692, 419), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 34.41497 )

    ########################
    player.display_comment("""add a few labels""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_6_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.Form' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(65, 163), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(71, 276), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 35.82572 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_6_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.Form' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(65, 163), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(71, 276), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 35.911049 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(61, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(67, 367), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 36.230343 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(62, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(68, 367), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 36.252251 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(62, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(68, 367), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 36.284635 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.AddLabelButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(68, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(83, 275), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 38.399903 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.AddLabelButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(69, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(84, 274), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 38.634851 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.AddLabelButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(69, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(84, 274), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 38.646853 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.AddLabelButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(80, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(95, 274), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 39.19129 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.AddLabelButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(80, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(95, 274), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 39.291276 )

    ########################
    player.display_comment("""do some labeling""")
    ########################

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(389, 365), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(700, 392), 360, Qt.NoButton, Qt.NoModifier, 2), 40.949041 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(389, 365), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(700, 392), 120, Qt.NoButton, Qt.NoModifier, 2), 41.062137 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(353, 347), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(664, 374), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 41.911905 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(353, 348), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(664, 375), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 41.986169 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(353, 348), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(664, 375), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 42.006382 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(353, 348), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(664, 375), 360, Qt.NoButton, (Qt.ControlModifier), 2), 42.031946 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(353, 348), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(664, 375), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 42.05095 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(353, 348), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(664, 375), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 42.229836 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(353, 348), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(664, 375), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 42.255034 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(353, 348), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(664, 375), 240, Qt.NoButton, (Qt.ControlModifier), 2), 42.2761 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(353, 348), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(664, 375), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 42.307964 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(353, 348), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(664, 375), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 42.55313 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(353, 348), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(664, 375), 240, Qt.NoButton, (Qt.ControlModifier), 2), 42.582564 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(353, 348), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(664, 375), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 42.764744 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(353, 348), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(664, 375), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 42.799451 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(353, 348), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(664, 375), 240, Qt.NoButton, (Qt.ControlModifier), 2), 42.823899 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(353, 348), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(664, 375), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 42.847504 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(353, 348), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(664, 375), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 43.599558 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(353, 348), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(664, 375), 240, Qt.NoButton, (Qt.ControlModifier), 2), 43.63715 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(353, 348), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(664, 375), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 43.800482 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(353, 348), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(664, 375), Qt.NoButton, Qt.NoButton, (Qt.ControlModifier)), 43.828372 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(353, 348), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(664, 375), 120, Qt.NoButton, (Qt.ControlModifier), 2), 43.854379 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(270, 222), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(581, 249), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 44.892179 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(254, 246), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(565, 273), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 45.163157 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(239, 279), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(550, 306), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 45.195581 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(232, 297), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(543, 324), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 45.220998 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(230, 303), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(541, 330), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 45.249636 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(226, 317), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(537, 344), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 45.349061 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(223, 333), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(534, 360), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 45.381611 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(224, 333), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(535, 360), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 45.494942 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(224, 333), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(535, 360), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 45.527604 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(342, 221), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(653, 248), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 47.984514 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(349, 224), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(660, 251), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 48.0114 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(358, 228), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(669, 255), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 48.10845 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(393, 263), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(704, 290), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 48.142098 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(397, 269), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(708, 296), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 48.166169 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(402, 278), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(713, 305), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 48.280915 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(420, 357), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(731, 384), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 48.308429 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(422, 377), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(733, 404), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 48.347842 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(422, 377), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(733, 404), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 48.459853 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(228, 396), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(539, 423), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 49.701278 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(275, 415), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(586, 442), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 49.739524 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(283, 419), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(594, 446), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 49.774069 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(288, 422), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(599, 449), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 49.87811 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(308, 431), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(619, 458), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 49.897019 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(316, 433), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(627, 460), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 49.919835 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(327, 435), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(638, 462), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 50.026225 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(349, 436), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(660, 463), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 50.047874 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(357, 434), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(668, 461), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 50.06685 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(364, 432), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(675, 459), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 50.18464 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(375, 427), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(686, 454), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 50.213485 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(397, 415), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(708, 442), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 50.232721 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(401, 410), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(712, 437), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 50.258166 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(401, 409), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(712, 436), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 50.360039 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(401, 409), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(712, 436), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 50.391694 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(324, 292), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(635, 319), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 51.637451 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(292, 311), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(603, 338), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 51.668495 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(289, 314), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(600, 341), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 51.688339 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(284, 320), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(595, 347), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 51.800433 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(276, 337), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 364), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 51.820343 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(276, 340), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(587, 367), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 51.8379 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(277, 346), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(588, 373), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 51.928338 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(308, 376), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(619, 403), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 51.95136 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(334, 382), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(645, 409), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 51.972048 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(360, 382), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(671, 409), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 52.074019 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(398, 348), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(709, 375), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 52.09152 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(399, 329), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(710, 356), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 52.114465 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(404, 310), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(715, 337), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 52.221124 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(388, 298), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(699, 325), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 52.243052 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(384, 296), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(695, 323), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 52.263528 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(376, 292), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(687, 319), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 52.364338 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(353, 290), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(664, 317), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 52.407404 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(347, 289), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(658, 316), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 52.439309 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(339, 290), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(650, 317), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 52.564421 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(325, 294), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(636, 321), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 52.597722 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(325, 295), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(636, 322), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 52.617389 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(323, 296), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(634, 323), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 52.73091 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(320, 299), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(631, 326), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 52.770424 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(320, 299), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(631, 326), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 52.795758 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.child_3_QTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(69, 16), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(86, 169), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 53.911182 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.child_3_QTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(68, 16), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(85, 169), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 54.173219 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.child_3_QTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(68, 16), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(85, 169), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 54.192486 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(453, 315), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(764, 342), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 54.902309 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(463, 364), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(774, 391), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 54.952442 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(461, 375), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(772, 402), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 54.97815 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(460, 383), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(771, 410), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 55.162563 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(460, 387), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(771, 414), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 55.194004 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(460, 387), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(771, 414), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 55.214928 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(212, 364), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(523, 391), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 56.336557 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(213, 369), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(524, 396), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 56.457272 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(213, 409), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(524, 436), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 56.486127 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(213, 411), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(524, 438), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 56.596031 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(215, 428), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(526, 455), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 56.637901 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(215, 430), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(526, 457), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 56.658915 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(216, 430), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(527, 457), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 56.765659 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(216, 430), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(527, 457), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 56.785488 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(252, 205), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(563, 232), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 57.957557 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(238, 209), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(549, 236), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 57.99856 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(235, 210), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(546, 237), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 58.024323 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(235, 211), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(546, 238), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 58.125108 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(223, 216), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(534, 243), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 58.145217 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(218, 218), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(529, 245), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 58.171194 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(217, 219), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(528, 246), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 58.270093 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(206, 223), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(517, 250), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 58.301557 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(205, 223), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(516, 250), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 58.320376 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(204, 223), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(515, 250), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 58.445719 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(204, 223), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(515, 250), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 58.576255 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(204, 9), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(297, 454), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 60.596202 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(204, -11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(297, 454), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 60.891564 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(201, 1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(294, 466), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 61.531936 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(192, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(287, 479), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 61.563879 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(191, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(286, 479), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 61.611129 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(190, 13), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(285, 480), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 61.777724 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(180, 20), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(275, 487), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 61.81322 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(176, 21), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(271, 488), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 61.876255 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(176, 22), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(271, 489), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 61.914034 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(176, 22), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(271, 489), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 62.109142 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(176, 22), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(271, 489), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 62.226305 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(198, 9), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(291, 454), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 63.914047 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(199, -11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(292, 454), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 63.941481 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(199, -11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(292, 454), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 63.957866 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(194, 0), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(289, 467), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 63.985071 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(194, 0), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(289, 467), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 64.070723 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(191, 2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(286, 469), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 64.098023 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(189, 3), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(284, 470), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 64.64979 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(183, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(278, 475), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 64.686353 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(181, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(276, 479), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 64.720355 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(180, 14), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(275, 481), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 64.745509 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(180, 16), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(275, 483), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 64.787211 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(178, 17), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(273, 484), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 64.815473 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(178, 18), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(273, 485), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 64.850703 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(178, 19), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(273, 486), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 64.889749 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(178, 20), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(273, 487), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 64.918183 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(177, 22), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(272, 489), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 64.948058 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(177, 23), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(272, 490), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 64.975915 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(177, 24), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(272, 491), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 65.002673 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(177, 25), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(272, 492), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 65.031775 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(177, 25), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(272, 492), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 65.062496 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(178, 25), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(273, 492), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 65.106107 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(178, 25), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(273, 492), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 65.163295 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(195, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(288, 456), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 66.427974 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(195, -8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(288, 457), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 66.528703 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(195, -8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(288, 457), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 66.546296 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(191, 1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(284, 466), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 66.647322 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(188, 3), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(283, 470), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 66.674223 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(188, 7), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(283, 474), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 66.692983 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(188, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(283, 475), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 66.727206 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(187, 9), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(282, 476), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 66.745171 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(185, 13), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(280, 480), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 66.766889 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(184, 16), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(279, 483), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 66.789253 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(183, 17), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(278, 484), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 66.869152 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(182, 19), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(277, 486), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 66.886649 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(180, 22), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(275, 489), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 66.905655 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(180, 23), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(275, 490), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 66.960041 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(180, 24), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(275, 491), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 66.99508 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(181, 25), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(276, 492), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 67.015596 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(181, 25), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(276, 492), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 67.065114 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(181, 25), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(276, 492), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 67.18242 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(204, 7), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(297, 452), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 67.727657 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(204, -13), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(297, 452), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 67.817085 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(179, 0), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(274, 467), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 68.089449 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(175, 0), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(270, 467), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 68.116984 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(175, 1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(270, 468), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 68.161059 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(173, 2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(268, 469), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 68.190825 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(172, 3), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(267, 470), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 68.229183 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(171, 3), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(266, 470), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 68.265197 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(170, 3), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(265, 470), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 68.294301 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(168, 5), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(263, 472), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 68.320387 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(165, 6), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(260, 473), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 68.349536 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(164, 7), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(259, 474), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 68.374269 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(164, 7), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(259, 474), 120, Qt.NoButton, Qt.NoModifier, 2), 68.483952 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(164, 7), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(259, 474), 120, Qt.NoButton, Qt.NoModifier, 2), 68.508462 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(164, 7), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(259, 474), 120, Qt.NoButton, Qt.NoModifier, 2), 68.531433 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QWheelEvent(PyQt4.QtCore.QPoint(164, 7), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(259, 474), 120, Qt.NoButton, Qt.NoModifier, 2), 68.562397 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(164, 7), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(259, 474), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 68.811117 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.layoutWidget.imageSelectionGroup.imageSelectionCombo.child_1_QFrame.child_1_QListView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(164, 7), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(259, 474), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 68.899324 )

    ########################
    player.display_comment("""(and we are done for this test)""")
    ########################

    player.display_comment("SCRIPT COMPLETE")
