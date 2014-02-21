from PyQt4.QtCore import pyqtSignal
from PyQt4.QtGui import QToolBox

class AppletDrawerToolBox(QToolBox):
    """
    A replacement for QToolBox that allows clients to truly hide a widget (including its header).

    To clients, it looks like the list of widgets in the toolbox remains constant even while a widget is hidden.
    Under the hood, the widgets are added and removed from the QToolBox.
    
    This class adds two special methods that QToolBox doesn't have:
    - hideIndexItem()
    - showIndexItem()
    These methods remove/re-add the item from the visible headings without changing any of the widget indexes.
    
    Note: Most of these methods shadow -- not override -- the base class functions,
          but for Python-only usage, there's no big difference.
    """
    _currentChanged = pyqtSignal(int)
    
    def __init__(self, *args, **kwargs):
        super( AppletDrawerToolBox, self ).__init__(*args, currentChanged=self._handleSuperCurrentChanged, **kwargs)
        self._all_widgets = []
        self._visible_widgets = []
        self._invisible_widgets = []

        # Replace the superclass signal with our own.
        self.currentChanged = self._currentChanged

    def _get_visible_index(self, index):
        widget, text = self._all_widgets[index]
        visible_index = self._index_of_widget(widget, self._visible_widgets)
        if visible_index != -1:
            assert visible_index == super( AppletDrawerToolBox, self ).indexOf(widget),\
                "visible index doesn't match: {} / {}".format( visible_index, super( AppletDrawerToolBox, self ).indexOf(widget) )
        return visible_index
    
    def _get_index(self, visible_index):
        try:
            widget, text = self._visible_widgets[visible_index]
            index = self._index_of_widget(widget, self._all_widgets)
            return index
        except IndexError:
            return -1

    ## Special methods ##
    def hideIndexItem(self, index):
        visible_index = self._get_visible_index(index)
        if visible_index != -1:
            widget, text = self._all_widgets[index]
            super( AppletDrawerToolBox, self ).removeItem( visible_index )
            widget.hide()
            widget.setParent(None)
            self._visible_widgets.pop( visible_index )
            self._invisible_widgets.append( (widget, text) )
    
    def showIndexItem(self, index):
        visible_index = self._get_visible_index(index)
        if visible_index == -1:
            widget, text = self._all_widgets[index]
            # Find visible index
            visible_index = 0
            for item in self._all_widgets:
                if item[0] is widget:
                    break
                if item in self._visible_widgets:
                    visible_index +=1
            self._visible_widgets.insert( visible_index, (widget, text) )
            print "Showing {} at {}".format( text, visible_index )
            super( AppletDrawerToolBox, self ).insertItem( visible_index, widget, text )

    ####

    def _handleSuperCurrentChanged(self, visible_index):
        index = self._get_index(visible_index)
        self.currentChanged.emit( index )
    
    def addItem(self, widget, text):
        self._all_widgets.append( (widget, text) )
        self._visible_widgets.append( (widget, text) )
        super( AppletDrawerToolBox, self ).addItem( widget, text )
    
    def count(self):
        return len( self._visible_widgets ) + len( self._invisible_widgets )
        
    def currentIndex(self):
        visible_index = super( AppletDrawerToolBox, self).currentIndex()
        return self._get_index(visible_index)
    
    def currentWidget(self):
        super( AppletDrawerToolBox, self ).currentWidget()
    
    def indexOf(self, widget):
        for i, (w, text) in enumerate(self._all_widgets):
            if w is widget:
                return i
        return -1
    
    def insertItem(self, index, widget, text):
        self._all_widgets.insert( index, (widget, text) )
        visible_index = self._get_visible_index(index)
        self._visible_widgets.insert( visible_index, (widget, text) )
        super( AppletDrawerToolBox, self ).insertItem( visible_index, widget, text )
    
    def isItemEnabled(self, index):
        visible_index = self._get_visible_index(index)
        if visible_index == -1:
            return False
        return super( AppletDrawerToolBox, self ).itemEnabled( visible_index )
    
    def itemIcon(self, index):
        raise NotImplementedError("Sorry, this class doesn't support icons (yet).")
    
    def itemText(self, index):
        return self._all_widgets[index][1]
    
    def itemToolTip(self, index):
        raise NotImplementedError("Sorry, this class doesn't support tool-tips (yet).")
    
    def removeItem(self, index):
        visible_index = self._get_visible_index(index)

        # Remove from 'all' list
        (widget, text) = self._all_widgets.pop( index )

        if visible_index != -1:
            # Remove from visible
            self._visible_widgets.pop( visible_index )
            widget.hide()
            super( AppletDrawerToolBox, self ).removeItem( visible_index )
        else:
            # Find this widget in the invisible list and remove it
            invisible_index = self._index_of_widget(widget, self._invisible_widgets)
            self._invisible_widgets.pop( invisible_index )
    
    def setItemEnabled(self, index, enabled):
        visible_index = self._get_visible_index(index)
        if visible_index != -1:
            super( AppletDrawerToolBox, self ).setItemEnabled( visible_index, enabled )
    
    def setItemIcon(self, index, icon):
        raise NotImplementedError("Sorry, this class doesn't support icons (yet).")
    
    def setItemText(self, index, newtext):
        widget, oldtext = self._all_widgets[index]
        self._all_widgets[index] = ( widget, newtext )

        visible_index = self._get_visible_index(index)
        if visible_index != -1:
            self._visible_widgets[visible_index] = ( widget, newtext )
        else:
            # Find this widget in the invisible list
            invisible_index = self._index_of_widget(widget, self._invisible_widgets)
            self._invisible_widgets[invisible_index] = ( widget, newtext )

    def setItemToolTip(self, index, toopTip):
        raise NotImplementedError("Sorry, this class doesn't support tool-tips (yet).")
    
    def widget(self, index):
        return self._all_widgets[index][0]
    
    def setCurrentIndex(self, index):
        visible_index = self._get_visible_index(index)
        # If the given index isn't actually visible, this is a no-op.
        if visible_index != -1:
            super( AppletDrawerToolBox, self ).setCurrentIndex( visible_index )
    
    def setCurrentWidget(self, widget):
        # Find this widget's total index
        index = self._index_of_widget(widget, self._all_widgets)
        self.setCurrentIndex(index)
    
    def _index_of_widget(self, widget, widget_list):
        for i, (w,t) in enumerate( widget_list ):
            if w is widget:
                return i
        return -1

if __name__ == "__main__":
    from PyQt4.QtGui import QApplication, QWidget, QLabel

    app = QApplication([])
    w = QWidget()
    t = AppletDrawerToolBox(w)
    
    t.addItem( QLabel("Zero"),  "0" )
    t.addItem( QLabel("One"),   "1" )
    t.addItem( QLabel("Two"),   "2" )
    t.addItem( QLabel("Three"), "3" )
    t.addItem( QLabel("Four"),  "4" )
    
    def printNewIndex(index):
        print "Index changed to {}".format( index )
    t.currentChanged.connect( printNewIndex )

    t.hideIndexItem(1)
    t.hideIndexItem(2)
    #t.showIndexItem(1)
    #t.showIndexItem(2)
    
    t.setCurrentIndex(3)
    
    #w.layout().addWidget(t) 
    w.show()
    
    app.exec_()