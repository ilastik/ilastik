
# Event Recording
# Started at: 2013-07-11 12:27:39.298448

def playback_events(player):
    import PyQt4.QtCore
    from PyQt4.QtCore import Qt, QEvent, QPoint
    import PyQt4.QtGui
    from ilastik.utility.gui.eventRecorder.objectNameUtils import get_named_object
    from ilastik.utility.gui.eventRecorder.eventRecorder import EventPlayer
    from ilastik.shell.gui.startShellGui import shell    

    player.display_comment("SCRIPT STARTING")


    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.startupPage.frame.CreateList.qt_scrollarea_viewport.scrollAreaWidgetContents.child_2_QToolButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(77, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(388, 211), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 0.008285 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.startupPage.frame.CreateList.qt_scrollarea_viewport.scrollAreaWidgetContents.child_2_QToolButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(77, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(388, 211), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 0.080615 )

    obj = get_named_object( 'MainWindow.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(85, 101), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(381, 225), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 1.558319 )

    obj = get_named_object( 'MainWindow.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(85, 101), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(381, 225), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 1.566587 )

    obj = get_named_object( 'MainWindow.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(85, 101), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(381, 225), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 1.576758 )

    obj = get_named_object( 'MainWindow.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonDblClick, PyQt4.QtCore.QPoint(85, 101), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(381, 225), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 1.682573 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.appendButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(49, 21), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(369, 141), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 4.266115 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(49, -12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(369, 141), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 4.314642 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(51, -1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(371, 152), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 4.818015 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(51, 2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(371, 155), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 4.837686 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(51, 5), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(371, 158), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 4.854177 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(51, 7), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(371, 160), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 4.87035 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(51, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(371, 161), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 4.897941 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(50, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(370, 165), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 4.912351 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(50, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(370, 168), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 4.930173 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(50, 18), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(370, 171), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 4.947525 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(49, 20), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(369, 173), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 4.96601 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(48, 21), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(368, 174), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 4.98292 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(48, 24), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(368, 177), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 4.995711 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(48, 24), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(368, 177), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 5.011678 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(48, 24), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(368, 177), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 5.035123 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(48, 25), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(368, 178), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 5.049811 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(48, 25), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(368, 178), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 5.102152 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(48, 25), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(368, 178), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 5.139844 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.Form.cancelButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(40, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(678, 572), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 6.672565 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.Form.cancelButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(40, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(678, 572), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 6.76513 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.Form.cancelButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(40, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(678, 572), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 6.777334 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.splitter.fileInfoTabWidget.qt_tabwidget_stackedwidget.DataDetailViewerWidget.appendButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(65, 25), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(385, 145), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 8.169277 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(65, -8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(385, 145), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 8.246813 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(65, -1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(385, 152), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 8.567989 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(65, 1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(385, 154), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 8.584405 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(65, 5), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(385, 158), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 8.597298 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(65, 7), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(385, 160), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 8.607631 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(65, 9), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(385, 162), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 8.628438 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(65, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(385, 164), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 8.644475 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(64, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(384, 165), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 8.662331 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(64, 14), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(384, 167), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 8.680805 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(64, 14), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(384, 167), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 8.691631 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(64, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(384, 168), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 8.704031 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(64, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(384, 168), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 8.718889 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(64, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(384, 168), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 8.734359 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(64, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(384, 168), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 8.748149 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(64, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(384, 168), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 8.895275 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.addFileButton_role_0' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(64, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(384, 168), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 8.931449 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(88, 39), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(384, 163), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 9.806724 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(88, 39), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(384, 163), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 9.873478 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(88, 39), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(384, 163), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 9.881731 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(88, 39), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(384, 163), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 10.532996 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(88, 39), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(384, 163), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 10.542323 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_1_lane_-1.QFileDialog.splitter.frame.stackedWidget.page.listView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonDblClick, PyQt4.QtCore.QPoint(88, 39), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(384, 163), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 10.668183 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(98, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(104, 370), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 15.502783 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(98, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(104, 370), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 15.563743 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(98, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(104, 370), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 15.576926 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(98, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(104, 370), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 15.590681 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(98, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(104, 370), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 15.60668 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(107, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(113, 367), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 15.687094 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(109, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(115, 367), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 15.698612 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(110, 7), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(116, 366), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 15.711148 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(110, 7), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(116, 366), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 15.725188 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(111, 7), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(117, 366), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 15.738408 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(111, 7), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(117, 366), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 15.75149 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(113, 7), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(119, 366), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 15.797284 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(113, 7), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(119, 366), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 15.809956 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(114, 7), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(120, 366), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 15.82206 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(116, 7), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(122, 366), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 15.83319 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(119, 6), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(125, 365), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 15.845164 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(122, 6), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(128, 365), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 15.857498 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(125, 5), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(131, 364), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 15.87012 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(128, 5), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(134, 364), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 15.882831 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(131, 5), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(137, 364), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 15.894753 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(132, 5), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(138, 364), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 15.907118 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(132, 5), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(138, 364), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 15.919294 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(132, 5), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(138, 364), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 15.93089 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(132, 5), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(138, 364), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 15.943805 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(131, 5), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(137, 364), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 15.968719 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(131, 5), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(137, 364), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 15.98054 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(131, 5), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(137, 364), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 15.994715 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(131, 6), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(137, 365), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 16.129576 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(131, 5), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(137, 364), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 16.154572 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(131, 4), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(137, 363), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 16.166014 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(131, -4), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(137, 355), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 16.177558 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(131, -33), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(137, 326), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 16.193235 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(131, -39), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(137, 320), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 16.202803 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(131, -42), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(137, 317), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 16.214737 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(131, -43), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(137, 316), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 16.227927 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(133, -44), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(139, 315), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 16.241645 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(133, -44), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(139, 315), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 16.263624 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(139, -44), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(145, 315), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 16.276162 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(142, -44), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(148, 315), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 16.290123 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(145, -44), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(151, 315), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 16.30227 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(147, -44), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(153, 315), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 16.314249 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(150, -44), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(156, 315), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 16.326008 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(150, -45), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(156, 314), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 16.338703 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(150, -45), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(156, 314), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 16.352415 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(150, -44), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(156, 315), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 16.388403 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(149, -43), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(155, 316), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 16.403895 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(149, -42), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(155, 317), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 16.416198 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(149, -41), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(155, 318), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 16.429451 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(151, -37), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(157, 322), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 16.441606 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(152, -34), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(158, 325), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 16.451452 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(152, -32), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(158, 327), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 16.460774 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(152, -31), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(158, 328), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 16.473616 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(150, -29), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(156, 330), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 16.486258 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(150, -28), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(156, 331), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 16.497933 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(149, -26), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(155, 333), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 16.511251 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(147, -23), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(153, 336), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 16.524862 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(146, -20), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(152, 339), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 16.536368 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(144, -19), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(150, 340), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 16.549521 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(143, -18), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(149, 341), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 16.559154 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(142, -18), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(148, 341), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 16.571557 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(142, -17), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(148, 342), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 16.583473 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(142, -17), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(148, 342), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 16.596363 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(142, -17), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(148, 342), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 16.611951 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_5_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(141, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(147, 342), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 16.77277 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_5_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(141, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(147, 341), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 16.784943 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_5_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(141, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(147, 341), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 16.793675 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_5_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(141, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(147, 341), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 16.844406 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_6_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.Form.SelectFeaturesButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(125, 4), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(131, 132), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 19.000413 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_6_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.Form.SelectFeaturesButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(125, 4), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(131, 132), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 19.194263 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_6_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_2_lane_0.Form.SelectFeaturesButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(125, 4), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(131, 132), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 19.203691 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.Dialog.featureTableWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(15, 16), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(467, 166), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 20.226597 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.Dialog.featureTableWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(15, 16), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(467, 166), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 20.23643 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.Dialog.featureTableWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(15, 16), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(467, 166), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 20.252176 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.Dialog.featureTableWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(25, 47), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(477, 197), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 20.661377 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.Dialog.featureTableWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(25, 47), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(477, 197), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 20.670681 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.Dialog.featureTableWidget.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(25, 47), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(477, 197), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 20.686101 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.Dialog.ok' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(41, 5), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(681, 409), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 21.909791 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_2_lane_0.Dialog.ok' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(41, 5), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(681, 409), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 21.999933 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(75, 9), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(81, 368), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 23.955879 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(75, 9), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(81, 368), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 24.114585 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(75, 9), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(81, 368), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 24.876861 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_7_QAbstractButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(75, 9), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(81, 368), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 24.945345 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(80, 120), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(86, 262), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 26.413912 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(80, 121), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(86, 263), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 26.445432 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(80, 121), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(86, 263), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 26.463297 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.AddLabelButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(71, 7), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(86, 270), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 26.825026 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.AddLabelButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(72, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(87, 271), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 26.846268 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.AddLabelButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(72, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(87, 271), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 26.862334 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.AddLabelButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonDblClick, PyQt4.QtCore.QPoint(72, 9), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(87, 272), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 27.152411 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.AddLabelButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(72, 9), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(87, 272), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 27.186747 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.child_2_QTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(38, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(55, 165), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 28.153343 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.child_2_QTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(38, 12), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(55, 165), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 28.174715 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(368, 321), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(679, 348), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 29.446136 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(312, 313), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(623, 340), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 29.504295 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(299, 311), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(610, 338), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 29.533287 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(297, 310), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(608, 337), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 29.699964 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(302, 312), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(613, 339), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 29.734519 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(302, 312), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(613, 339), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 29.758941 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.child_2_QTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(27, 52), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(44, 205), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 30.682982 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.child_2_QTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(27, 51), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(44, 204), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 30.701361 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.labelListView.child_2_QTableView.qt_scrollarea_viewport' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(27, 51), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(44, 204), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 30.715399 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(342, 361), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(653, 388), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 31.780114 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(307, 356), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(618, 383), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 31.834246 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(295, 354), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(606, 381), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 32.018522 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(295, 355), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(606, 382), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 32.060655 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.appletStack.centralWidget_applet_3_lane_0.volumeEditorWidget.child_9_QuadView.child_1_QSplitter.splitter1.child_1_ImageView2DDockWidget.child_1_ImageView2D.child_2_QWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(295, 355), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(606, 382), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 32.084812 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.liveUpdateButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(96, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(111, 329), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 34.02308 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.liveUpdateButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(96, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(111, 329), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 34.23825 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.liveUpdateButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(96, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(111, 329), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 35.656046 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.liveUpdateButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(96, 10), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(111, 329), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 35.736278 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(142, 231), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(148, 373), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 36.689666 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(142, 229), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(148, 371), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 37.056547 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(142, 227), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(148, 369), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 37.079923 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(142, 226), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(148, 368), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 37.093509 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(142, 225), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(148, 367), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 37.106537 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(142, 225), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(148, 367), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 37.117496 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.savePredictionsButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(140, 17), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(155, 364), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 37.526195 )

    obj = get_named_object( 'MainWindow.mainLayout.mainStackedWidget.contentPage.widget.sideSplitter.mainSplitter.appletBar.child_8_QScrollArea.qt_scrollarea_viewport.appletDrawer_applet_3_lane_0.containingWidget.savePredictionsButton' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(140, 17), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(155, 364), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 37.917061 )

    obj = get_named_object( 'MainWindow.child_8_QMenuBar' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(40, 8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(40, 8), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 41.921074 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(40, -8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(40, 11), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 42.195277 )

    obj = get_named_object( 'MainWindow.child_8_QMenuBar' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(40, 11), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(40, 11), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 42.207658 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(40, -8), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(40, 11), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 42.275656 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(39, -2), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(39, 17), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 42.378679 )

    obj = get_named_object( 'MainWindow.child_8_QMenuBar' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(39, 17), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(46, 29), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 42.400614 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(42, 1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(42, 20), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 42.420975 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(47, 20), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(47, 39), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 42.433668 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(48, 23), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(48, 42), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 42.449155 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(51, 28), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(51, 47), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 42.476303 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(55, 35), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(55, 54), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 42.488819 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(56, 38), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(56, 57), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 42.501838 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(57, 41), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(57, 60), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 42.527372 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(57, 49), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(57, 68), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 42.553837 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(58, 49), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(58, 68), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 42.571561 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(58, 49), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(58, 68), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 42.598901 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(58, 49), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(58, 68), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 42.611406 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(58, 49), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(58, 68), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 42.623135 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(59, 49), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(59, 68), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 42.6358 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(59, 49), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(59, 68), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 42.722629 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(59, 49), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(59, 68), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 42.762692 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(59, 49), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(59, 68), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 42.792067 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(59, 49), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(59, 68), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 42.943055 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(59, 49), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(59, 68), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 43.007483 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(58, 50), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(58, 69), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 43.291762 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(58, 50), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(58, 69), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 43.311347 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(58, 50), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(58, 69), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 43.330678 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(58, 51), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(58, 70), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 43.368822 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(58, 51), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(58, 70), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 43.396063 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(58, 51), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(58, 70), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 43.409747 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(58, 52), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(58, 71), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 43.424069 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(58, 52), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(58, 71), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 43.440306 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(58, 52), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(58, 71), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 43.453076 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(58, 52), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(58, 71), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 43.474581 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(57, 52), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(57, 71), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 43.494566 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(57, 52), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(57, 71), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 43.513136 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(57, 52), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(57, 71), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 43.532254 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(56, 52), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(56, 71), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 43.547196 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(56, 52), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(56, 71), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 43.573338 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(56, 52), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(56, 71), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 43.592326 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(56, 52), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(56, 71), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 43.658726 )

    obj = get_named_object( 'MainWindow.child_8_QMenuBar' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(33, 14), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(33, 14), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 46.12201 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(33, -4), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(33, 15), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 46.360603 )

    obj = get_named_object( 'MainWindow.child_8_QMenuBar' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(33, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(36, 15), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 46.383708 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(33, -4), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(33, 15), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 46.45011 )

    obj = get_named_object( 'MainWindow.child_8_QMenuBar' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(33, 15), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(36, 15), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 46.461131 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(33, -4), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(33, 15), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 46.474323 )

    obj = get_named_object( 'MainWindow.child_8_QMenuBar' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(33, 17), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(33, 18), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 46.743655 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(33, -1), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(33, 18), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 46.764201 )

    obj = get_named_object( 'MainWindow.child_8_QMenuBar' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(33, 18), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(33, 19), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 46.778238 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(33, 0), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(33, 19), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 46.796475 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(33, 4), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(33, 23), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 46.811172 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(33, 9), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(33, 28), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 46.825774 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(33, 18), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(33, 37), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 46.846595 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(37, 34), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(37, 53), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 46.864901 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(41, 38), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(41, 57), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 46.885747 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(44, 40), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(44, 59), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 46.917836 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(45, 40), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(45, 59), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 46.94534 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(45, 40), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(45, 59), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 46.965488 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(45, 40), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(45, 59), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 47.016811 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(46, 40), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(46, 59), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 47.038746 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(46, 40), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(46, 59), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 47.05374 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(46, 40), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(46, 59), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 47.070176 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(46, 40), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(46, 59), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 47.141451 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(47, 40), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(47, 59), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 47.166002 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(47, 40), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(47, 59), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 47.181883 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(64, 54), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(64, 73), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 47.196447 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(72, 66), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(72, 85), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 47.218477 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(77, 79), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(77, 98), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 47.23049 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(81, 83), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(81, 102), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 47.244546 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(81, 86), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(81, 105), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 47.264293 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(82, 87), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(82, 106), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 47.275386 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(82, 87), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(82, 106), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 47.338345 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(84, 88), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(84, 107), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 47.354584 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(83, 88), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(83, 107), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 48.000623 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(82, 88), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(82, 107), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 48.023629 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(82, 89), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(82, 108), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 48.044476 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(82, 89), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(82, 108), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 48.060231 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(82, 88), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(82, 107), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 48.098603 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(82, 87), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(82, 106), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 48.110535 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(82, 86), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(82, 105), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 48.122372 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(82, 85), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(82, 104), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 48.134113 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(83, 85), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(83, 104), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 48.15608 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(83, 84), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(83, 103), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 48.17097 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(85, 82), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(85, 101), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 48.187238 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(87, 81), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(87, 100), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 48.202204 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(87, 80), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(87, 99), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 48.215319 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(88, 80), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(88, 99), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 48.228402 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(89, 80), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(89, 99), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 48.242409 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(89, 80), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(89, 99), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 48.260293 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(89, 80), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(89, 99), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 48.273767 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(90, 80), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(90, 99), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 48.287481 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(90, 80), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(90, 99), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 48.305171 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(92, 78), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(92, 97), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 48.326185 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(92, 78), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(92, 97), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 48.484184 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(92, 79), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(92, 98), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 48.503336 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(92, 79), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(92, 98), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 48.52423 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(92, 79), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(92, 98), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 48.541768 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(92, 79), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(92, 98), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 48.566855 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(92, 79), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(92, 98), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 48.591667 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(92, 80), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(92, 99), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 48.620431 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(92, 80), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(92, 99), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 48.640044 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(92, 80), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(92, 99), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 48.651953 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(92, 80), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(92, 99), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 48.663891 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(92, 80), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(92, 99), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 48.676021 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(92, 81), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(92, 100), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 48.68876 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(92, 81), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(92, 100), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 48.701059 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(92, 81), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(92, 100), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 48.712831 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(92, 82), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(92, 101), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 48.727292 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(92, 82), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(92, 101), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 48.750903 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(92, 82), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(92, 101), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 48.763261 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(92, 82), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(92, 101), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 48.780042 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(92, 82), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(92, 101), Qt.NoButton, Qt.NoButton, Qt.NoModifier), 48.814897 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonPress, PyQt4.QtCore.QPoint(92, 82), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(92, 101), (Qt.LeftButton), (Qt.LeftButton), Qt.NoModifier), 49.53859 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseMove, PyQt4.QtCore.QPoint(92, 82), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(92, 101), Qt.NoButton, (Qt.LeftButton), Qt.NoModifier), 49.571159 )

    obj = get_named_object( 'MainWindow.project_menu' )
    player.post_event( obj,  PyQt4.QtGui.QMouseEvent(QEvent.MouseButtonRelease, PyQt4.QtCore.QPoint(92, 82), shell.mapToGlobal( QPoint(0,0) ) + PyQt4.QtCore.QPoint(92, 101), (Qt.LeftButton), Qt.NoButton, Qt.NoModifier), 49.580047 )

    obj = get_named_object( 'MainWindow.QFileDialog.fileNameEdit' )
    player.post_event( obj,  PyQt4.QtGui.QKeyEvent(QEvent.KeyPress, 0x1000004, Qt.NoModifier, """""", False, 1), 50.824275 )

    ########################
    player.display_comment("""crashhh!11""")
    ########################

    player.display_comment("SCRIPT COMPLETE")
